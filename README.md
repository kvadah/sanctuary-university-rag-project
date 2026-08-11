# 🎓 KnowledgeHub AI — Sanctuary University

KnowledgeHub AI is an AI-powered knowledge assistant built specifically for Sanctuary University. It allows students, faculty members, and administrative staff to query university handbooks, academic regulations, course catalogs, admission guidelines, and departmental websites using natural language, returning accurate, citation-backed answers.

---

## 🏗️ Project Architecture Overview

This project is built using a modular, service-oriented architecture:

- **`backend/`**: FastAPI (Python 3.11+) service providing REST APIs, authentication, hybrid retrieval RAG pipeline, and LLM integrations.
- **`frontend/`**: Next.js (TypeScript, Tailwind CSS, Zustand, React Query) web application for student/faculty chat and admin document management.
- **`docker/`**: Nginx proxy and service container configurations.
- **`scripts/`**: Utility scripts for database initialization, data ingestion, and testing.

---

## ⚡ Quick Start (Local Development)

### 1. Environment Setup
Copy the environment template and adjust configurations:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
Start the complete infrastructure stack (FastAPI, Next.js, PostgreSQL, Qdrant, Redis, MinIO, Celery):
```bash
docker-compose up --build
```

---

## 📚 Documentation
For complete technical specifications, database schema designs, and RAG pipeline blueprints, refer to the specification documents located in the parent directory (`../`).
