#!/bin/bash

# Variables de entorno
SA_PASSWORD=$SA_PASSWORD
APP_USER=$DB_UID
APP_PASS=$DB_PASSWORD

# Iniciar SQL Server en segundo plano
echo "Starting SQL Server..."
/opt/mssql/bin/sqlservr &
SQLSERVERPID=$!

# Esperar a que SQL Server esté listo
echo "Waiting for SQL Server to be ready..."
until /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SELECT 1" &> /dev/null; do
  echo "SQL Server not ready yet, waiting..."
  sleep 5
done

echo "SQL Server is ready!"

# Ejecutar el script de inicialización de la base de datos (init.sql)
echo "Creating database and user..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -i /docker-entrypoint-initdb.d/init.sql

# Crear el usuario de la aplicación y asignar permisos en la base de datos
echo "Connecting to SQL Server to create user and set permissions..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "USE BakeryDB; IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = '$APP_USER') BEGIN CREATE USER $APP_USER FOR LOGIN $APP_USER; ALTER ROLE db_owner ADD MEMBER $APP_USER; END;"
echo "SQL Server setup complete."

# Mantener el proceso en ejecución (espera a que SQL Server termine)
wait $SQLSERVERPID
