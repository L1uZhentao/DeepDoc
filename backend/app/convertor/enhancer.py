import openai
import os
from typing import List, Optional
from .constant import DocumentType
class Enhancer:
    def __init__(self, model: str ,openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAPI_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it as an argument or in the environment variable 'OPENAPI_KEY'.")
        openai.api_key = self.openai_api_key
        self.model = model
        self.client = openai.OpenAI(api_key=self.openai_api_key)

    def enhance(self, text: str, document_type: DocumentType = DocumentType.PDF):
        enhanced_text = self.enhance_extraction(text, document_type)
        unified_text = self.handle_multilingual_sections(enhanced_text, target_language="en")
        return unified_text
    
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
        try:
            prompt_template = prompt_template or """
            You are given the following extracted text from a {document_type} document in Markdown format. 
            Correct any malformed or incomplete content while ensuring the Markdown style remains consistent.
            Text:
            {extracted_text}
            """

            prompt = prompt_template.format(extracted_text=extracted_text, document_type=document_type.value)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Markdown text enhancement assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response['choices'][0]['message']['content'].strip()
        except:
            return extracted_text
    
    def handle_multilingual_sections(self, text: str, target_language: str = "en") -> str:
        """
        Use LLMs to translate or improve multilingual or inconsistent sections of the document.
        
        Args:
            text (str): Text, possibly in different languages.
            target_language (str): The target language to translate content into.

        Returns:
            str: Translated and improved text if needed.
        """
        try:
            prompt = f"Please translate the following text to {target_language} and improve its clarity if needed:\n\n{text}"

            response =  self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a multilingual text assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response['choices'][0]['message']['content'].strip()
        except:
            return text