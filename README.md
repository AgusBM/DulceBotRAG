[English](README.md) | [Català](README.cat.md) | [Español](README.es.md)


# RAG Agent for WhatsApp

**What it does**

* Handles interviews and support via WhatsApp.
* Retrieves knowledge (RAG) from `.md/.json` with autodiscovery.
* Orchestrates with RabbitMQ and Docker.

**Stack**
Python (embeddings + retrieval) · Node.js (bots) · RabbitMQ · Docker · (optional) PostgreSQL/MSSQL.

## Demo

* 🎥 Video showing the end-to-end flow.
* 🖼️ Screenshots / video: `/video/agenteRAG.mp4`

## Architecture

![Diagram](images/arquitectura.png)

## Getting Started

```bash
# 1) Clone the repository
git clone https://github.com/AgusBM/DulceBotRAG.git
cd DulceBotRAG

# 2) Load your md or txt files into the knowledge folders.
# In the classifier folder, add a few sample documents
# so the system can classify the incoming message and pick
# between the support agent and the service agent.
# In the consumer folder, load the whole knowledge base.
# ├── agent/
# │   ├── classifier/
# │          ├── order/
# │          └── support/
# │   └── consumer/
# │          ├── order/
# │          └── support/

# 3) Update environment variables in .env.example, index.js, and config.py
cp .env.example .env
# Fill in ENDPOINT_URL, API_KEY, MODEL_ID, RABBITMQ_USER/PASSWORD, etc.

# 4) Install and launch LM Studio
# download the AppImage from https://lmstudio.ai/
chmod u+x LM_Studio-*.AppImage
./LM_Studio-*.AppImage --appimage-extract
cd squashfs-root
sudo chown root:root chrome-sandbox
sudo chmod 4755 chrome-sandbox
./lm-studio
# A window will open; enable the server in developer mode.
# It will be available at http://127.0.0.1:1234

# 5) Start RabbitMQ with Docker
cd DulceBotRAG
docker compose up --build -d

# 6) Install Node and start the WhatsApp Bot
# (On first run, it will show a QR to link your device)

# Install Volta (Linux/macOS)
curl https://get.volta.sh | bash
# close and reopen the terminal, or:
source ~/.bashrc  # or ~/.zshrc depending on your shell

# Install and pin Node 22.9.0 for the current project
volta install node@22.9.0
volta pin node@22.9.0   # saves the version in package.json -> "volta": { "node": "22.9.0" }

# Install Baileys (WhatsApp library)
npm install @whiskeysockets/baileys

# Start the bot
node whatsapp-bot/index.js
# Scan the QR code shown in the terminal the first time to link your WhatsApp session

# 7) Create and activate the Python environment (and verify version)
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
# Create and activate virtual environment
python3.12 -m venv .venv312
source .venv312/bin/activate
python -V
# Python 3.12.3

# 8) Install dependencies

# Option A (quick): use requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Option B (recommended for development): pip-tools
pip install --upgrade pip pip-tools
# compile from requirements.in to requirements.txt
pip-compile requirements.in -o requirements.txt
# sync the environment with the generated lock
pip-sync requirements.txt

# 9) Start the WhatsApp consumer
python consumer/whatsapp_consumer.py

# 10) The agent will answer questions sent to the linked WhatsApp account. Enjoy!
```

