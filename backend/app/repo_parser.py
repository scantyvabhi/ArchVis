import re
from typing import Dict, Any, List, Optional
import httpx

class RepoParser:
    """Fetches repository manifests and README files to reverse-engineer architecture."""

    @staticmethod
    def extract_owner_and_repo(url: str) -> tuple[Optional[str], Optional[str]]:
        url = url.strip().rstrip('/')
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            return owner, repo
        
        # Handle format "owner/repo"
        parts = url.split('/')
        if len(parts) == 2 and not url.startswith('http'):
            return parts[0], parts[1]

        return None, None

    @classmethod
    async def fetch_repo_context(cls, repo_url: str) -> Dict[str, Any]:
        owner, repo = cls.extract_owner_and_repo(repo_url)
        if not owner or not repo:
            raise ValueError(f"Invalid GitHub URL: {repo_url}. Expected format: https://github.com/owner/repo")

        headers = {
            "User-Agent": "ArchVis-AI-Agent",
            "Accept": "application/vnd.github.v3+json",
        }

        detected_tech: List[str] = []
        readme_content = ""
        files_found: List[str] = []

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # 1. Fetch Repo metadata
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            try:
                repo_res = await client.get(api_url, headers=headers)
                if repo_res.status_code == 200:
                    data = repo_res.json()
                    primary_lang = data.get("language")
                    if primary_lang:
                        detected_tech.append(primary_lang)
            except Exception as e:
                print(f"Error fetching repo metadata: {e}")

            # 2. Fetch Root Directory Contents
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            try:
                contents_res = await client.get(contents_url, headers=headers)
                if contents_res.status_code == 200:
                    files = contents_res.json()
                    if isinstance(files, list):
                        files_found = [f.get("name", "") for f in files]
            except Exception as e:
                print(f"Error fetching contents: {e}")

            # 3. Detect manifests
            manifest_map = {
                "package.json": "Node.js / JavaScript / TypeScript",
                "requirements.txt": "Python",
                "pyproject.toml": "Python",
                "Dockerfile": "Docker Container",
                "docker-compose.yml": "Docker Compose Multi-Container",
                "go.mod": "Golang",
                "Cargo.toml": "Rust",
                "pom.xml": "Java Maven",
                "build.gradle": "Java / Kotlin Gradle",
                "redis.conf": "Redis",
                "postgres": "PostgreSQL",
            }
            for file_name in files_found:
                for key, tech in manifest_map.items():
                    if key.lower() in file_name.lower():
                        detected_tech.append(tech)

            # 4. Fetch README
            for branch in ["main", "master"]:
                raw_readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
                try:
                    rm_res = await client.get(raw_readme_url, headers=headers)
                    if rm_res.status_code == 200 and rm_res.text:
                        readme_content = rm_res.text[:4000] # Excerpt
                        break
                except Exception:
                    continue

        # If rate-limited or minimal files detected, infer from repo name
        if not detected_tech:
            repo_lower = repo.lower()
            if "redis" in repo_lower:
                detected_tech = ["C", "In-Memory Key-Value", "Replication", "Sentinel"]
            elif "fastapi" in repo_lower:
                detected_tech = ["Python", "FastAPI", "Starlette", "Uvicorn", "Pydantic"]
            elif "kafka" in repo_lower:
                detected_tech = ["Java", "Distributed Streaming", "ZooKeeper/KRaft"]
            elif "supabase" in repo_lower:
                detected_tech = ["PostgreSQL", "GoTrue Auth", "PostgREST", "Realtime"]
            else:
                detected_tech = ["Web Service", "REST API", "Database"]

        return {
            "repo_url": repo_url,
            "owner": owner,
            "repo": repo,
            "files": files_found,
            "detected_tech": list(dict.fromkeys(detected_tech)),
            "readme_excerpt": readme_content or f"Repository {owner}/{repo}",
        }
