# classifier_agent.py
import requests
import os
import numpy as np
import yaml
import re
from pathlib import Path
# --- Auto-descubrimiento de ficheros por extensión ---
BASE_DIR = Path(__file__).resolve().parent

def list_files_recursive(*folders, exts=(".md", ".json")):
    """Devuelve rutas (str) únicas y ordenadas de todos los ficheros con las extensiones indicadas, recursivo."""
    paths = []
    for folder in folders:
        root = (BASE_DIR / folder).resolve()
        if root.exists():
            for ext in exts:
                paths.extend(str(p) for p in root.rglob(f"*{ext}"))
    return sorted(set(paths))

class ClassifierAgent:
    def __init__(self, endpoint_url, api_key=None, embedding_model_id="benevolencemessiah/text-embedding-nomic-embed-text-v1.5"): #Added default embedding model
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.embedding_model_id = embedding_model_id #set the embedding model
        # Después: autodiscovery en las carpetas indicadas
        order_paths = list_files_recursive("agent/classifier/order", exts=(".md", ".json"))
        support_paths = list_files_recursive("agent/classifier/support", exts=(".md", ".json"))
        self.order_docs_embeddings = self._load_and_embed_docs(order_paths)
        self.support_docs_embeddings = self._load_and_embed_docs(support_paths)
    def _load_and_embed_docs(self, paths):
        """Loads and embeds documents from the given paths."""
        documents = self._load_documents(paths)
        embeddings = []
        for doc in documents:
            embedding = self.get_embedding(doc["text"])
            if embedding is not None:
                embeddings.append(embedding)
        return embeddings

    def _load_documents(self, paths):
        """Loads documents from Markdown files, preserving content and YAML metadata."""
        docs = []
        for path in paths:
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    metadata_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
                    metadata = {}
                    if metadata_match:
                        metadata = yaml.safe_load(metadata_match.group(1))
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

    def get_embedding(self, text):
        """Calls the LM Studio /api/v0/embeddings endpoint to generate the embedding for the text."""
        url = f"{self.endpoint_url}/api/v0/embeddings"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.embedding_model_id,
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
        """Calculates the cosine similarity between two vectors."""
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def classify(self, query):
        """Classifies the query by comparing it to the embeddings of the documents of each agent."""
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return None

        # Calculate similarity for each document in the "order" category
        order_sims = [self.cosine_similarity(query_embedding, emb) for emb in self.order_docs_embeddings]
        # Calculate similarity for each document in the "support" category
        support_sims = [self.cosine_similarity(query_embedding, emb) for emb in self.support_docs_embeddings]

        order_score = np.max(order_sims) if order_sims else 0.0
        support_score = (np.max(support_sims) if support_sims else 0.0)-0.14
        # Imprime en consola la puntuación del documento, junto con su categoría (si la hubiera)
        print("Similitudes con documentos de Order:")
        for i, sim in enumerate(order_sims):
            print(f"  Documento {i+1}: {sim:.4f}")

        print("Similitudes con documentos de Support:")
        for i, sim in enumerate(support_sims):
            print(f"  Documento {i+1}: {sim:.4f}")

        print(f"Puntuación Order: {order_score:.4f} | Puntuación Support: {support_score:.4f}")

        # Retornar la categoría con mayor puntuación
        return "order" if order_score >= (support_score) else "support"

    def route_query(self, query):
        """
        Clasifica la consulta y la reenvía al agente correspondiente.
        """
        category = self.classify(query)
        if category is None:
            return "Error en la clasificación de la consulta."
        return category
