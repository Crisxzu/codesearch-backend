from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import numpy as np

from ..core.config import ES_HOST, ES_INDEX, ES_API_KEY, MODEL_NAME

# Minimum similarity threshold (cosine similarity: -1 to 1)
# Results below this threshold are considered not relevant
MIN_SIMILARITY_THRESHOLD = 0.1  # Adjust this value based on your needs

def search(user_id: str, query_string: str, project_name: str = None, top_k: int = 5):
    """
    Performs a multi-tiered search for a specific user and optional project.
    Tries kNN first, then falls back to text.
    """
    print(f"Searching for user '{user_id}' in project '{project_name}' with query: '{query_string}'")

    es = Elasticsearch(ES_HOST, api_key=ES_API_KEY)
    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(query_string)

    # Build the base filter for user and project
    # Using 'term' for exact match on keyword fields
    filters = [{"term": {"user_id": user_id}}]
    if project_name:
        filters.append({"term": {"project_name": project_name}})
    bool_filter = {"bool": {"filter": filters}}

    response = None

    # --- STAGE 1: Get filtered documents and compute similarity manually ---
    try:
        print("Executing filtered search with manual similarity ranking...")
        # First, get all documents matching the filter (up to a reasonable limit)
        search_body = {
            "size": 100,  # Get more candidates to rank
            "_source": ["file_path", "code_content", "line_start", "line_end", "language", "user_id", "project_name", "code_embedding"],
            "query": bool_filter
        }
        
        response = es.search(
            index=ES_INDEX,
            body=search_body
        )
        
        # Compute similarity scores manually
        hits = response['hits']['hits']
        if hits:
            similarities = []
            for hit in hits:
                doc_embedding = np.array(hit['_source']['code_embedding'])
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append((hit, similarity))
            
            # Sort by similarity (descending) and take top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by minimum similarity threshold
            filtered_results = [(hit, score) for hit, score in similarities if score >= MIN_SIMILARITY_THRESHOLD]
            top_results = filtered_results[:top_k]
            
            # Reconstruct response with scored results
            response['hits']['hits'] = []
            for hit, score in top_results:
                hit['_score'] = float(score)
                # Remove embedding from source to reduce response size
                del hit['_source']['code_embedding']
                response['hits']['hits'].append(hit)
            
            response['hits']['total']['value'] = len(top_results)
            response['hits']['max_score'] = float(top_results[0][1]) if top_results else None
            
            print(f"Manual similarity search returned {len(top_results)} results (filtered by threshold {MIN_SIMILARITY_THRESHOLD})")
        else:
            print("No documents found matching the filter")
            
    except Exception as e:
        print(f"Filtered search failed: {e}")
        response = None

    # --- STAGE 2: If kNN failed, do a text-only search ---
    if response is None:
        try:
            print("Falling back to text-only search...")
            text_query = {
                "bool": {
                    "filter": filters,
                    "must": {
                        "multi_match": {
                            "query": query_string,
                            "fields": ["code_content", "function_name", "class_name"]
                        }
                    }
                }
            }
            response = es.search(
                index=ES_INDEX,
                query=text_query, # The 'query' parameter works for text-only search
                size=top_k,
                _source=["file_path", "code_content", "line_start", "line_end", "language"]
            )
        except Exception as fallback_e:
            print(f"All search attempts failed. Final error: {fallback_e}")
            return None

    return response