import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load API keys
load_dotenv()

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("gh-index")  # Ensure this matches your indexing script

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
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results['matches']

def build_prompt(user_question, matches):
    """Build a prompt using retrieved cottage metadata"""
    context_entries = []
    for match in matches:
        metadata = match['metadata']
        title = metadata.get("title", "Unknown Cottage")
        context_lines = [f"🏡 {title}"]
        for k, v in metadata.items():
            if k not in {"title", "text", "standard_info"} and v:
                pretty_key = k.replace("_", " ").capitalize()
                context_lines.append(f"- {pretty_key}: {v}")
        context_entries.append("\n".join(context_lines))
    
    context = "\n\n".join(context_entries)

    return f"""You are a helpful assistant answering guest questions based on details from rental cottages.

Cottage Listings:
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

        # Build GPT prompt
        prompt = build_prompt(user_question, results)

        # Ask OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Upgrade to gpt-4-turbo for production
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify({
            "response": response.choices[0].message.content.strip()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
