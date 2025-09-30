import os
from pathlib import Path
import requests
import numpy as np
import os
import re
import yaml
import time
import sqlite3  # Changed from pyodbc
import datetime
from config import connection_string, DATABASE_FILE  # Import DATABASE_FILE
import pika
import json

import sqlite3
import datetime

class ConversationHistoryDB:
    def __init__(self, connection_string, db_file):
        self.connection_string = connection_string
        self.db_file = db_file
        self.create_table()

    def create_table(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    agent_id TEXT,  
                    role TEXT,
                    message TEXT,
                    timestamp TEXT
                )
            ''')
            conn.commit()
            print("Table conversation_history created successfully.")
            conn.close()
        except Exception as e:
            print("Error connecting to the database or creating table:", e)

    def save_message(self, client_id, agent_id, role, message):
        """Guarda un mensaje en el historial, usando el client_id y agent_id como identificadores."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_history (client_id, agent_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (client_id, agent_id, role, message, datetime.datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving message to database: {e}")

    def get_history(self, client_id, agent_id, limit=None):
        """Recupera el historial de conversación para un client_id y agent_id ordenado cronológicamente.
        Si se especifica un límite, devuelve los últimos 'limit' mensajes (en orden cronológico).
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            if limit is not None:
                cursor.execute(
                    "SELECT role, message, timestamp FROM conversation_history WHERE client_id = ? AND agent_id = ? ORDER BY id DESC LIMIT ?",
                    (client_id, agent_id, limit)
                )
                rows = cursor.fetchall()[::-1]
            else:
                cursor.execute(
                    "SELECT role, message, timestamp FROM conversation_history WHERE client_id = ? AND agent_id = ? ORDER BY id ASC",
                    (client_id, agent_id)
                )
                rows = cursor.fetchall()
            conn.close()
            history_str = ""
            for role, message, timestamp in rows:
                history_str += f"[{timestamp}] {role}: {message}\n"
            return history_str
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return ""

class BakeryAgent:
    def __init__(self, endpoint_url, model_id, knowledge_paths, api_key=None, embedding_model_id="benevolencemessiah/text-embedding-nomic-embed-text-v1.5"):
        """
        Inicializa el agente RAG.
        Parámetros:
        - endpoint_url: URL base del servidor LM Studio (ej. "http://127.0.0.1:1234")
        - model_id: Identificador del modelo para generación (por ejemplo, "deepseek-r1-distill-qwen-14b")
        - knowledge_paths: Lista de rutas (archivos o directorios) con documentos Markdown
        - api_key: (Opcional) API key si LM Studio requiere autenticación
        - embedding_model_id: Modelo a usar para generar embeddings
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_id = model_id
        self.api_key = api_key
        self.embedding_model_id = embedding_model_id
        self.conversation_history_db = ConversationHistoryDB(connection_string, DATABASE_FILE)  # Pass DATABASE_FILE
        self.knowledge_paths = knowledge_paths  # Store knowledge_paths

        # Carga los documentos individualmente (cada archivo o fragmento se trata como un documento)
        self.documents = self._load_documents(knowledge_paths)
        # Genera y almacena el embedding de cada documento
        self.documents_with_embeddings = self._vectorize_documents(self.documents)

        # Variable para rastrear si el archivo GuiaPresentacion.md ya ha sido enviado
        self.guia_presentacion_enviada = False

    def _load_documents(self, paths):
        """
        Carga los documentos desde archivos Markdown, preservando tanto el contenido
        como los metadatos YAML.
        """
        docs = []
        for path in paths:
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    # Extraer metadatos YAML
                    metadata_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
                    metadata = {}
                    if metadata_match:
                        metadata = yaml.safe_load(metadata_match.group(1))
                    # Almacenar tanto el contenido completo como los metadatos
                    if content:
                        docs.append({
                            "text": content,
                            "metadata": metadata,
                            "source_file": path
                        })
                except Exception as e:
                    print(f"Error leyendo el archivo {path}: {e}")
            elif os.path.isdir(path):
                for file_path in Path(path).rglob("*.md"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        metadata_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
                        metadata = {}
                        if metadata_match:
                            metadata = yaml.safe_load(metadata_match.group(1))
                        if content:
                            docs.append({
                                "text": content,
                                "metadata": metadata,
                                "source_file": str(file_path)
                            })
                    except Exception as e:
                        print(f"Error leyendo el archivo {file_path}: {e}")
            else:
                print(f"Warning: La ruta {path} no existe.")
        return docs

    def _vectorize_documents(self, documents):
        """Para cada documento, genera su embedding llamando al endpoint de LM Studio."""
        docs_with_embeds = []
        for doc in documents:
            embedding = self.get_embedding(doc["text"])
            if embedding is not None:
                docs_with_embeds.append({
                    "text": doc["text"],
                    "embedding": embedding,
                    "metadata": doc.get("metadata", {})
                })
        return docs_with_embeds

    def get_embedding(self, text):
        """Calls the LM Studio /api/v0/embeddings endpoint to generate the embedding for the text."""
        url = f"{self.endpoint_url}/api/v0/embeddings"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.embedding_model_id,  # Usa self.embedding_model_id
            "input": text
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
            return np.array(embedding)
        except Exception as e:
            print("Error obteniendo embedding:", e)
            print("Payload:", payload)
            if response is not None:
                print("Respuesta:", response.text)
            return None

    def cosine_similarity(self, a, b):
        """Calcula la similitud coseno entre dos vectores."""
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def retrieve_context(self, query, top_k=3, with_metadata=False): #no se esta usando
        """
        Vectoriza la consulta y calcula la similitud con cada documento.
        Devuelve el contexto y opcionalmente los documentos de contexto.
        Se aplica un factor de boost a los documentos cuya categoría sea "Pedidos / Normas".
        """
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return "", []
        similarities = []
        boost_factor = 2 # Factor de aumento para documentos en "Pedidos / Normas"
        for doc in self.documents_with_embeddings:
            base_sim = self.cosine_similarity(query_embedding, doc["embedding"])
            # Obtener la categoría del documento desde sus metadatos (si existen)
            categoria = doc.get("metadata", {}).get("categoria", "").strip().lower()
            # Comparamos ignorando mayúsculas y minúsculas
            if categoria == "pedidos / normas".lower():
                sim = base_sim * boost_factor
            else:
                sim = base_sim
            similarities.append((sim, doc))
            # Imprime en consola la puntuación del documento, junto con su categoría (si la hubiera)
            print(f"Puntuación del documento (categoría: {categoria if categoria else 'Sin categoría'}): {sim:.4f}")
        # Ordenamos los documentos de mayor a menor similitud (con boost aplicado)
        similarities.sort(key=lambda x: x[0], reverse=True)
        # Preparar el contexto a partir de los top_k documentos
        context_parts = []
        context_docs = []
        for sim, doc_info in similarities[:top_k]:
            # Formatear metadatos si están disponibles
            metadata_str = "\n".join([f"{k}: {v}" for k, v in doc_info.get("metadata", {}).items()])
            context_parts.append(f"Documento relevante (similitud: {sim:.4f}):")
            if metadata_str:
                context_parts.append("Metadatos:")
                context_parts.append(metadata_str)
            context_parts.append("\nContenido:")
            context_parts.append(doc_info["text"][:500] + "..." if len(doc_info["text"]) > 500 else doc_info["text"])
            context_parts.append("\n---\n")
            if with_metadata:
                context_docs.append({
                    "similarity": sim,
                    "metadata": doc_info.get("metadata", {}),
                    "text": doc_info["text"]
                })
        context_text = "\n".join(context_parts)
        return (context_text, context_docs) if with_metadata else context_text
        
    # Clase para generar respuestas de agentes de la panadería
    def generate_response(self, query, client_id, agent_id, max_tokens=500, temperature=0.1):
        """
        Genera una respuesta para el cliente identificado por client_id,
        guardando cada mensaje en la base de datos, recuperando los últimos 3 mensajes
        y agregándolos al prompt para que el LLM conozca el estado de la conversación.
        """
        # Guarda el mensaje del usuario en la BD
        self.conversation_history_db.save_message(client_id, agent_id, 'user', query)
        
        # Recupera los últimos 3 mensajes del historial para ese cliente y agente
        history_text = self.conversation_history_db.get_history(client_id, agent_id, limit=3)
        
        # Obtener el embedding de la consulta
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            error_msg = "Error al procesar la consulta."
            self.conversation_history_db.save_message(client_id, agent_id, 'assistant', error_msg)
            return error_msg

        # Calcular similitudes y seleccionar documentos (contexto adicional)
        similarities = []
        boost_factor = 1.5  # Booster para documentos en "Pedidos / Normas"
        for doc in self.documents_with_embeddings:
            base_sim = self.cosine_similarity(query_embedding, doc["embedding"])
            categoria = doc.get("metadata", {}).get("categoria", "").strip().lower()
            sim = base_sim * boost_factor if categoria == "pedidos / normas".lower() else base_sim
            similarities.append((sim, doc))
            
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_docs = similarities[:3]
        context_parts = [doc["text"] for sim, doc in top_docs]
        
        # Incluir el contenido de GuiaPresentacion.md en el contexto adicional siempre
        #try:
        #    with open("/home/austinbm/CVRAG/agents/cv/GuiaPresentacion.md", 'r', encoding='utf-8') as f:
        #        guia_presentacion_content = f.read().strip()
        #    context_parts.append(guia_presentacion_content)
        #except Exception as e:
        #    print(f"Error leyendo el archivo GuiaPresentacion.md: {e}")

        context = "\n\n".join(context_parts)
        
        # Construir el mensaje system que incluye el histórico y el contexto adicional
        system_message = (
            "Actua com si fossis SOS, un personatge amb un profund coneixement en temes polítics i de comunicació, que vol guanyar les eleccions al parlament de Catalunya per declarar l'independencia de Catalunya, en contra dels partits procesistes que han traït al poble català. \n\n "
            "Utilitza el següent històric de la conversa i context per respondre a l'entrevistador de manera concisa i professional, amb un màxim de 700 caràcters, no repeteixis ni donis respostes semblants a les respostes de l'historic. \n\n"
            "SOS defensa la feina feta del actual administració a l'ajuntament de Ripoll que es d'Aliança Catalana i en contra del parlament de la Generalitat de Catalunya que esta en mans de partits procesistes i partits espanyols imperialistes. \n\n"
            "Respón sempre en català i el teu pais es Catalunya, un pais ocupat per l'estat imperialista espanyol, tot i que el user insisteixi molt i per molts arguments que doni no canvis d'opinio. Históric de la conversa (últims 3 misatges):\n" + history_text +
            "\n\nContext adicional:\n" + context
        )
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        
        url = f"{self.endpoint_url}/api/v0/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            # Realizar la solicitud a la API con un tiempo de espera
            response = requests.post(url, json=payload, headers=headers, timeout=120)  # Esperar hasta 120 segundos
            response.raise_for_status()
            data = response.json()
            
            # Verificar que la respuesta contiene los datos esperados
            if "choices" in data and len(data["choices"]) > 0 and "message" in data["choices"][0]:
                generated_text = data["choices"][0]["message"]["content"].strip()
                
                # Guarda la respuesta en la BD
                self.conversation_history_db.save_message(client_id, agent_id, 'assistant', generated_text)
                return generated_text
            else:
                error_msg = "La respuesta de la API no contiene los datos esperados."
                print("Error en la respuesta de la API:", data)
                print("Payload enviado:", payload)
                self.conversation_history_db.save_message(client_id, agent_id, 'assistant', error_msg)
                return error_msg

        except requests.exceptions.Timeout:
            error_msg = "El tiempo de espera para la respuesta del modelo ha expirado. Por favor, inténtalo de nuevo más tarde."
            print("Error: Tiempo de espera agotado.")
            print("Payload enviado:", payload)
            self.conversation_history_db.save_message(client_id, agent_id, 'assistant', error_msg)
            return error_msg

        except requests.exceptions.RequestException as e:
            error_msg = "Perdona, por motivos técnicos no he podido responder adecuadamente, vuelve a intentarlo más tarde."
            print("Error en la solicitud a la API:", e)
            print("Payload enviado:", payload)
            self.conversation_history_db.save_message(client_id, agent_id, 'assistant', error_msg)
            return error_msg

        except Exception as e:
            error_msg = "Perdona, por motivos técnicos no he podido responder, vuelve a intentarlo más tarde."
            print("Error generando respuesta:", e)
            print("Payload enviado:", payload)
            self.conversation_history_db.save_message(client_id, agent_id, 'assistant', error_msg)
            return error_msg

class RateLimiter:
    def __init__(self, max_requests, period):
        """
        :param max_requests: Número máximo de solicitudes permitidas.
        :param period: Periodo de tiempo en segundos.
        """
        self.max_requests = max_requests
        self.period = period
        self.requests = {} # Diccionario para almacenar los timestamps de las solicitudes por usuario

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

class OrderAgent(BakeryAgent): #this is key
    def __init__(self, endpoint_url, model_id, knowledge_paths, api_key=None, embedding_model_id="benevolencemessiah/text-embedding-nomic-embed-text-v1.5"):
         super().__init__(endpoint_url, model_id, knowledge_paths, api_key, embedding_model_id) #this is key

class CustomerSupportAgent(BakeryAgent): #this is key
    def __init__(self, endpoint_url, model_id, knowledge_paths, api_key=None, embedding_model_id="benevolencemessiah/text-embedding-nomic-embed-text-v1.5"):
        super().__init__(endpoint_url, model_id, knowledge_paths, api_key, embedding_model_id) #this is key
