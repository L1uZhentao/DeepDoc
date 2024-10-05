from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

# Import parsers for different file types (to be implemented)
from .parsers import parse_pdf, parse_docx, parse_csv, parse_html

app = FastAPI()

# CORS configuration (assuming frontend runs on http://localhost:3000)
from fastapi.middleware.cors import CORSMiddleware

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple status check endpoint
@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}


# Endpoint to upload and process a document
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Check file extension
    if file_extension not in [".pdf", ".docx", ".csv", ".html"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Handle different file types
    try:
        if file_extension == ".pdf":
            content = await parse_pdf(file)
        elif file_extension == ".docx":
            content = await parse_docx(file)
        elif file_extension == ".csv":
            content = await parse_csv(file)
        elif file_extension == ".html":
            content = await parse_html(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    # Return the extracted content as a response
    return JSONResponse(content={"markdown": content})

