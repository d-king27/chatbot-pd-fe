import os
import re
import docx
from dotenv import load_dotenv
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone client (v3+ compatible)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Set index name and region (make sure PINECONE_ENV is your region like "us-west-2")
index_name = "gh-index"
pinecone_env = os.getenv("PINECONE_ENV")

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  # Change to "gcp" if needed
            region=pinecone_env
        )
    )

# Connect to the index
index = pc.Index(index_name)

# === Utility Functions ===

def read_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])

def format_standard_info(raw_text):
    text = raw_text.replace("\r", "").strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    formatted_lines = ["#### 🏠 General Information for All Cottages\n"]
    for line in lines:
        if re.match(r"^[A-Z][\w\s]+[:\-]?\s*\d", line):
            line = re.sub(r"[:\-]?\s+", ": ", line, count=1)
            formatted_lines.append(f"- **{line}**")
        elif re.match(r"^(Travel Cot|Highchair|Hairdryer|Iron|Non smoking|.*provided|.*included|.*not provided)", line, re.IGNORECASE):
            formatted_lines.append(f"- {line}")
        else:
            formatted_lines.append(f"- {line}")
    return "\n".join(formatted_lines)

def extract_cottages_info(text):
    entries = re.split(r'\n(?=[A-Z][a-z]+\s(?:Cottage|House|Flat|View|Mews|Fold|Firs|Bakestones|Holmdale|Treacle|Acer))', text)
    data = []
    for entry in entries:
        lines = entry.strip().split("\n")
        if lines:
            title = lines[0].strip()
            body = " ".join(lines[1:]).strip()
            if title and body:
                data.append({"title": title, "text": body})
    return data

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# === Process Documents ===

specific_text = read_docx("Cottage_Specific_Information.docx")
raw_standard_text = read_docx("Information_Standard_Cottages.docx")
formatted_standard_text = format_standard_info(raw_standard_text)

cottages = extract_cottages_info(specific_text)

for cottage in cottages:
    cottage["text"] += "\n\nStandard Info:\n" + formatted_standard_text

# === Index into Pinecone ===

for i, cottage in tqdm(enumerate(cottages), total=len(cottages)):
    embedding = get_embedding(cottage["text"])
    metadata = {"text": cottage["text"], "title": cottage["title"]}
    index.upsert([(f"cottage-{i}", embedding, metadata)])

print("✅ Indexing complete.")
