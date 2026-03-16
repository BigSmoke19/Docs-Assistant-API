import time
import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI

def cleanup_old_sessions(base_folder : str,max_age_hours: int = 24):
    now = time.time()
    
    for session_id in os.listdir(base_folder):
        session_path = os.path.join(base_folder, session_id)
        # Delete sessions older than max_age_hours
        if os.path.isdir(session_path):
            age = now - os.path.getctime(session_path)
            if age > max_age_hours * 3600:
                shutil.rmtree(session_path)
                print(f"🗑️ Deleted old session: {session_id}")

# Run cleanup on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create folders if they don't exist
    os.makedirs("user_files", exist_ok=True)
    os.makedirs("user_data", exist_ok=True)
    os.makedirs("user_chroma_persistent_storage", exist_ok=True)

    cleanup_old_sessions("user_files")
    cleanup_old_sessions("user_data")
    cleanup_old_sessions("user_chroma_persistent_storage")
    yield
