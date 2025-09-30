# consumer.py

import pika
import json
from your_agent_module import MyAgent  # Importa tu clase de agente según corresponda

# Define el callback para procesar cada mensaje recibido
def process_request(ch, method, properties, body):
    # Convertir el mensaje de JSON a diccionario
    message = json.loads(body)
    client_id = message.get("client_id")
    query = message.get("query")
    
    # Inicializa (o utiliza una instancia existente) de tu agente
    # Asegúrate de pasar los parámetros requeridos (endpoint, model_id, etc.)
    agent = MyAgent(endpoint_url="http://127.0.0.1:1234",
                    model_id="qwen2.5-7b-instruct-1m",
                    knowledge_paths=["agents/customersupportagent"])
    
    # Genera la respuesta utilizando el método generate_response
    response = agent.generate_response(query, client_id)
    print(f"Respuesta para {client_id}: {response}")
    
    # Confirma que el mensaje se procesó correctamente
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Conectar a RabbitMQ (asegúrate que el host y la cola sean los correctos)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    
    # Declarar la cola (por ejemplo, 'customer-service-queue')
    queue_name = 'customer-service-queue'
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Configurar la calidad del servicio para evitar que se asignen demasiados mensajes a un solo consumidor
    channel.basic_qos(prefetch_count=1)
    
    # Asociar la función process_request a la cola
    channel.basic_consume(queue=queue_name, on_message_callback=process_request)
    
    print("Esperando mensajes. Para salir presiona CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    main()
