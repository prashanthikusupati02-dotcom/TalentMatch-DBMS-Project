
import os
import mysql.connector
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# Load the embedding model
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to MySQL
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="job_app_user",
    password=os.getenv("MYSQL_PASSWORD"),
    database="job_matching_db"
)

cursor = mysql_conn.cursor(dictionary=True)

# Connect to MongoDB Atlas
mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client["talentmatch_db"]
collection = mongo_db["job_vectors"]

# Fetch jobs from MySQL
cursor.execute("""
    SELECT job_id, title, description,
           required_experience, location
    FROM job
""")

jobs = cursor.fetchall()

print(f"Found {len(jobs)} jobs.")

# Generate embeddings and store them in MongoDB
for job in jobs:
    text = (
        f"Job title: {job['title']}. "
        f"Description: {job['description'] or ''}. "
        f"Required experience: {job['required_experience']} years. "
        f"Location: {job['location'] or ''}."
    )

    embedding = model.encode(text).tolist()

    document = {
        "job_id": job["job_id"],
        "title": job["title"],
        "description": job["description"],
        "required_experience": float(job["required_experience"]),
        "location": job["location"],
        "embedding": embedding
    }

    collection.update_one(
        {"job_id": job["job_id"]},
        {"$set": document},
        upsert=True
    )

    print(f"Stored embedding for: {job['title']}")

cursor.close()
mysql_conn.close()
mongo_client.close()

print("All job embeddings generated and stored successfully!")
