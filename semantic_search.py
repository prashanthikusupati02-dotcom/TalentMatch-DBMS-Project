import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Connecting to MongoDB...")
client = MongoClient(os.getenv("MONGO_URI"))
collection = client["talentmatch_db"]["job_vectors"]

query = input("\nEnter the job you are looking for: ")

query_embedding = model.encode(query).tolist()

pipeline = [
    {
        "$vectorSearch": {
            "index": "job_vector_index",
            "path": "embedding",
            "queryVector": query_embedding,
            "numCandidates": 20,
            "limit": 5
        }
    },
    {
        "$project": {
            "_id": 0,
            "job_id": 1,
            "title": 1,
            "description": 1,
            "location": 1,
            "score": {"$meta": "vectorSearchScore"}
        }
    }
]

results = list(collection.aggregate(pipeline))

print("\nSemantic Job Search Results:")
for job in results:
    print("\nJob:", job["title"])
    print("Description:", job["description"])
    print("Location:", job["location"])
    print("Similarity Score:", round(job["score"], 4))

if not results:
    print("No matching jobs found.")

client.close()