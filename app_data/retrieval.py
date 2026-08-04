from app_data.ingestion import collection

def retrieve(query , k_closest = 3):
    results = collection.query(query_texts=[query] , n_results=k_closest)
    return results['documents'][0]


    