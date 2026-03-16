# 📄 Document Assistant API

A production-ready REST API that allows users to upload documents and ask questions about them using RAG (Retrieval-Augmented Generation). The system supports multiple file formats, session-based user isolation, and uses a free LLM for intelligent answers.

---

## 🧠 How It Works

```
User uploads files (PDF, DOCX, PPTX, TXT)
        ↓
Extract text from each file
        ↓
Split into chunks → Embed → Store in ChromaDB
        ↓
User asks a question
        ↓
ChromaDB finds relevant chunks
        ↓
Groq LLM generates answer from context
        ↓
Return answer + sources
```

---

## 🚀 Features

- 📁 **Multi-format support** — PDF, DOCX, PPTX, TXT
- 👤 **Session-based isolation** — each user gets their own storage
- 🔍 **RAG pipeline** — answers grounded in uploaded documents
- 🧹 **Auto cleanup** — old sessions deleted after 24 hours
- 🛡️ **Rate limiting** — prevents API abuse
- ⚡ **Fast inference** — powered by Groq (Llama 3.3 70B)

---

## 📁 Project Structure

```
Document-Assistant/
├── main.py                          # FastAPI app and endpoints
├── rag.py                           # RAG pipeline (embed, store, query)
├── extract_text.py                  # File text extraction
├── clean_data.py                       # Session cleanup on startup
├── Dockerfile                       # For deployment
├── requirements.txt                 # Python dependencies
├── .env                             # API keys (never commit)
├── user_files/                      # Uploaded files per session
├── user_data/                       # Extracted text per session
└── user_chroma_persistent_storage/  # Vector DB per session
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| `FastAPI` | REST API backend |
| `ChromaDB` | Local persistent vector database |
| `sentence-transformers` | Local text embeddings |
| `Groq (Llama 3.3 70B)` | LLM for answer generation |
| `PyMuPDF` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `python-pptx` | PPTX text extraction |
| `slowapi` | Rate limiting |
| `python-dotenv` | Environment variable management |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/BigSmoke19/Document-Assistant.git
cd Document-Assistant
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

Get your free keys:
- Groq: [console.groq.com](https://console.groq.com)
- HuggingFace: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 5. Run the API

```bash
uvicorn main:app --reload
```

API will be live at `http://localhost:8000`

---

## 📡 API Endpoints

### POST /upload
Upload one or more documents and get a session ID.

**Request:** `multipart/form-data`
```
files  →  File  →  document.pdf
files  →  File  →  notes.docx
```

**Response:**
```json
{
    "session_id": "abc-123-xyz",
    "message": "2 file(s) uploaded successfully",
    "files": ["document.pdf", "notes.docx"]
}
```

---

### POST /ask
Ask a question about your uploaded documents.

**Request:** `application/json`
```json
{
    "question": "What are the main topics covered?",
    "session_id": "abc-123-xyz"
}
```

**Response:**
```json
{
    "answer": "The documents cover...",
    "tools_used": [
        {
            "tool": "search_documents",
            "input": "main topics"
        }
    ]
}
```

---

### GET /health
Check if the API is running.

**Response:**
```json
{
    "status": "ok"
}
```

---

## 💬 Example Usage

```python
import requests

# Step 1 — Upload files
with open("report.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files=[("files", ("report.pdf", f, "application/pdf"))]
    )
data = response.json()
session_id = data["session_id"]

# Step 2 — Ask questions
response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What is the main conclusion?",
        "session_id": session_id
    }
)
print(response.json()["answer"])
```

---

## 🔒 Rate Limits

| Endpoint | Limit |
|---|---|
| `/upload` | 3 requests/minute |
| `/ask` | 5 requests/minute |

---

## 📦 Requirements

```
fastapi
uvicorn
groq
chromadb
sentence-transformers
pymupdf
python-docx
python-pptx
python-dotenv
slowapi
requests
```

Install all:
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key (free) |
| `HF_TOKEN` | HuggingFace token (free) |

---

## 📌 Notes

- Each user upload creates a **unique session** — no data is shared between users
- Sessions are **automatically deleted** after 24 hours
- Embeddings run **fully locally** using sentence-transformers
- The LLM runs on **Groq's free inference API**
- Supported formats: `.pdf`, `.docx`, `.pptx`, `.txt`


## 👤 Author

**Mohammad Safieddine**
CS Graduate | Full Stack Developer | AI Engineer
[LinkedIn](https://www.linkedin.com/in/mohammad-safieddine-153635248) • [GitHub](https://github.com/BigSmoke19)