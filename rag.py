import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

#HF Embedding function
local_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str) -> list[float]:
    return local_model.encode(text[:512]).tolist()

class HFEmbeddingFunction:
    def name(self) -> str:
        return "sentence_transformer"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [get_embedding(text) for text in input]

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return [get_embedding(text) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return [get_embedding(text) for text in input]

huggingface_ef = HFEmbeddingFunction()

# Groq Face Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to load documents from a directory
def load_documents_from_directory(directory_path):
    print("==== Loading documents from directory ====")
    documents = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            with open(
                os.path.join(directory_path, filename), "r", encoding="utf-8"
            ) as file:
                documents.append({"id": filename, "text": file.read()})
    return documents

# Function to split text into chunks
def split_text(text, chunk_size=1000, chunk_overlap=20):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks

async def embedd_data(session_id : str,directory_path: str = "data"):

    collection = get_collection(session_id)

    # Load documents from the directory
     
    documents = load_documents_from_directory(directory_path)

    print(f"Loaded {len(documents)} documents")
    # Split documents into chunks
    chunked_documents = []
    for doc in documents:
        chunks = split_text(doc["text"])
        print("==== Splitting docs into chunks ====")
        for i, chunk in enumerate(chunks):
            chunked_documents.append({"id": f"{doc['id']}_chunk{i+1}", "text": chunk})

    # print(f"Split documents into {len(chunked_documents)} chunks")

    # Generate embeddings for the document chunks
    for doc in chunked_documents:
        print("==== Generating embeddings... ====")
        doc["embedding"] = get_embedding(doc["text"])

    ##print(doc["embedding"])

    # Upsert documents with embeddings into Chroma
    for doc in chunked_documents:
        print("==== Inserting chunks into db;;; ====")
        collection.upsert(
            ids=[doc["id"]], documents=[doc["text"]], embeddings=[doc["embedding"]]
        )
    return collection

def get_collection(session_id: str):
    # ✅ Each session gets its own ChromaDB storage path
    chroma_client = chromadb.PersistentClient(
        path=f"user_chroma_persistent_storage/{session_id}"
    )
    collection = chroma_client.get_or_create_collection(
        name="documents",
        embedding_function=huggingface_ef
    )
    return collection
# Function to query documents
def query_documents(question,session_id,n_results=2):

    collection = get_collection(session_id)

    # query_embedding = get_embedding(question)
    results = collection.query(query_texts=question, n_results=n_results)

    # Extract the relevant chunks
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]

    # Extract sources
    base_sources = [id for sublist in results["ids"] for id in sublist]

    sources = set()  
    for source in base_sources:
        filename = source.split("_chunk")[0]  # remove chunk number
        filename = filename.replace(".txt", "")  # remove .txt
        sources.add(filename)


    return relevant_chunks,sources

# Function to generate a response from HF
def generate_response(question, relevant_chunks):
    context = "\n\n".join(relevant_chunks)
    prompt = (
        "You are an assistant for question-answering tasks. Use the following pieces of "
        "retrieved context to answer the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the answer concise."
        "\n\nContext:\n" + context + "\n\nQuestion:\n" + question
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            max_tokens=512,
        )

    answer = response.choices[0].message.content  # add .content at the end
    return answer

if __name__ == "__main__":
    # Example query and response generation
    question = "what are the steps of installing react?"
    relevant_chunks,sources = query_documents(question)
    answer = generate_response(question, relevant_chunks)

    print(answer)
    
    for filename in sources:
        print(f"  📄 {filename}")