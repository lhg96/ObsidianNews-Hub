import chromadb
import os

print("Current working directory:", os.getcwd())

try:
    client = chromadb.PersistentClient(path="./chroma_db")
    print("ChromaDB client created successfully")

    collection = client.create_collection("test_collection")
    print("Collection created successfully")

    collection.add(
        documents=["This is a test document"],
        metadatas=[{"source": "test"}],
        ids=["test1"]
    )
    print("Document added successfully")

    results = collection.query(query_texts=["test"], n_results=1)
    print("Query results:", results)

except Exception as e:
    print(f"An error occurred: {e}")

print("Script completed")
