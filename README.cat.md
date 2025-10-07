# Agent RAG per a WhatsApp

**Què fa**

* Respon entrevistes i dona suport via WhatsApp.
* Recupera coneixement (RAG) des de `.md/.json` amb autodescoberta.
* Orquestra amb RabbitMQ i Docker.

**Stack**
Python (embeddings + retrieval) · Node.js (bots) · RabbitMQ · Docker · (opcional) PostgreSQL/MSSQL.

## Demo

* 🎥 Vídeo mostrant el flux end-to-end.
* 🖼️ Captures / vídeo: `/video/agenteRAG.mp4`

## Arquitectura

![Diagrama](images/arquitectura.png)

## Posada en marxa

```bash
# 1) Clona el repositori
git clone https://github.com/AgusBM/DulceBotRAG.git
cd DulceBotRAG

# 2) Carrega els teus fitxers md o txt a les carpetes de coneixement.
# A la carpeta classifier, afegeix alguns documents de mostra
# per tal que el sistema pugui classificar el missatge rebut i escollir
# entre l’agent de suport i l’agent de servei.
# A la carpeta consumer, carrega tota la base de coneixement.
# ├── agent/
# │   ├── classifier/
# │          ├── order/
# │          └── support/
# │   └── consumer/
# │          ├── order/
# │          └── support/

# 3) Actualitza les variables d’entorn a .env.example, index.js i config.py
cp .env.example .env
# Omple ENDPOINT_URL, API_KEY, MODEL_ID, RABBITMQ_USER/PASSWORD, etc.

# 4) Instal·la i llança LM Studio
# descarrega l’AppImage de https://lmstudio.ai/
chmod u+x LM_Studio-*.AppImage
./LM_Studio-*.AppImage --appimage-extract
cd squashfs-root
sudo chown root:root chrome-sandbox
sudo chmod 4755 chrome-sandbox
./lm-studio
# S’obrirà una finestra; activa el servidor en mode desenvolupador.
# Estarà disponible a http://127.0.0.1:1234

# 5) Inicia RabbitMQ amb Docker
cd DulceBotRAG
docker compose up --build -d

# 6) Instal·la Node i inicia el Bot de WhatsApp
# (El primer cop mostrarà un codi QR per enllaçar el dispositiu)

# Instal·lar Volta (Linux/macOS)
curl https://get.volta.sh | bash
# tanca i torna a obrir el terminal, o bé:
source ~/.bashrc  # o ~/.zshrc segons el teu shell

# Instal·la i fixa Node 22.9.0 per al projecte actual
volta install node@22.9.0
volta pin node@22.9.0   # desa la versió a package.json -> "volta": { "node": "22.9.0" }

# Instal·lar Baileys (llibreria de WhatsApp)
npm install @whiskeysockets/baileys

# Inicia el bot
node whatsapp-bot/index.js
# Escaneja el codi QR que apareix al terminal el primer cop per vincular la sessió de WhatsApp

# 7) Crea i activa l’entorn de Python (i verifica la versió)
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
# Crear i activar entorn virtual
python3.12 -m venv .venv312
source .venv312/bin/activate
python -V
# Python 3.12.3

# 8) Instal·la dependències

# Opció A (ràpida): usar requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Opció B (recomanada per desenvolupament): pip-tools
pip install --upgrade pip pip-tools
# compilar de requirements.in a requirements.txt
pip-compile requirements.in -o requirements.txt
# sincronitzar l’entorn amb el lock generat
pip-sync requirements.txt

# 9) Inicia el consumer de WhatsApp
python consumer/whatsapp_consumer.py

# 10) L’agent respondrà les preguntes enviades al compte de WhatsApp vinculat. Bon servei!
```
