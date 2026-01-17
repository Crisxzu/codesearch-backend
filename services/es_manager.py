from elasticsearch import Elasticsearch
from ..core.config import ES_HOST, ES_INDEX, ES_API_KEY

def get_es_client():
    return Elasticsearch(ES_HOST, api_key=ES_API_KEY)

def clean_index(user_id: str = None, project_name: str = None, delete_all: bool = False):
    """
    Cleans the Elasticsearch index.
    - If delete_all is True, the entire index is deleted (admin operation).
    - If user_id and project_name are provided, documents for that project are deleted.
    - if only user_id is provided, all documents for that user are deleted.
    """
    es = get_es_client()

    if delete_all:
        if es.indices.exists(index=ES_INDEX):
            es.indices.delete(index=ES_INDEX)
            return {"status": "success", "message": f"Index '{ES_INDEX}' deleted."}
        return {"status": "success", "message": "Index did not exist."}

    if not user_id:
        raise ValueError("user_id must be provided for project or user-specific cleaning.")

    filters = [{"term": {"user_id": user_id}}]
    if project_name:
        filters.append({"term": {"project_name": project_name}})
        msg_scope = f"project '{project_name}' for user '{user_id}'"
    else:
        msg_scope = f"user '{user_id}'"

    
    response = es.delete_by_query(
        index=ES_INDEX,
        body={"query": {"bool": {"filter": filters}}},
        refresh=True
    )
    
    deleted_count = response.get('deleted', 0)
    if deleted_count > 0:
        return {"status": "success", "message": f"Successfully deleted {deleted_count} documents for {msg_scope}."}
    
    return {"status": "success", "message": f"No documents found for {msg_scope}."}

def get_all_documents():
    """
    Retrieves all documents from the index for debugging.
    """
    es = get_es_client()
    if not es.indices.exists(index=ES_INDEX):
        return {"error": "Index does not exist."}
    
    return es.search(index=ES_INDEX, body={"query": {"match_all": {}}}, size=100)


