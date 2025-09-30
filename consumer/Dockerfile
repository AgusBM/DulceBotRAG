FROM python:3.11-slim-buster AS builder

WORKDIR /app

# Instala las dependencias del sistema necesarias para pyodbc
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    unixodbc-dev \
    odbcinst \
    unixodbc \
    locales \
    curl \
    gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Configura el driver de MSSQL (opcional, solo si usas SQL Server)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/10/prod buster main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql17 \
    mssql-tools \
    && rm -rf /var/lib/apt/lists/*

# Establece el locale
RUN sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

#Crea un entorno virtual
RUN python -m venv /app/venv

# Activa el entorno virtual
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copia requirements.txt
COPY consumer/requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crea el directorio para la aplicación
RUN mkdir /app/src

# Copia los archivos de la aplicación
COPY consumer/whatsapp_consumer.py /app/src
COPY classifier_agent.py /app/src
COPY backery_agents_rag.py /app/src
COPY config.py /app/src
 
# Copia el directorio "agents" (que contiene los archivos Markdown)
COPY agents /app/src/agents 

# Etapa Final
FROM python:3.11-slim-buster

# Copia las dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    locales \
    curl \
    gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Configura el driver de MSSQL en la imagen final
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/10/prod buster main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copia el entorno virtual desde la etapa builder
COPY --from=builder /app/venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copia el resto desde builder
COPY --from=builder /app/src /app/src

# Establece el locale
RUN sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV PATH "$PATH:/opt/mssql-tools/bin"

# verificar que pyodbc está instalado después de la instalación y antes de ejecutar la aplicación principal
RUN python -c "import pyodbc; print(pyodbc.version)"
WORKDIR /app/src

#CMD ["python", "whatsapp_consumer.py"] #Comentamos la ejecucion del script

CMD ["sh"] 
#iniciamos bash en vez de ejecutar el script