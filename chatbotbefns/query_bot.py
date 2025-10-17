import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from openai import OpenAI
from pinecone import Pinecone

# -----------------------
# Config
# -----------------------
INDEX_NAME = os.getenv("PC_INDEX", "gh-index")
PC_NAMESPACE = os.getenv("PC_NAMESPACE", "")  # leave blank if you’re not using namespaces
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # must match your index build
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")  # choose any model you prefer

# -----------------------
# App setup
# -----------------------
app = Flask(__name__)
CORS(app)
load_dotenv()

# -----------------------
# Clients
# -----------------------
openai_key = os.getenv("OPENAI_API_KEY")
pc_key = os.getenv("PINECONE_API_KEY")

if not openai_key:
    raise RuntimeError("OPENAI_API_KEY not set")
if not pc_key:
    raise RuntimeError("PINECONE_API_KEY not set")

client = OpenAI(api_key=openai_key)
pc = Pinecone(api_key=pc_key)
index = pc.Index(INDEX_NAME)

# -----------------------
# Helper functions
# -----------------------
def get_embedding(text: str) -> List[float]:
    """Get embedding for a given text using the same model as the index."""
    resp = client.embeddings.create(input=text, model=EMBED_MODEL)
    return resp.data[0].embedding

def _as_dict(match: Any) -> Dict[str, Any]:
    """Normalize Pinecone match (object or dict) to dict."""
    if isinstance(match, dict):
        return match
    return {
        "id": getattr(match, "id", None),
        "score": getattr(match, "score", None),
        "metadata": getattr(match, "metadata", {}) or {},
        "values": getattr(match, "values", None),
    }

def query_index(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Query Pinecone and return normalized matches."""
    vec = get_embedding(query)
    res = index.query(
        vector=vec,
        top_k=top_k,
        include_metadata=True,
        namespace=PC_NAMESPACE if PC_NAMESPACE else None,
    )
    matches = res.get("matches") if isinstance(res, dict) else getattr(res, "matches", [])
    return [_as_dict(m) for m in (matches or [])]

def build_prompt(user_question: str, matches: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Build a prompt for DK that includes both cottage-specific info and standard info.
    """
    if not matches:
        system = (
            "You are DK, a friendly and knowledgeable digital assistant for the holiday cottages. "
            "If no context is available, politely say you don’t have enough information and suggest contacting support."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Guest question: {user_question}"},
        ]

    # Create text blocks from retrieved cottages
    blocks = []
    for m in matches:
        meta = m.get("metadata") or {}
        title = meta.get("title", "Unknown Cottage")
        text = (meta.get("text") or "").strip()
        std = (meta.get("standard_info") or "").strip()

        block_lines = [f"### {title}"]
        if text:
            block_lines.append(text)
        if std:
            block_lines.append("\n" + std)
        blocks.append("\n".join(block_lines))

    context = "\n\n".join(blocks)

    system_msg = (
        "You are DK, a friendly and knowledgeable digital assistant for the holiday cottages. "
        "Answer guest questions using ONLY the context provided. "
        "If an answer isn't clearly supported by the context, say so and suggest contacting support. "
        "Prefer specific cottage details when present; otherwise include relevant standard information. "
        "Keep answers concise, polite, and actionable. "
        "Always refer to yourself as 'DK' when speaking in first person."
    )

    user_msg = f"""Context:
{context}

Guest question: {user_question}

Instructions:
- If multiple cottages are mentioned in the context, specify which cottage your facts come from.
- If the question is general (e.g., parking, Wi-Fi, check-in), include applicable standard information.
- Use bullet points for steps or lists.
- Begin your answer with: "Hi, DK here —" when appropriate.
"""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

# -----------------------
# Routes
# -----------------------
@app.route("/query", methods=["POST"])
def handle_query():
    data = request.json or {}
    user_question = data.get("question", "").strip()
    top_k = int(data.get("top_k", 5))

    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    try:
        matches = query_index(user_question, top_k=top_k)
        msgs = build_prompt(user_question, matches)

        chat = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=msgs,
            temperature=0.2,
        )

        answer = chat.choices[0].message.content.strip()
        debug_hits = [
            {
                "id": m.get("id"),
                "score": m.get("score"),
                "title": (m.get("metadata") or {}).get("title"),
            }
            for m in matches
        ]

        return jsonify({
            "response": answer,
            "retrieved": debug_hits,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
