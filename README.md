# Agente RAG para WhatsApp y Telegram

**Qué hace**  
- Responde entrevistas y soporte vía WhatsApp.  
- Recupera conocimiento (RAG) desde `.md/.json` con autodiscovery.  
- Orquestación con RabbitMQ y Docker.

**Stack**  
Python (embeddings + retrieval) · Node.js (bots) · RabbitMQ · Docker · (opcional) PostgreSQL/MSSQL.

## Demo
- 🎥 Video mostrando el flujo end-to-end.
- 🖼️ Capturas: `images/`

## Arquitectura
![Diagrama](images/arquitectura.png)

## Puesta en marcha
```bash
# 1) Clonar
git clone https://github.com/AgusBM/DulceBotRAG.git
cd DulceBotRAG

# 2) Inicia LMStudio y carga tu modelo LLM favorito
../squashfs-root/./lm-studio

# 3) Variables de entorno .env y config.py
cp .env.example .env
# Rellena ENDPOINT_URL, API_KEY, MODEL_ID, RABBITMQ_USER/PASSWORD, etc.

# 4) Docker (recomendado)
docker compose up --build -d

# 5) Bot
node whatsapp-bot/index.js

# 6) Inicia el consumer de WhatsApp
python consumer/whatsapp_consumer.py


