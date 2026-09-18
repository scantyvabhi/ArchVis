# 🏗️ ArchVis AI

> **Minimalist, Production-Ready Browser-Based AI System Design Visualizer & Real-Time Simulator**

ArchVis AI transforms high-level architectural ideas, GitHub repositories, and design specifications into interactive React Flow graph diagrams with live traffic simulation, bottleneck detection, and Gemini 1.5 Flash architectural intelligence.

---

## 📸 Core Capabilities

- **AI Architecture Generation**: Natural language prompt-to-graph synthesis powered by Google Gemini 1.5 Flash.
- **Dual-Mode System Design**:
  - **Learner Mode**: Explains *what* each component is, *why* it was chosen, and foundational trade-offs.
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
- **High-Resolution Export**: Export 300 DPI PNG diagrams preserving vector crispness, as well as importable JSON specs.

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
│   │   ├── ai_agent.py           # Gemini 1.5 Flash agent & fallback heuristic engine
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

---

## ⚙️ Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your Google Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_key
   ```
   *(Note: ArchVis AI features built-in fallback mock generation so the app works seamlessly even before setting your key).*

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
| `GET` | `/api/health` | Backend and Gemini API health check | None |

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
