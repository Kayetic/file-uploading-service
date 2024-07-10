from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import FileResponse
import shutil
import os
from typing import Dict, List, Optional
import schedule
import time
import threading

app = FastAPI()

# Directory to store uploaded files
UPLOAD_DIR = "uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), expiry: Optional[int] = Query(None, description="Expiry time in minutes")) -> Dict[str, str]:
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Schedule file deletion
    if expiry is not None:
        schedule.every(expiry).minutes.do(delete_file, file_path)
    else:
        schedule.every(30).days.do(delete_file, file_path)
    
    # Generate download link
    download_link = f"http://localhost:8000/download/{file.filename}"
    return {"download_link": download_link}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return {"error": "File not found"}

@app.get("/list/")
async def list_files() -> List[Dict[str, str]]:
    files = os.listdir(UPLOAD_DIR)
    file_list = []
    for filename in files:
        download_link = f"http://localhost:8000/download/{filename}"
        file_list.append({"filename": filename, "download_link": download_link})
    return file_list

if __name__ == "__main__":
    import uvicorn
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)