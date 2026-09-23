# 🏗️ ArchVis AI

> **Minimalist, Production-Ready Browser-Based AI System Design Visualizer & Real-Time Simulator**

ArchVis AI transforms high-level architectural ideas, GitHub repositories, and design specifications into interactive React Flow graph diagrams with live traffic simulation, bottleneck detection, and multi-agent architectural intelligence (Gemini 2.5 Flash, Nemotron-3 Ultra, Hugging Face, TypeSafe AI).

---

## 📸 Core Capabilities

- **Multi-Agent Architecture Generation**: Natural language prompt-to-graph synthesis powered by a consensus-based multi-agent pipeline (Repo Fetcher → Architecture Analyst → Diagram Builder) with LLM fallback chain.
- **Dual-Mode System Design**:
  - **Learner Mode**: Explains *what* each component is, *why* it was chosen, and foundational trade-offs with educational tips.
  - **Professional Mode**: Produces enterprise-grade HLD/LLD diagrams with caching tiers, partition strategies, and concrete tech stacks.
- **Semantic Canvas Zooming**:
  - **Macro View (< 0.5x)**: Compact cards with component badges and titles.
  - **Normal View (0.5x – 0.8x)**: Standard cards with throughput and utilization gauges.
  - **Micro View (> 0.8x)**: Detailed configuration specs including latency, replication topology, and failure rates.
- **Real-Time Simulation Engine (Web Worker)**:
  - 60 FPS non-blocking queueing model simulating traffic propagation.
  - Automatic detection of bottlenecks where incoming load exceeds component capacity.
  - Red pulsing alerts and live telemetry overlay (System Throughput, Average Latency, P99 Tail Latency, Error Rate).
- **Component Drawer**: Searchable drag-and-drop and single-click insertion of APIs, Gateways, Services, Caches, Databases, Queues, and Storage.
- **Node Configuration Drawer**: Live adjustment of Latency (ms), Request Rate (RPS), Capacity (RPS), and Failure Rate (%).
- **Reverse-Engineer Repos**: Provide any public GitHub repo URL to extract file structures and READMEs into an interactive architecture.
- **TypeSafe AI Structured Validation**: Integrated quality gates using TypeSafe AI's JEV model (Noul, Choice, Score primitives) for production readiness checks, security posture, scalability scoring, and maintainability ratings.
- **Command Palette (`/`)**: Slash-command interface for both modes with keyboard navigation (↑/↓/Enter/Escape), filter-by-name, and direct actions.
- **Live Agent Thinking Display**: Real-time visualization of multi-agent pipeline progress with reasoning, tool calls, model used, and confidence scores.
- **High-Resolution Export**: Export 300 DPI PNG, SVG, and JSON diagrams preserving vector crispness, as well as importable JSON specs.

---

## 📁 Repository Structure

```
archvis-ai/
├── frontend/                     # React + Vite + TypeScript + Tailwind CSS + React Flow
│   ├── src/
│   │   ├── components/
│   │   │   ├── canvas/           # ArchitectureCanvas, CustomNode (semantic zooming), CustomEdge
│   │   │   ├── sidebar/          # ComponentDrawer (drag & drop component palette)
│   │   │   ├── drawer/           # NodeConfigDrawer (latency, RPS, capacity, failure %)
│   │   │   ├── assistant/        # FloatingAssistant, RepoIngestionModal, MetricsOverlay
│   │   │   └── layout/           # TopBar (simulate, auto-layout, presets, export)
│   │   ├── workers/              # simulation.worker.ts (traffic propagation & queuing engine)
│   │   ├── services/             # api.ts (typed FastAPI client)
│   │   ├── constants/            # presets.ts, components.ts
│   │   └── utils/                # layout.ts (Dagre auto-align), export.ts (300 DPI PNG/JSON)
│   ├── Dockerfile
│   └── nginx.conf
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── main.py               # REST API endpoints & CORS middleware
│   │   ├── ai_agent.py           # Gemini 2.5 Flash agent & fallback heuristic engine
│   │   ├── repo_parser.py        # GitHub repository manifest & README extractor
│   │   └── schemas.py            # Pydantic models & validation schemas
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml            # Multi-container orchestration
├── .env.example                  # Environment variable reference
└── README.md
```

---

## 🛠️ Prerequisites

