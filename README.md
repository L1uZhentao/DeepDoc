# DeepDoc
An AI-based Doc Parsing and Standardization Platform. 

## Overview

DeepDoc is a full-stack application designed to streamline the process of document format standardization. It takes in different document formats (PDF, DOCX, CSV, and HTML) and converts them into clean Markdown text. The Markdown output is optimized for use cases such as providing context for large language models (LLMs) and storing content in a vector database for retrieval-augmented generation (RAG) workflows. The focus of this application is on effective text extraction, and converting graphical elements into descriptive text for better context enrichment.

## Features

### Core Functionality
1. **Document Parsing**
   - Handles various document formats: PDF, DOCX, CSV, and HTML.
   - Extracts titles, headings, text blocks, and converts graphical elements (such as images) into descriptive text.
   - Produces well-structured, clean Markdown optimized for LLM and vector database use cases.

2. **User Interface**
   - Provides a straightforward user interface for uploading files and receiving Markdown output.

3. **Performance and Robustness**
   - Fast processing even for larger files.
   - Gracefully handles errors (e.g., unsupported file types or extraction issues).

4. **Security**
   - Securely handles document data by deleting files after processing.
   - Ensures API keys are stored securely.

### Optional Features
- **LLM Integration**
  - Uses LLMs to enhance extraction quality by correcting malformed or incomplete content.
  - Handles multilingual or inconsistent document sections.

- **Image Recognition**
  - Utilizes Azure OpenAI for generating textual descriptions for visual content, adding more context to the Markdown.

## Technologies Used
- **Frontend**: React
- **Backend**: Python (FastAPI)
- **Libraries**: `pdfminer`, `python-docx`, `pandas`, `BeautifulSoup`, `Azure OpenAI`

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone git@github.com:L1uZhentao/DeepDoc.git
   cd DeepDoc
   ```

2. **Set Up Environment Variables**
   - Set the following environment variables in a `.env` file:
     ```
     VISION_ENDPOINT=<Your Azure Vision API endpoint>
     VISION_KEY=<Your Azure Vision API key>
     OPENAPI_KEY=<Your OpenAI Key>
     ```

     For the Azure Vision API key setup, please refer to the [Azure Vision API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/quickstarts-sdk/image-analysis-client-library-40?tabs=visual-studio%2Clinux&pivots=programming-language-python).

     For the OpenAI API key setup, please refer to the [OpenAI API Documentation](https://platform.openai.com/docs/overview).
     
3. **Install Dependencies**
   - Install the required dependencies using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   - To start the backend server:
   ```bash
   uvicorn main:app --reload
   ```
   - The application will be accessible at `http://127.0.0.1:8000`.

5. **Frontend Setup**
   - Navigate to the `frontend` folder and follow the setup instructions for the UI framework used (e.g., React).

## Usage Instructions

1. **Upload a File**
   - Use the UI to upload a document (PDF, DOCX, CSV, or HTML).

2. **Receive Markdown Output**
   - The system will parse the document and provide a Markdown representation optimized for LLM use.

## Testing

- Unit tests are included to validate the document parsing and image recognition features.
- To run tests:
  ```bash
  pytest tests/
  ```

## Security Considerations

- **Data Deletion**: All uploaded documents are deleted after processing to ensure privacy and data security.
- **API Key Management**: Store your Azure API keys in environment variables or a secure secret management solution.

## Contribution Guidelines

1. **Fork the Repository**
   - Create a new branch for your feature or bug fix.

2. **Make Changes**
   - Ensure code follows best practices for organization, maintainability, and security.

3. **Submit a Pull Request**
   - Describe the changes made in the pull request.

## License

This project is licensed under the MIT License.

## Contact

For any inquiries, please reach out to [liuzhentao0613@gmail.com].

