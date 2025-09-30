import os

def listar_archivos_relativos(ruta_base="."):
    """
    Recorre la carpeta actual y sus subcarpetas, mostrando los archivos con su ruta relativa.
    
    :param ruta_base: Ruta base (por defecto, el directorio actual)
    """
    print(f"Archivos en '{ruta_base}':\n")

    for root, _, files in os.walk(ruta_base):
        for file in files:
            ruta_relativa = os.path.relpath(os.path.join(root, file), ruta_base)
            print(ruta_relativa)

# Llamar a la función en la carpeta actual
listar_archivos_relativos()
