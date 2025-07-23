import os
import re
import docx
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime, timezone
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# === Load environment variables ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "gh-index"
pinecone_env = os.getenv("PINECONE_ENV")

# === Create index if it doesn't exist ===
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=pinecone_env)
    )

index = pc.Index(index_name)

# === Utility Functions ===

def read_docx(file_path):
    """Read and normalize text from DOCX file"""
    doc = docx.Document(file_path)
    text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
    # Normalize line breaks
    text = text.replace("\r", "\n").strip()
    return text

def format_standard_info(raw_text):
    """Format the general cottage information uniformly"""
    text = raw_text.replace("\r", "").strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    formatted_lines = ["#### 🏠 General Information for All Cottages\n"]
    for line in lines:
        if re.match(r"^[A-Z][\w\s]+[:\-]?\s*\d", line):
            line = re.sub(r"[:\-]?\s+", ": ", line, count=1)
            formatted_lines.append(f"- **{line}**")
        else:
            formatted_lines.append(f"- {line}")
    return "\n".join(formatted_lines)

def extract_cottages_info(text):
    """
    Split the document into sections per cottage using clear headings.
    Correctly handles 'Firs' as a standalone title.
    """
    # Normalize text
    text = re.sub(r"\r", "\n", text).strip()

    # Titles: any line ending with known suffixes or exactly 'Firs'
    title_pattern = re.compile(
        r'^(?P<title>(?:[A-Z][A-Za-z\s]+(?:Cottage|House|Flat|View|Mews|Fold|Bakestones|Holmdale|Treacle|Acer)|Firs))$',
        re.MULTILINE
    )

    matches = list(title_pattern.finditer(text))
    data = []

    for i, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        if title and body:
            data.append({"title": title, "text": body})

    return data

def parse_fields(text):
    """Parse key-value lines into a dictionary"""
    fields = {}
    other_lines = []

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        match = re.match(r"^([A-Za-z\s]+)[:\-]\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            fields[key] = value
        else:
            other_lines.append(line)

    return fields, other_lines

def generate_embedding_text(title, fields, extra_lines):
    """Combine title and fields into a single string for embedding"""
    lines = [f"Cottage: {title}"]
    for key, value in fields.items():
        pretty_key = key.replace("_", " ").capitalize()
        lines.append(f"{pretty_key}: {value}")
    lines.extend(extra_lines)
    return "\n".join(lines)

def get_embedding(text):
    """Generate OpenAI embedding for text"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# === Load and Format Data ===

specific_text = read_docx("Cottage_Specific_Information.docx")
raw_standard_text = read_docx("Information_Standard_Cottages.docx")
formatted_standard_text = format_standard_info(raw_standard_text)

cottages = extract_cottages_info(specific_text)
print(f"Found {len(cottages)} cottages to index:", [c['title'] for c in cottages])

# === Index Data ===

for i, cottage in tqdm(enumerate(cottages), total=len(cottages)):
    title = cottage["title"]
    fields, extra_lines = parse_fields(cottage["text"])
    embedding_text = generate_embedding_text(title, fields, extra_lines)
    embedding = get_embedding(embedding_text)

    metadata = {
        "title": title,
        "text": embedding_text,
        "standard_info": formatted_standard_text,
        "InformationSourceDate": datetime.now(timezone.utc).isoformat(),
        **fields
    }

    try:
        index.upsert([(f"cottage-{i}", embedding, metadata)])
    except Exception as e:
        print(f"Error upserting {title}: {e}")

print("✅ Indexing complete with timestamps and corrected parsing.")
