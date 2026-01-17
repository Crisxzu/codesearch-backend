import os

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from tree_sitter import Parser
from tree_sitter_languages import get_language

from ..core.config import ES_HOST, ES_INDEX, ES_API_KEY, MODEL_NAME
from .vision_service import VisionService
from .document_service import DocumentService

CHUNK_SIZE = 20
SUPPORTED_CODE_LANGUAGES = {
    ".py": "python",
}

SUPPORTED_IMAGE_FORMATS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'
}


class IndexingService:
    def __init__(self):
        print("Initializing IndexingService...")
        self.es = Elasticsearch(ES_HOST, api_key=ES_API_KEY)
        self.model = SentenceTransformer(MODEL_NAME)
        self.vision_service = None  # Lazy init
        self.document_service = DocumentService()
        self.parser = Parser()
        self._create_index_if_not_exists()
        print("IndexingService initialized.")

    def _create_index_if_not_exists(self):
        if not self.es.indices.exists(index=ES_INDEX):
            print(f"Creating index '{ES_INDEX}'...")
            self.es.indices.create(
                index=ES_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "user_id": {"type": "keyword"},
                            "project_name": {"type": "keyword"},
                            "file_path": {"type": "keyword"},
                            "content_type": {"type": "keyword"},  # code, image, document
                            "language": {"type": "keyword"},
                            "class_name": {"type": "keyword"},
                            "function_name": {"type": "keyword"},
                            "code_content": {"type": "text"},
                            "code_embedding": {
                                "type": "dense_vector",
                                "dims": 384
                            },
                            "line_start": {"type": "integer"},
                            "line_end": {"type": "integer"},
                        }
                    }
                }
            )
            print("Index created.")
    
    def recreate_index(self):
        """Delete and recreate the index with proper mappings"""
        if self.es.indices.exists(index=ES_INDEX):
            print(f"Deleting existing index '{ES_INDEX}'...")
            self.es.indices.delete(index=ES_INDEX)
            print("Index deleted.")
        self._create_index_if_not_exists()

    def _get_ast_nodes(self, tree, lang_object):
        if lang_object.name != "python":
            return []

        query_string = """
        (class_definition) @class
        (function_definition) @function
        """
        query = lang_object.query(query_string)
        captures = query.captures(tree.root_node)

        nodes = []
        for node, capture_name in captures:
            node_type = "class" if capture_name == "class" else "function"
            
            name_node = node.child_by_field_name('name')
            name = name_node.text.decode('utf8') if name_node else "Unnamed"
            
            nodes.append({
                "name": name,
                "type": node_type,
                "content": node.text.decode('utf8'),
                "start_line": node.start_point[0],
                "end_line": node.end_point[0]
            })
        return nodes

    def index_file_content(self, user_id: str, project_name: str, file_path: str, file_content: str):
        """
        Parses, chunks, embeds, and indexes a single file's content.
        Removes existing entries for this file before indexing to avoid duplicates.
        """
        print(f"Indexing file for user '{user_id}', project '{project_name}': {file_path}")
        
        # Remove existing entries for this specific file/user/project combination
        self.remove_file_from_index(user_id, project_name, file_path)
        
        _, ext = os.path.splitext(file_path)
        lang_name = SUPPORTED_CODE_LANGUAGES.get(ext)
        if not lang_name:
            return

        lang_object = get_language(lang_name)
        self.parser.set_language(lang_object)

        try:
            file_content_bytes = file_content.encode('utf-8')
            tree = self.parser.parse(file_content_bytes)
            nodes = self._get_ast_nodes(tree, lang_object)

            for node in nodes:
                lines = node['content'].splitlines()
                for i in range(0, len(lines), CHUNK_SIZE):
                    chunk_lines = lines[i:i + CHUNK_SIZE]
                    chunk_content = "\n".join(chunk_lines)
                    
                    if not chunk_content.strip():
                        continue

                    embedding = self.model.encode(chunk_content)
                    
                    doc = {
                        "user_id": user_id,
                        "project_name": project_name,
                        "file_path": file_path,
                        "content_type": "code",
                        "language": lang_name,
                        "class_name": node['name'] if node['type'] == 'class' else None,
                        "function_name": node['name'] if node['type'] == 'function' else None,
                        "code_content": chunk_content,
                        "code_embedding": embedding.tolist(),
                        "line_start": node['start_line'] + i,
                        "line_end": node['start_line'] + i + len(chunk_lines) - 1,
                    }
                    
                    self.es.index(index=ES_INDEX, document=doc, refresh=True)
            print(f"Successfully indexed {len(nodes)} nodes from {file_path}")

        except Exception as e:
            print(f"Failed to index {file_path}: {e}")

    def remove_file_from_index(self, user_id: str, project_name: str, file_path: str):
        """Remove all entries for a specific file/user/project combination"""
        print(f"Removing existing entries for user '{user_id}', project '{project_name}', file: {file_path}")
        self.es.delete_by_query(
            index=ES_INDEX,
            body={
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"user_id": user_id}},
                            {"term": {"project_name": project_name}},
                            {"term": {"file_path": file_path}}
                        ]
                    }
                }
            },
            refresh=True
        )
    
    def index_image(self, user_id: str, project_name: str, file_path: str, image_bytes: bytes):
        """
        Index an image by generating a description using vision AI,
        then creating an embedding of the description.
        """
        print(f"Indexing image for user '{user_id}', project '{project_name}': {file_path}")
        
        # Remove existing entries
        self.remove_file_from_index(user_id, project_name, file_path)
        
        # Lazy init vision service
        if self.vision_service is None:
            self.vision_service = VisionService()
        
        try:
            # Generate description using vision AI
            description = self.vision_service.describe_image(image_bytes)
            
            # Generate embedding from description
            embedding = self.model.encode(description)
            
            # Index the image with its description
            doc = {
                "user_id": user_id,
                "project_name": project_name,
                "file_path": file_path,
                "content_type": "image",
                "language": None,
                "class_name": None,
                "function_name": None,
                "code_content": description,  # Store description as searchable content
                "code_embedding": embedding.tolist(),
                "line_start": None,
                "line_end": None,
            }
            
            self.es.index(index=ES_INDEX, document=doc, refresh=True)
            print(f"Successfully indexed image: {file_path}")
            
        except Exception as e:
            print(f"Failed to index image {file_path}: {e}")
            raise
    
    def index_document(self, user_id: str, project_name: str, file_path: str, file_bytes: bytes):
        """
        Index a document (PDF, DOCX, etc.) by extracting text,
        chunking it, and creating embeddings.
        """
        print(f"Indexing document for user '{user_id}', project '{project_name}': {file_path}")
        
        # Remove existing entries
        self.remove_file_from_index(user_id, project_name, file_path)
        
        try:
            # Extract text from document
            text_content = self.document_service.extract_text(file_path, file_bytes)
            
            if not text_content.strip():
                print(f"No text content extracted from {file_path}")
                return
            
            # Split into chunks (similar to code chunking)
            lines = text_content.split('\n')
            chunk_count = 0
            
            for i in range(0, len(lines), CHUNK_SIZE):
                chunk_lines = lines[i:i + CHUNK_SIZE]
                chunk_content = "\n".join(chunk_lines)
                
                if not chunk_content.strip():
                    continue
                
                # Generate embedding
                embedding = self.model.encode(chunk_content)
                
                doc = {
                    "user_id": user_id,
                    "project_name": project_name,
                    "file_path": file_path,
                    "content_type": "document",
                    "language": None,
                    "class_name": None,
                    "function_name": None,
                    "code_content": chunk_content,
                    "code_embedding": embedding.tolist(),
                    "line_start": i,
                    "line_end": i + len(chunk_lines) - 1,
                }
                
                self.es.index(index=ES_INDEX, document=doc, refresh=True)
                chunk_count += 1
            
            print(f"Successfully indexed document {file_path} ({chunk_count} chunks)")
            
        except Exception as e:
            print(f"Failed to index document {file_path}: {e}")
            raise
    
    def index_file(self, user_id: str, project_name: str, file_path: str, file_bytes: bytes):
        """
        Smart indexing that detects file type and routes to appropriate handler.
        
        Args:
            user_id: User ID
            project_name: Project name
            file_path: File path/name
            file_bytes: Raw file bytes
        """
        _, ext = os.path.splitext(file_path.lower())
        
        # Check if it's an image
        if ext in SUPPORTED_IMAGE_FORMATS:
            return self.index_image(user_id, project_name, file_path, file_bytes)
        
        # Check if it's a document
        if DocumentService.is_supported(file_path):
            return self.index_document(user_id, project_name, file_path, file_bytes)
        
        # Check if it's code
        if ext in SUPPORTED_CODE_LANGUAGES:
            file_content = file_bytes.decode('utf-8', errors='ignore')
            return self.index_file_content(user_id, project_name, file_path, file_content)
        
        # Unsupported type
        print(f"Unsupported file type for {file_path}: {ext}")
        raise ValueError(f"Unsupported file type: {ext}")
