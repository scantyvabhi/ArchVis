import os
import json
import asyncio
import tempfile
import shutil
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import subprocess
import sys
import signal

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    REPO_FETCHER = "repo_fetcher"
    ARCHITECTURE_ANALYST = "architecture_analyst"
    DIAGRAM_BUILDER = "diagram_builder"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentContext:
    session_id: str
    user_prompt: str
    repo_url: Optional[str] = None
    repo_context: Optional[Dict[str, Any]] = None
    canvas_state: Optional[Dict[str, Any]] = None
    mode: str = "pro"
    markdown_spec: Optional[str] = None
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    consensus_round: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResult:
    agent_role: AgentRole
    status: AgentStatus
    output: Dict[str, Any]
    reasoning: str
    confidence: float
    execution_time_ms: int
    error: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(
        self,
        role: AgentRole,
        model_client: "MultiModelClient",
        sandbox: "SandboxManager",
        tools: Dict[str, Callable],
        config: Optional[Dict[str, Any]] = None,
    ):
        self.role = role
        self.model_client = model_client
        self.sandbox = sandbox
        self.tools = tools
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.execution_history: List[AgentResult] = []

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_available_tools(self) -> List[str]:
        pass

    async def _call_model(
        self,
        prompt: str,
        model_preference: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
    ) -> str:
        return await self.model_client.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model_preference=model_preference,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    async def _call_tool(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name not in self.tools:
            return ToolResult(success=False, error=f"Tool '{tool_name}' not available")
        try:
            tool_func = self.tools[tool_name]
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**kwargs)
            else:
                result = tool_func(**kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _record_execution(self, result: AgentResult):
        self.execution_history.append(result)
        self.status = result.status


class SandboxManager:
    def __init__(
        self,
        max_execution_time: int = 30,
        max_memory_mb: int = 512,
        allowed_imports: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
    ):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.allowed_imports = allowed_imports or [
            "json",
            "re",
            "datetime",
            "typing",
            "dataclasses",
            "enum",
            "uuid",
            "hashlib",
            "base64",
            "collections",
            "itertools",
            "functools",
            "math",
            "statistics",
            "pydantic",
            "httpx",
        ]
        self.blocked_commands = blocked_commands or [
            "import os",
            "import sys",
            "import subprocess",
            "import shutil",
            "import socket",
            "import requests",
            "import urllib",
            "open(",
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "globals()",
            "locals()",
            "vars(",
            "dir(",
            "getattr",
            "setattr",
            "delattr",
        ]
        self._temp_dirs: List[str] = []

    def create_sandbox(self) -> str:
        temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
        self._temp_dirs.append(temp_dir)
        return temp_dir

    def cleanup(self):
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dirs.clear()

    def validate_code(self, code: str) -> tuple[bool, Optional[str]]:
        for blocked in self.blocked_commands:
            if blocked in code:
                return False, f"Blocked pattern detected: {blocked}"
        return True, None

    async def execute_python(
        self,
        code: str,
        context_vars: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        valid, error = self.validate_code(code)
        if not valid:
            return {"success": False, "error": error, "output": None}

        temp_dir = self.create_sandbox()
        script_path = os.path.join(temp_dir, "agent_script.py")

        wrapper_code = f"""
import json
import sys
import traceback

{code}

if __name__ == "__main__":
    try:
        result = main()
        print("___RESULT_START___")
        print(json.dumps(result, default=str))
        print("___RESULT_END___")
    except Exception as e:
        print("___ERROR_START___")
        print(json.dumps({{"error": str(e), "traceback": traceback.format_exc()}}))
        print("___ERROR_END___")
        sys.exit(1)
"""

        try:
            with open(script_path, "w") as f:
                f.write(wrapper_code)

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout or self.max_execution_time,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {"success": False, "error": "Execution timeout", "output": None}

            stdout_str = stdout.decode("utf-8")
            stderr_str = stderr.decode("utf-8")

            if "___RESULT_START___" in stdout_str:
                result_json = stdout_str.split("___RESULT_START___")[1].split("___RESULT_END___")[0]
                return {"success": True, "output": json.loads(result_json.strip()), "error": None}
            elif "___ERROR_START___" in stdout_str:
                error_json = stdout_str.split("___ERROR_START___")[1].split("___ERROR_END___")[0]
                return {"success": False, "output": None, "error": json.loads(error_json.strip()).get("error", "Unknown error")}
            else:
                return {"success": False, "output": None, "error": stderr_str or "No output"}

        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self._temp_dirs.remove(temp_dir)
            except Exception:
                pass

    async def execute_tool(
        self,
        tool_name: str,
        tool_code: str,
        args: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.execute_python(tool_code, timeout=timeout)


class MultiModelClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        import httpx

        self.httpx_client = httpx.AsyncClient(timeout=60.0)

        if self.config.get("gemini_api_key"):
            self.clients["gemini"] = {
                "api_key": self.config["gemini_api_key"],
                "model": self.config.get("gemini_model", "gemini-1.5-flash"),
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models",
            }

        if self.config.get("nemotron_api_key"):
            self.clients["nemotron"] = {
                "api_key": self.config["nemotron_api_key"],
                "model": self.config.get("nemotron_model", "nvidia/nemotron-3-ultra"),
                "endpoint": self.config.get("nemotron_endpoint", "https://integrate.api.nvidia.com/v1"),
            }

        if self.config.get("huggingface_api_key"):
            self.clients["huggingface"] = {
                "api_key": self.config["huggingface_api_key"],
                "model": self.config.get("huggingface_model", "meta-llama/Llama-3.1-70B-Instruct"),
                "endpoint": "https://api-inference.huggingface.co/models",
            }

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        model_preference: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
    ) -> str:
        model_order = self._resolve_model_order(model_preference)

        for model_name in model_order:
            if model_name not in self.clients:
                continue

            try:
                return await self._call_model(
                    model_name=model_name,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as e:
                print(f"Model {model_name} failed: {e}, trying next...")
                continue

        raise RuntimeError("All models failed to generate response")

    def _resolve_model_order(self, preference: Optional[str]) -> List[str]:
        if preference and preference in self.clients:
            return [preference] + [m for m in self.clients if m != preference]
        return ["nemotron", "gemini", "huggingface"]

    async def _call_model(
        self,
        model_name: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict],
    ) -> str:
        client = self.clients[model_name]

        if model_name == "gemini":
            return await self._call_gemini(client, prompt, system_prompt, temperature, max_tokens, response_format)
        elif model_name == "nemotron":
            return await self._call_nemotron(client, prompt, system_prompt, temperature, max_tokens, response_format)
        elif model_name == "huggingface":
            return await self._call_huggingface(client, prompt, system_prompt, temperature, max_tokens, response_format)

        raise ValueError(f"Unknown model: {model_name}")

    async def _call_gemini(
        self,
        client: Dict,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict],
    ) -> str:
        url = f"{client['endpoint']}/{client['model']}:generateContent?key={client['api_key']}"
        full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if response_format and response_format.get("type") == "json_object":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        res = await self.httpx_client.post(url, json=payload)
        res.raise_for_status()
        res_json = res.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_nemotron(
        self,
        client: Dict,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict],
    ) -> str:
        headers = {
            "Authorization": f"Bearer {client['api_key']}",
            "Content-Type": "application/json",
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": client["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format and response_format.get("type") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        res = await self.httpx_client.post(
            f"{client['endpoint']}/chat/completions",
            json=payload,
            headers=headers,
        )
        res.raise_for_status()
        res_json = res.json()
        return res_json["choices"][0]["message"]["content"]

    async def _call_huggingface(
        self,
        client: Dict,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict],
    ) -> str:
        headers = {
            "Authorization": f"Bearer {client['api_key']}",
            "Content-Type": "application/json",
        }

        full_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>\n"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }

        res = await self.httpx_client.post(
            f"{client['endpoint']}/{client['model']}",
            json=payload,
            headers=headers,
        )
        res.raise_for_status()
        res_json = res.json()

        if isinstance(res_json, list) and len(res_json) > 0:
            return res_json[0].get("generated_text", "")
        return str(res_json)

    async def close(self):
        await self.httpx_client.aclose()


def create_agent_context(
    session_id: str,
    user_prompt: str,
    repo_url: Optional[str] = None,
    canvas_state: Optional[Dict[str, Any]] = None,
    mode: str = "pro",
    markdown_spec: Optional[str] = None,
) -> AgentContext:
    return AgentContext(
        session_id=session_id,
        user_prompt=user_prompt,
        repo_url=repo_url,
        canvas_state=canvas_state,
        mode=mode,
        markdown_spec=markdown_spec,
    )