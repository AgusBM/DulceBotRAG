# Agente RAG para WhatsApp

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
# 1) Clona el repositorio
git clone https://github.com/AgusBM/DulceBotRAG.git
cd DulceBotRAG

# 2) Carga tus archivos md o txt en las carpetas de conocimiento,
# en la carpeta classifier carga algunos documentos de muestra
# que permita clasificar el mensaje recibido y escoger entre
# el agente de soporte y el agente de servicio.
# En la carpeta consumer carga toda la base de conocimiento.
# ├── agent/            
# │   ├── classifier/
# │          ├── order/
# │          └── support/
# │   └── consumer/
# │          ├── order/
# │          └── support/

# 3) Actualiza las variables de entorno .env y config.py
cp .env.example .env
# Rellena ENDPOINT_URL, API_KEY, MODEL_ID, RABBITMQ_USER/PASSWORD, etc.

# 4) Inicia LMStudio y carga tu modelo LLM favorito
../squashfs-root/./lm-studio

# 5) Inicia RabbitMQ en Docker
docker compose up --build -d

# 6) Instalar Node e iniciar el Bot de WhatsApp, la primera vez te mostrara un QR para enlazar con tu dispositivo
# Instalar Volta (Linux/macOS)
curl https://get.volta.sh | bash
# cierra y abre la terminal, o:
source ~/.bashrc  # o ~/.zshrc según tu shell

# Instalar y fijar Node 22.9.0 para el proyecto actual
volta install node@22.9.0
volta pin node@22.9.0   # guarda la versión en package.json -> "volta": { "node": "22.9.0" }

# Inicia el bot
node whatsapp-bot/index.js

# 7) Activar el entorno y comprobar version de Python
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate  # Windows PowerShell
python -V
# Python 3.12.3

# 8) Instalar dependencias

Opción A (rápida): usar requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

Opción B (recomendado para desarrollo): pip-tools
pip install --upgrade pip pip-tools
# compilar desde requirements.in a requirements.txt
pip-compile requirements.in -o requirements.txt
# sincronizar el entorno con el lock generado
pip-sync requirements.txt

# 9) Inicia el consumer de WhatsApp
python consumer/whatsapp_consumer.py


