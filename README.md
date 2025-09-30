This repository contains a full retrieval-augmented generation (RAG) stack for WhatsApp and Telegram. A Node.js bot ingests messages and publishes them to RabbitMQ; a Python consumer performs classification, embeddings, and retrieval over auto-discovered .md/.json knowledge bases, and responds through the chat platforms. The system is modular, containerized with Docker Compose, and configurable via environment variables (embedding endpoint/model, queues, providers). It supports recursive knowledge loading, YAML front-matter metadata, and clean separation between “order” and “support” knowledge domains. Use it as a starting point for customer support, interview automation, or knowledge assistants that run on real messaging apps.

Highlights

WhatsApp/Telegram bots (Node.js) + Python RAG consumer

RabbitMQ for reliable, decoupled messaging

Auto-discovery of knowledge files (agent/*/**/*.md|json)

Pluggable embeddings endpoint (e.g., LM Studio / local / cloud)

Dockerized, .env-driven configuration, CI-friendly layout

Quick start

git clone https://github.com/<you>/rag-whatsapp-telegram.git
cd rag-whatsapp-telegram
cp .env.example .env   # set ENDPOINT_URL, MODEL_ID, RabbitMQ creds, etc.
docker compose up --build -d
node whatsapp-bot/index.js
# (optional) node telegram-bot/index.js


Use cases
Customer support, FAQ agents, interview Q&A, internal knowledge assistants, task triage.

Tech
Python · Node.js · RabbitMQ · Docker · Markdown/JSON knowledge · Embeddings + vector similarity.
