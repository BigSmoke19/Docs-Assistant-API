# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from typing import List
import os
import shutil
from extract_text import get_txt_data
from rag import embedd_data
import uuid
from clean_storage import lifespan

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def clear_folder_contents(folder_path: str):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "Too many requests."})

# ✅ Import RAG lazily — only when first request comes in
rag_loaded = False
query_documents = None
generate_response = None

def load_rag():
    global rag_loaded, query_documents, generate_response
    if not rag_loaded:
        print("Loading RAG pipeline...")
        from rag import query_documents as qd, generate_response as gr
        query_documents = qd
        generate_response = gr
        rag_loaded = True
        print("RAG pipeline loaded ✅")

# ✅ Import agent lazily too
agent_loaded = False
run_agent_func = None

def load_agent():
    global agent_loaded, run_agent_func
    if not agent_loaded:
        print("Loading agent...")
        from agent import run_agent
        run_agent_func = run_agent
        agent_loaded = True
        print("Agent loaded ✅")

class QuestionRequest(BaseModel):
    question: str
    session_id : str

@app.get("/")
def root():
    return {"status": "File Browsing Agent is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

def get_user_folder(session_id: str,type : str) -> str:
    folder = os.path.join(type, session_id)
    return folder

@app.post("/upload")
@limiter.limit("3/minute")
async def upload_files(
    files: List[UploadFile] = File(...),
    request: Request = None,
):

    # Generate unique session
    session_id = str(uuid.uuid4())
    user_folder = get_user_folder(session_id,"user_files")
    user_data_folder = get_user_folder(session_id,"user_data")
    user_chroma_folder = get_user_folder(session_id,"user_chroma_persistent_storage")
    os.makedirs(user_folder, exist_ok=True)
    os.makedirs(user_data_folder, exist_ok=True)
    os.makedirs(user_chroma_folder, exist_ok=True)
    print(f"📁 Session created: {session_id}")

    saved_files = []

    for file in files:
        contents = await file.read()
        if len(contents) == 0:
            print(f"⚠️ Empty: {file.filename}")
            continue

        file_path = os.path.join(user_folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        saved_files.append(file.filename)
        print(f"✅ Saved: {file.filename}")

    await get_txt_data(user_folder,user_data_folder)
    await embedd_data(session_id,user_data_folder)

    return {
        "session_id": session_id,  # ✅ frontend stores this
        "message": f"{len(saved_files)} file(s) uploaded successfully",
        "files": saved_files
    }

@app.post("/ask")
@limiter.limit("5/minute")
def ask(request: Request, body: QuestionRequest):
    load_agent()  # loads only on first request
    result = run_agent_func(body.question,body.session_id, silent=True)
    return {
        "answer": result["answer"],
        "tools_used": result["tools_used"],
        "sources": result["sources"],
        "session_id" : body.session_id
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)