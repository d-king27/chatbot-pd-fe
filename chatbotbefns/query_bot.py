import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS  # Add CORS support if your frontend is separate

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Load API keys
load_dotenv()

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("gh-index")  # Connect to existing index

def get_embedding(text):
    """Get embedding for a given text using OpenAI"""
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def query_index(query, top_k=5):
    """Query Pinecone index with the given query"""
    query_embedding = get_embedding(query)
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return results['matches']

def build_prompt(user_question, results):
    """Build the prompt for ChatGPT based on query results"""
    context = "\n".join([f"- {match['metadata']['text']}" for match in results])
    return f"""You are a helpful assistant answering questions based on the product catalog below.

Catalog:
{context}

Question: {user_question}
Answer:"""

@app.route('/query', methods=['POST'])
def handle_query():
    """Handle incoming queries from the frontend"""
    data = request.json
    user_question = data.get('question')
    
    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        # Search Pinecone
        results = query_index(user_question)

        # Build prompt for GPT
        prompt = build_prompt(user_question, results)

        # Get response from ChatGPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Consider gpt-4-turbo for better quality
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify({
            "response": response.choices[0].message.content,
            "relevant_products": [match['metadata'] for match in results]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)