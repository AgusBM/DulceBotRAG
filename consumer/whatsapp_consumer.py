# whatsapp_consumer.py

import asyncio
import json
import os
import time
import pika
import sqlite3  # Changed from pyodbc
from classifier_agent import ClassifierAgent
from backery_agents_rag import OrderAgent, CustomerSupportAgent
from config import connection_string, RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD, ENDPOINT_URL, API_KEY, MODEL_ID, DATABASE_FILE
from pathlib import Path
# Define the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

def list_files(*folders, exts=(".md",)):
    """Devuelve una lista ordenada de rutas (str) a todos los ficheros con las extensiones dadas, de forma recursiva."""
    out = []
    for folder in folders:
        root = (BASE_DIR / folder).resolve()
        if root.exists():
            for ext in exts:
                out.extend(str(p) for p in root.rglob(f"*{ext}"))
    return sorted(set(out))
# Initialize agents
classifier = ClassifierAgent(ENDPOINT_URL, api_key=API_KEY)

# Corrected knowledge paths
ORDER_AGENT_KNOWLEDGE_PATHS = list_files("agent/consumer/order", exts=(".md", ".txt"))
SUPPORT_AGENT_KNOWLEDGE_PATHS = list_files("agent/consumer/support", exts=(".md", ".txt"))

order_agent = OrderAgent(ENDPOINT_URL, MODEL_ID, ORDER_AGENT_KNOWLEDGE_PATHS, api_key=API_KEY)
support_agent = CustomerSupportAgent(ENDPOINT_URL, MODEL_ID, SUPPORT_AGENT_KNOWLEDGE_PATHS, api_key=API_KEY)

# Database Connection
def create_table():
    try:
        conn = sqlite3.connect(DATABASE_FILE)  # Changed from pyodbc
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS WhatsAppMessages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                message TEXT,
                timestamp TEXT  -- Store timestamp as text
            )
        ''')
        conn.commit()
        print("Table WhatsAppMessages created successfully.")
        conn.close()

    except Exception as e:
        print("Error connecting to the database:", e)

# RabbitMQ Configuration
WHATSAPP_QUEUE = "whatsapp_queue"
RESPONSE_QUEUE = "response_queue"  # cola para las responses

class RateLimiter:
    def __init__(self, max_requests, period):
        """
        :param max_requests: Número máximo de solicitudes permitidas.
        :param period: Periodo de tiempo en segundos.
        """
        self.max_requests = max_requests
        self.period = period
        self.requests = {}  # Diccionario para almacenar los timestamps de las solicitudes por usuario

    def is_allowed(self, user_id):
        """
        Retorna True si el usuario (identificado por user_id) puede realizar una nueva solicitud.
        """
        now = time.time()
        # Si el usuario no tiene registros, inicializar la lista
        if user_id not in self.requests:
            self.requests[user_id] = []

        # Eliminar las solicitudes antiguas
        self.requests[user_id] = [ts for ts in self.requests[user_id] if now - ts < self.period]

        # Verificar si se ha alcanzado el límite
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        else:
            return False

RATE_LIMIT = 5  # 5 mensajes
RATE_LIMIT_PERIOD = 60  # por 60 segundos (1 minuto)
rate_limiter = RateLimiter(RATE_LIMIT, RATE_LIMIT_PERIOD)

# Declarar las variables connection y channel en un alcance superior
connection = None
channel = None
async def handle_message(phone_number, text, agent_id):
    """Handle incoming messages"""
    if not rate_limiter.is_allowed(phone_number):
        print(f"Rate limit exceeded for {phone_number}")
        send_response_to_whatsapp(phone_number, "Has excedido el límite de mensajes. Intenta de nuevo en un minuto.")  # Optional: Send a rate limit message
        return

    try:
        # 1. Clasificar y enrutar la consulta
        agent_type = classifier.route_query(text)  # get agent type

        if agent_type == "order":
            response = order_agent.generate_response(text, phone_number, agent_id)
        elif agent_type == "support":
            response = support_agent.generate_response(text, phone_number, agent_id)
        else:
            response = "No entiendo tu consulta."  # Default
        # 2. Enviar la respuesta a través de RabbitMQ
        send_response_to_whatsapp(phone_number, response)
        print(f"Respuesta enviada (a RabbitMQ) para {phone_number}: {response}")

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

def send_response_to_whatsapp(phone_number, text):
    """Envia la respuesta al bot de Node.js a traves de RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)
        message = {
            "phone_number": phone_number,
            "text": text  # Asegúrate de que el texto está aquí
        }

        channel.basic_publish(
            exchange='',
            routing_key=RESPONSE_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
            ))
        print(f"Mensaje enviado a RabbitMQ: {message}")  # Debugging
    except Exception as e:
        print(f"Error al enviar la respuesta a RabbitMQ: {e}")
    finally:
        try:
            if 'channel' in locals() and channel and channel.is_open:
                channel.close()
            if 'connection' in locals() and connection and connection.is_open:
                connection.close()
        except Exception as e:
            print(f"Error al cerrar la conexión a RabbitMQ: {e}")


def callback(ch, method, properties, body):
    """Callback function to process messages from RabbitMQ"""
    message_data = json.loads(body)
    phone_number = message_data.get("phone_number")
    message_text = message_data.get("message")
    agent_id = message_data.get("agent_id")  # Extrae el agent_id del mensaje

    if phone_number and message_text and agent_id:
        try:
            print(f"Mensaje Recibido: {message_text} | Numero de telefono: {phone_number} | Agent ID: {agent_id}")
            asyncio.run(handle_message(phone_number, message_text, agent_id))  # Llama a la función asíncrona con agent_id
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    global connection, channel

    try:
        # Initialize the RabbitMQ connection
        print("Servidor RabbitMQ:", RABBITMQ_HOST)
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=WHATSAPP_QUEUE, durable=True)
        create_table()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=WHATSAPP_QUEUE, on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()  # This keeps the script running

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()

    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando...")

    except Exception as e:
        print(f"Error inesperado: {e}")

    finally:
        try:
            if channel:
                channel.close()
            if connection:
                connection.close()
        except Exception as e:
            print(f"Error al cerrar la conexión: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando...")
    try:
        if channel:  # check if they are defined
            channel.close()
        if connection:
            connection.close()
    except:
        pass
