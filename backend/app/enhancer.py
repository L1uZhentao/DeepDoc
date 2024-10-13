import openai
import os
from typing import List, Optional
from .constant import DocumentType
class Enhancer:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAPI_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it as an argument or in the environment variable 'OPENAPI_KEY'.")
        openai.api_key = self.openai_api_key

    def enhance_extraction(self, extracted_text: str, document_type: DocumentType = DocumentType.PDF, prompt_template: Optional[str] = None) -> str:
        """
        Enhance the extracted text using LLM to correct malformed or incomplete content.
        
        Args:
            extracted_text (str): The raw extracted Markdown text.
            document_type (DocumentType): The type of document from which the text was extracted (e.g., PDF, DOCX, HTML, CSV).
            prompt_template (str, optional): Template to structure the enhancement prompt.

        Returns:
            str: Enhanced Markdown text.
        """
        prompt_template = prompt_template or """
        You are given the following extracted text from a {document_type} document in Markdown format. 
        Correct any malformed or incomplete content while ensuring the Markdown style remains consistent.
        Text:
        {extracted_text}
        """

        prompt = prompt_template.format(extracted_text=extracted_text, document_type=document_type.value)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Markdown text enhancement assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response['choices'][0]['message']['content'].strip()
    
    def handle_multilingual_sections(self, text: str, target_language: str = "en") -> str:
        """
        Use LLMs to translate or improve multilingual or inconsistent sections of the document.
        
        Args:
            text (str): Text, possibly in different languages.
            target_language (str): The target language to translate content into.

        Returns:
            str: Translated and improved text if needed.
        """
        prompt = f"Please translate the following text to {target_language} and improve its clarity if needed:\n\n{text}"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a multilingual text assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response['choices'][0]['message']['content'].strip()

# Usage example:
# enhancer = Enhancer()
# enhanced_text = enhancer.enhance_extraction(raw_markdown_text, document_type=DocumentType.DOCX)
# enhanced_blocks = enhancer.handle_multilingual_sections(text_blocks=['Texto en español', 'Some English text'], target_language='en')