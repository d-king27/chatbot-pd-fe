# chatbot-pd-fe
front end for custom chat bot

---

## Chatbot Vector Index

A Python-based project that builds a vector index using Pinecone and OpenAI embeddings.

---

### 📦 Requirements

* Python 3.10+
* Git
* A [Pinecone](https://www.pinecone.io/) account
* An [OpenAI](https://platform.openai.com/) API key

---

### ⚙️ Setup Instructions

1. **Clone the repo**

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the project root**

   Your `.env` file should contain the following:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENV=your_pinecone_environment
   ```

   ⚠️ **Never commit your `.env` file to version control.** It's included in `.gitignore` by default.

5. **Run the build script**

   This script processes your data and pushes it to the Pinecone index:

   ```bash
   python build_index.py
   ```

---

### 🔐 Security

This project uses secret scanning and push protection. Don't commit secrets directly to the repo. If you accidentally do, rotate the keys immediately and follow GitHub's [push protection recovery guide](https://docs.github.com/en/code-security).

---

Let me know if you want to add Docker, Jupyter, Streamlit, or anything else and I’ll customize it further.
