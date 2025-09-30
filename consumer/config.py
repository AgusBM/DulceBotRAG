import os


# Variables de entorno para RabbitMQ (opcional, pero recomendable)
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "userapp_rabbitmq")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "dcji484hf8ft4")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://127.0.0.1:1234")
API_KEY = os.getenv("API_KEY", None)
MODEL_ID = os.getenv("MODEL_ID", "gemma-3-12b-it@q6_k")
#qwen2.5-7b-instruct-1m
 # SQLite database file
DATABASE_FILE = "bakery.db" 
connection_string = f"DRIVER={{SQLite3 ODBC Driver}};DATABASE={DATABASE_FILE}"
