import pyodbc

# Datos de conexión
driver = "{ODBC Driver 18 for SQL Server}"
server = "localhost"
database = "BakeryDB"
username = "appwhats"
password = "KSDF9jihd78fG3ND8"

# Cadena de conexión
connection_string = f"""
    DRIVER={driver};
    SERVER={server};
    DATABASE={database};
    UID={username};
    PWD={password};
    TrustServerCertificate=yes;  # Deshabilitar la verificación del certificado SSL
"""

try:
    # Establecer la conexión
    connection = pyodbc.connect(connection_string)
    print("Conexión exitosa a la base de datos")

    # Puedes realizar operaciones en la base de datos aquí, por ejemplo:
    cursor = connection.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"Versión de SQL Server: {row[0]}")

except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"Error de conexión a la base de datos: {ex}")

finally:
    # Cerrar la conexión
    if 'connection' in locals() and connection:
        connection.close()
        print("Conexión cerrada")