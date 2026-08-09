from app_data.ingestion import collection
import asyncio

def retrieve(query , k_closest = 5):
    results = collection.query(query_texts=[query] , n_results=k_closest)
    return results['documents'][0]

async def retrieve_async(query: str):
    return await asyncio.to_thread(retrieve, query)