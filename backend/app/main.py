import threading
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import logging
from .libemail import DeepDocEmailSender
from .convertor.parser import Parser, ParserFactory
from .convertor.enhancer import Enhancer

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
  
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

# Create an instance of DeepDocEmailSender with the markdown content and recipient email
def parse_and_send_email(parser: Parser, file_name:str, receipient_email: str):    
    content = parser.advanced_parse()
    enhancer = Enhancer(model="gpt-3.5-turbo")
    content = enhancer.enhance_extraction(content)
    d = DeepDocEmailSender(content, file_name, receipient_email)
    # Set up the email
    d.setup_email()
    # Send the email
    d.send_email()

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}

# Endpoint to upload and process a document
@app.post("/upload")
def upload_file(file: UploadFile = File(...), advanced: bool = False, receipient_email: str = None):
    logger.info(f"Received file: {file.filename}")
    file_extension = os.path.splitext(file.filename)[1].lower()
    if advanced and not receipient_email:
        raise HTTPException(status_code=400, detail="Recipient email is required for advanced processing")
    # Supported file types
    supported_extensions = [".pdf", ".docx", ".csv", ".html"]
    if file_extension not in supported_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        parser = ParserFactory.get_parser(file_extension)
        parser.set_file(file)
        basic_info = parser.get_document_info()
        if advanced and ("image_count" in basic_info and basic_info["image_count"] > 0):

            # Create a new thread to send the email
            email_thread = threading.Thread(target=parse_and_send_email, args=(parser, file.filename, receipient_email))    
            email_thread.start()

            return JSONResponse(content={"markdown": "## The result will be sent to your email", "file_info": basic_info, "isSentEmail": True})
        else:
            content = parser.basic_parse()
        
        # Extract basic information
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return JSONResponse(content={"markdown": content, "file_info": basic_info, "isSentEmail": False})
