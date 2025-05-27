import os
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "chatbot-pd"
cloud = "aws"
region = os.getenv("PINECONE_ENV")

if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region)
    )

index = pc.Index(name=index_name)

df = pd.read_csv("sheet1.csv")
df['text'] = df.apply(
    lambda row: f"{row['Product Name']} ({row['Category']}): ${row['Price']} - {row['Description']}", axis=1
)

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

for _, row in tqdm(df.iterrows(), total=len(df)):
    embedding = get_embedding(row['text'])
    metadata = {"text": row['text'], "product_id": str(row['Product ID'])}
    index.upsert([(str(row['Product ID']), embedding, metadata)])

print("✅ Indexing complete.")
