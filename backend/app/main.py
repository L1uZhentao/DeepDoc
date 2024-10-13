from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import logging

from .parsers import ParserFactory

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware
  
app_host = os.getenv("HOST", "localhost")  
app_port = os.getenv("PORT", "3000")  
origins = ["http://" + app_host + ":" + app_port]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}

# Endpoint to upload and process a document
@app.post("/upload")
def upload_file(file: UploadFile = File(...), advanced: bool = False):
    logger.info(f"Received file: {file.filename}")
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Supported file types
    supported_extensions = [".pdf", ".docx", ".csv", ".html"]
    if file_extension not in supported_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        parser = ParserFactory.get_parser(file_extension)
        parser.set_file(file)
        if advanced:
            content = parser.advanced_parse()
        else:
            content = parser.basic_parse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return JSONResponse(content={"markdown": content})
