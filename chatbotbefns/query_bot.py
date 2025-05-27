import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load API keys
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Connect to the existing index
index = pc.Index("chatbot-pd")

# Function to get an embedding from a query
def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# Function to query Pinecone
def query_index(query, top_k=5):
    query_embedding = get_embedding(query)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return results['matches']

# Function to build the ChatGPT prompt
def build_prompt(user_question, results):
    context = "\n".join([f"- {match['metadata']['text']}" for match in results])
    prompt = f"""You are a helpful assistant answering questions based on the product catalog below.

Catalog:
{context}

Question: {user_question}
Answer:"""
    return prompt

# Ask the user for a question
user_question = input("Ask your question: ")

# Search Pinecone
results = query_index(user_question)

# Build prompt for GPT
prompt = build_prompt(user_question, results)

# Get response from ChatGPT
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

# Display the result
print("\n💬 Chatbot Response:\n")
print(response.choices[0].message.content)
