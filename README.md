# Can You Pi?

<div align="center">

**A Pi memorisation game with conversational gameplay and real-time verification**

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Groq](https://img.shields.io/badge/Groq_AI-000000?style=for-the-badge)](https://groq.com/)

[**Live Demo**](https://can-you-pi-1041928881529.us-central1.run.app) · [**API Docs**](https://can-you-pi-1041928881529.us-central1.run.app/docs)

</div>

---

## Overview

**Can You Pi?** is an interactive game that challenges users to recite digits of Pi from memory, powered by a conversational AI assistant. Built with modern cloud-native architecture, the application leverages FastAPI for high-performance async operations, Groq's LLM for natural language interactions, and Google Cloud Run for scalable serverless deployment.

The game validates user input against a dataset of 1 million Pi digits in real-time, provides intelligent hints through AI conversation, and supports multiple gameplay modes including standard sequential play and custom position challenges.

### Motivation

After successfully memorising 100 decimals of Pi, I wanted to create an engaging way to test and improve Pi memorisation skills. This project combines my interests in mathematics, AI, and cloud architecture into a practical, production-ready application.

### Project Evolution

Started as a Python CLI game, evolved into a full-stack application with:
- Terminal-based gameplay for quick practice sessions
- RESTful API backend with FastAPI for web/mobile integration
- AI-powered conversational interface using Model Context Protocol (MCP)
- Production deployment on Google Cloud Platform with enterprise-grade security
- Frontend in another repo

**Future plans:** Java/Spring Boot implementation for polyglot architecture exploration

---

## Architecture

### System Design

```
┌─────────────┐
│   Client    │
│  (Any HTTP) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   Google Cloud Run      │
│  ┌──────────────────┐  │
│  │  FastAPI Server  │  │
│  │  (Uvicorn/ASGI)  │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │   Game Logic     │  │
│  │  - Verify digits │  │
│  │  - Track state   │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │   MCP Server     │  │
│  │  (Tool Router)   │  │
│  └────────┬─────────┘  │
└───────────┼─────────────┘
            │
            ▼
    ┌───────────────┐
    │   Groq API    │
    │  (LLM/Chat)   │
    └───────────────┘
```

### Technology Stack

**Backend Framework**
- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **Uvicorn**: Lightning-fast ASGI server for production workloads
- **Pydantic**: Runtime type validation and serialisation

**AI & Intelligence**
- **Groq API**: High-performance LLM inference for conversational AI
- **Model Context Protocol (MCP)**: Tool-based AI architecture for extensible game commands
- **Custom Tool System**: Structured function calling for game operations

**Cloud Infrastructure**
- **Google Cloud Run**: Fully managed serverless container platform with automatic scaling (0→∞)
- **Google Cloud Build**: Automated container builds from source with multi-stage optimisation
- **Google Secret Manager**: Encrypted secret storage with IAM-controlled access
- **Artifact Registry**: Private container image repository with vulnerability scanning

**Development & Operations**
- **Docker**: Multi-stage builds with security hardening (non-root user, minimal surface)
- **Python 3.11**: Latest stable Python with performance improvements
- **Git**: Version control with structured commit history

---

## Features

### Core Gameplay
- **Sequential Challenge**: Recite Pi digits starting from position 0 (3.14159...)
- **Custom Start Position**: Jump to any position within 1 million digits
- **Real-time Verification**: Instant validation against authoritative Pi dataset
- **Precise Error Feedback**: Identifies exact position of first mistake with correct digit

### AI Assistant
- **Natural Language Interaction**: Chat-based gameplay without rigid commands
- **Context-Aware Responses**: Maintains conversation history across game sessions
- **Intelligent Hints**: AI can provide strategic hints without spoiling the challenge
- **Multi-tool Integration**: AI orchestrates game operations through MCP tool system

### Developer Experience
- **RESTful API**: Clean HTTP endpoints for any client (web, mobile, CLI)
- **Auto-generated Documentation**: Interactive Swagger UI at `/docs`
- **CORS Enabled**: Ready for frontend integration
- **Stateless Design**: Horizontal scaling without session affinity

### Production Ready
- **Health Checks**: Kubernetes-style health endpoints for orchestration
- **Structured Logging**: JSON logs for cloud monitoring and alerting
- **Security Hardening**: Non-root containers, secret management, minimal attack surface
- **Zero-Downtime Deployment**: Cloud Run's gradual rollout with traffic splitting

---

## Deployment

### Production (Google Cloud Run)

The application is deployed on Google Cloud Run with the following configuration:

**Infrastructure**
- **Region**: us-central1 (Iowa) 
- **Scaling**: Automatic scaling from 0 to N instances based on traffic
- **Authentication**: Public access with unauthenticated invocations
- **Port**: 8000 (custom from default 8080)

**Security**
- API keys stored in Google Secret Manager 
- Container runs as non-root user (UID 1000)
- Minimal base image (python:3.11-slim)
- IAM-controlled secret access via service account

**Deployment Command**
```bash
gcloud run deploy can-you-pi \
  --source . \
  --port 8000 \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets="GROQ_API_KEY=groq-api-key:latest"
```

### Local Development

**Using Docker Compose**
```bash
# Set environment variables
echo "GROQ_API_KEY=your_key_here" > .env

# Start services
docker-compose up

# Access at http://localhost:8000
```

**Without Docker**
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### CLI Version (Terminal Game)

For quick practice sessions without the API server, you can play directly in your terminal:

**Original CLI (Single digit input)**
```bash
# Install dependencies first
pip install -r requirements.txt

# Run the game
python cli/cli.py
```

**Enhanced CLI (Multiple game modes)**
```bash
# Install dependencies (requires readchar)
pip install -r requirements.txt

# Run the enhanced version
python cli/cli_v2.py
```

The enhanced CLI (`cli_v2.py`) offers three game modes:
1. **Standard Mode**: Start from the beginning (3.14159...)
2. **Custom Mode**: Jump to any position within 1 million digits
3. **Decimal Guess Mode**: Test your knowledge of specific Pi positions

---

## Project Structure

```
can-you-pi/
├── backend/
│   ├── main.py              # FastAPI application entry
│   ├── routes.py            # API endpoint definitions
│   └── __init__.py
├── mcp/
│   ├── server.py            # MCP tool definitions
│   └── client.py            # MCP client logic
├── cli/
│   ├── cli.py               # Original terminal game
│   └── cli_v2.py            # Enhanced CLI version
├── assets/
│   └── pi_decimals.txt      # 1M digits of Pi dataset
├── utils/
│   └── clean_pi.py          # Data preprocessing utilities
├── game_logic.py            # Core game mechanics
├── Dockerfile               # Multi-stage container build
├── docker-compose.yml       # Local development orchestration
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Technical Highlights

### Performance
- **Async I/O**: Non-blocking request handling with FastAPI + Uvicorn
- **Efficient Lookups**: Optimised string operations for Pi digit verification
- **Cold Start < 2s**: Quick container startup on Cloud Run

### Scalability
- **Stateless Architecture**: Each request is independent, enabling horizontal scaling
- **Serverless Auto-scaling**: Cloud Run handles 1 to 10,000+ concurrent requests automatically
- **Cost Efficient**: Scales to zero when idle, pay only per request

### Code Quality
- **Type Hints**: Full Python type annotations for IDE support and static analysis
- **Pydantic Models**: Runtime validation of all API inputs/outputs
- **Structured Code**: Clear separation of concerns (routes, logic, MCP, CLI)

---