- **Node.js**: v20.x or higher (npm v10+)
- **Python**: v3.10 or higher
- **Docker & Docker Compose**: (optional, for containerized execution)
- **Google Gemini API Key**: [Get your free key from Google AI Studio](https://aistudio.google.com/app/apikey)
- **NVIDIA Nemotron-3 Ultra API Key**: [Get your key from NVIDIA Build](https://build.nvidia.com/explore/discover)
- **Hugging Face API Key**: [Get your token from Hugging Face](https://huggingface.co/settings/tokens)
- **TypeSafe AI API Key**: [Get your key from TypeSafe Console](https://console.typesafe.ai/keys)

> **Note**: The system features a robust LLM fallback chain (Nemotron → Gemini → Hugging Face) and built-in mock generation so the app works seamlessly even without API keys. TypeSafe AI key is required for structured quality gates.

---

## ⚙️ Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your API keys:
   ```env
   # Google Gemini API Key (Gemini 2.5 Flash)
   # Obtain from https://aistudio.google.com/app/apikey
   GEMINI_API_KEY="your_gemini_key"

   # NVIDIA Nemotron-3 Ultra API Key
   # Obtain from https://build.nvidia.com/explore/discover
   NEMOTRON_API_KEY="your_nemotron_key"

   # Hugging Face API Key (for open-source models)
   # Obtain from https://huggingface.co/settings/tokens
   HUGGINGFACE_API_KEY="your_hf_key"

   # TypeSafe AI API Key (for structured quality gates)
   # Obtain from https://console.typesafe.ai/keys
   TYPESAFE_API_KEY="your_typesafe_key"

   # Multi-Agent Configuration
   ORCHESTRATION_MODE=consensus
   MAX_CONSENSUS_ROUNDS=3
   CONSENSUS_THRESHOLD=0.8
   SANDBOX_TIMEOUT=30
   SANDBOX_MEMORY_MB=512
   ```

---

## 🚀 Quick Start Guide

### Option A: One-Command Docker Start (Recommended)

From the project root:

```bash
docker-compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`

---

### Option B: Local Standalone Development

#### 1. Start the Python Backend
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Start the Frontend Dev Server
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 📡 Backend API Endpoints Specification

Interactive Swagger UI is accessible at `http://localhost:8000/docs`.

| Method | Endpoint | Description | Request Body |
|---|---|---|---|
| `POST` | `/api/generate-architecture` | Synthesizes a system design graph from prompt | `{"prompt": string, "mode": "learner" \| "pro"}` |
| `POST` | `/api/parse-repo` | Reverse-engineers a GitHub repository | `{"repo_url": string, "mode": "learner" \| "pro"}` |
| `POST` | `/api/chat` | Contextual Q&A conditioned on active canvas | `{"message": string, "canvas_state": object, "mode": string}` |
| `POST` | `/api/simulate` | Pre-flight validation of node throughput | `{"nodes": array, "edges": array}` |
| `GET` | `/api/health` | Backend and LLM health check | None |
| `POST` | `/api/agent/orchestrate` | Run full multi-agent orchestration | `{"prompt": string, "repo_url": string?, "canvas_state": object?, "mode": string}` |
| `POST` | `/api/agent/chat` | Multi-agent contextual chat | `{"message": string, "canvas_state": object, "mode": string}` |
| `GET` | `/api/agent/models` | List available LLM models | None |

---

## 🤖 TypeSafe AI Integration

ArchVis AI integrates **TypeSafe AI** for structured architectural quality gates using their JEV (Judgment Evaluation) model with three primitives:

### Evaluation Primitives
| Primitive | Type | Use Case | Output |
|-----------|------|----------|--------|
| **Noul** | Yes/No | Pass/Fail gates | Probability 0-1 |
| **Choice** | Classification | Pattern detection, security posture | Choice + probabilities + confidence |
| **Score** | Ordinal rating | Quality dimensions | Weighted score 0-4 + confidence |

### Built-in Quality Gates
- **Circular Dependencies** (Noul): Detects circular data flows
- **Single Point of Failure** (Noul): Identifies components whose failure brings down the system
- **Cloud-Native Best Practices** (Noul): Validates 12-factor, observability, circuit breakers
- **Production Readiness** (Noul): Checks monitoring, scaling, security, DR

### Quality Scores (0-4 scale)
- **Scalability**: Horizontal scaling capability
- **Observability**: Logging, metrics, tracing, SLIs/SLOs
- **Cost Efficiency**: Resource utilization optimization
- **Maintainability**: Coupling, boundaries, documentation
- **Reliability**: Fault tolerance, recovery time, SLA potential

### Classifications
- **Architecture Pattern**: microservices, modular_monolith, serverless, event_driven, layered, custom
- **Primary Bottleneck**: database, network, compute, cache, none
- **Security Posture**: hardened, standard, basic, weak

### Accessing Validation
1. **Command Palette**: Type `/` and select "TypeSafe AI Validation" (Pro mode) or "Validate diagram" (both modes)
2. **Auto-run**: Runs automatically after multi-agent orchestration completes
3. **Badge Display**: Real-time validation badge in top-right of canvas showing gates passed, quality score, and recommendations

---

## ☁️ Step-by-Step AWS Free Tier Deployment

Deploy ArchVis AI on the **AWS Free Tier** using **AWS Amplify** for the frontend and **AWS EC2 (t2.micro / t3.micro)** for the backend.

### 1. Backend on AWS EC2 (t2.micro)
1. **Launch an EC2 Instance**:
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: `t2.micro` (Free Tier eligible)
   - Security Group: Allow SSH (`22`), HTTP (`80`), and Custom TCP (`8000`).
2. **SSH into the Instance**:
   ```bash
   ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
   ```
3. **Install Docker and Docker Compose**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   sudo usermod -aG docker ubuntu
   ```
4. **Deploy Backend**:
   ```bash
   git clone <YOUR_REPO_URL>
   cd ArchVisAI/backend
   echo "GEMINI_API_KEY=your_key_here" > .env
   docker build -t archvis-backend .
   docker run -d --name archvis-backend -p 8000:8000 --env-file .env archvis-backend
   ```
   Verify backend health: `curl http://localhost:8000/api/health`.

### 2. Frontend on AWS Amplify Hosting
1. Open the [AWS Amplify Console](https://console.aws.amazon.com/amplify).
2. Select **Host web app** and connect your GitHub repository.
3. Configure the Build Settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/dist
       files:
         - '**/*'
     cache:
       paths:
         - frontend/node_modules/**/*
   ```
4. **Add Reverse Proxy Rule in Amplify**:
   In Amplify Console -> **Rewrites and redirects**:
   - Source address: `/api/<*>`
   - Target address: `http://<EC2_PUBLIC_IP>:8000/api/<*>`
   - Type: `200 (Rewrite)`
5. Click **Save and Deploy**. Your web app is now globally distributed via AWS CloudFront with SSL!

---

## 📄 License

MIT License. Crafted with precision for system designers and software engineers.
