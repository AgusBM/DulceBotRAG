#!/bin/bash
sleep 30
# Esperar a que RabbitMQ esté listo
echo "Waiting for RabbitMQ to be ready..."
until rabbitmqctl status; do
  echo "RabbitMQ not ready yet, waiting..."
  sleep 5
done

echo "RabbitMQ is ready!"

# Crea el usuario
#echo "Creating user: userapp_rabbitmq"
#rabbitmqctl add_user userapp_rabbitmq dcji484hf8ft4

# Otorga permisos al usuario
echo "Setting permissions for user: userapp_rabbitmq"
rabbitmqctl set_permissions -p / userapp_rabbitmq ".*" ".*" ".*"

# Asigna la etiqueta de administrador al usuario
echo "Setting tags for user: userapp_rabbitmq"
rabbitmqctl set_user_tags userapp_rabbitmq administrator

echo "RabbitMQ configuration complete."

# Inicia RabbitMQ en primer plano
echo "Starting RabbitMQ server..."
exec rabbitmq-server
