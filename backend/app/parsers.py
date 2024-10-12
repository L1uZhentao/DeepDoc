import io
import os
from fastapi import FastAPI, UploadFile, File
from azure.core.credentials import AzureKeyCredential
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTImage, LTTextBox, LTTextLine, LTChar, LTFigure, LAParams, LTContainer
import fitz  # PyMuPDF for extracting images from PDFs
import docx2txt  # Library to extract text and images from DOCX
from PIL import Image
import pandas as pd
from tabulate import tabulate
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import re
import numpy as np
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
import logging
logger = logging.getLogger(__name__)

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.vision.imageanalysis.models import VisualFeatures
import hashlib
from functools import cache, lru_cache

# Azure Vision API setup
try:
    AZURE_VISION_ENDPOINT = os.environ["VISION_ENDPOINT"]
    AZURE_VISION_KEY = os.environ["VISION_KEY"]
except KeyError:
    print("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'")
    print("Set them before running this sample.")
    exit()
vision_client = ImageAnalysisClient(
    endpoint=AZURE_VISION_ENDPOINT,
    credential=AzureKeyCredential(AZURE_VISION_KEY)
)
# Base parser class
class Parser:
    def __init__(self, file: UploadFile = None, path: str = None):
        if file:
            self.file = file.file.read()
        elif path:
            with open(path, 'rb') as f:
                self.file = f.read()
        else:
            self.data = None

    def set_file(self, file: UploadFile = None, path: str = None):
        if file:
            self.file = file.file.read()
        elif path:
            with open(path, 'rb') as f:
                self.file = f.read()
        else:
            raise ValueError("Either file or path must be provided")

    def basic_parse(self) -> str:
        raise NotImplementedError("Basic parse method not implemented")

    def advanced_parse(self) -> str:
        raise NotImplementedError("Advanced parse method not implemented")

class PDFParser(Parser):
    def __init__(self):
        super().__init__()
        self.elements = []  # Store all elements (text blocks and images) in the document
        self.font_size_threshold = 0
        self.max_text_length = 100  # Set a threshold for maximum allowed text length for headings
        self.figure_count = 0  # Track the number of figures (images)

    def basic_parse(self) -> str:
        self.collect_elements()
        markdown_output = self.process_elements()
        return markdown_output

    def collect_elements(self):
        doc_bytes = io.BytesIO(self.file)
        font_sizes = []

        # Step 1: Extract all images using PyMuPDF
        pdf_document = fitz.open(stream=self.file, filetype="pdf")
        image_data_list = []
        image_counter = 0  
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                if base_image:
                    image_bytes = base_image.get("image")
                    if image_bytes:
                        image_data_list.append((page_num, io.BytesIO(image_bytes)))

        # Step 2: Parse PDF using pdfminer and collect text elements
        for page_num, page_layout in enumerate(extract_pages(doc_bytes, laparams=LAParams())):
            for element in page_layout:
                if isinstance(element, (LTTextBox, LTTextLine)):
                    for line in element:
                        if isinstance(line, LTTextLine):
                            font_size = None
                            text_content = line.get_text().strip()

                            for char in line:
                                if isinstance(char, LTChar):
                                    font_size = char.size
                                    break

                            if font_size:
                                self.elements.append(("text", font_size, text_content))
                                font_sizes.append(font_size)
                elif isinstance(element, LTFigure):
                    # Insert images in the correct order
                    if image_counter < len(image_data_list) and image_data_list[image_counter][0] == page_num:
                        self.figure_count += 1
                        self.elements.append(("image", image_data_list[image_counter][1]))
                        image_counter += 1

        # Calculate the 80th percentile font size once for all text blocks
        if font_sizes:
            self.font_size_threshold = np.percentile(font_sizes, 80)


    def process_elements(self):
        markdown_output = []
        heading_candidates = self.find_heading_candidates()
        heading_candidates = self.filter_long_text_blocks(heading_candidates)

        image_id = 1
        for index, element in enumerate(self.elements):
            if element[0] == "text":
                _, font_size, text_content = element
                if text_content == "-":
                    continue

                if index in heading_candidates:
                    heading_level = self.determine_heading_level(font_size, text_content)
                    markdown_output.append(f"{'#' * heading_level} {text_content} {'\n'}")
                else:
                    markdown_output.append(text_content)

            elif element[0] == "image":
                image_bytes = element[1]
                if image_bytes:
                    # Validate image dimensions before generating description
                    image = Image.open(image_bytes)
                    if image.size[0] < 50 or image.size[1] < 50 or image.size[0] > 16000 or image.size[1] > 16000:
                        logger.error("Image dimensions are out of supported range (50x50 to 16000x16000)")
                        image_description = "Image description unavailable due to unsupported dimensions"
                    else:
                        image_description = self._generate_image_description(image_bytes)
                    print(image_id, image_description)
                    markdown_output.append(f"\n\n![Figure {image_id}] {image_description}\n")
                    image_id += 1

        return "\n".join(markdown_output)

    @cache
    def _generate_image_description(self, image_bytes):
        # Use Azure Vision API to generate description
        try:
            description_result = vision_client.analyze(image_data=image_bytes.getvalue(), visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ])
            caption = description_result.caption.text if description_result.caption and description_result.caption.text else "Image description unavailable"
            ocr_text = " ".join([line.text for block in description_result.read.blocks for line in block.lines]) if description_result.read else ""
            return f"{caption} - {ocr_text}" if ocr_text else caption
        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return "Image description unavailable"

    def find_heading_candidates(self):
        heading_candidates = []

        for i, element in enumerate(self.elements):
            if element[0] == "text":
                _, font_size, _ = element
                if font_size and font_size > self.font_size_threshold:
                    heading_candidates.append(i)

        return heading_candidates

    def filter_long_text_blocks(self, heading_candidates):
        valid_headings = []

        for i in heading_candidates:
            _, _, text_content = self.elements[i]
            if len(text_content) <= self.max_text_length:
                valid_headings.append(i)

        return valid_headings

    def determine_heading_level(self, font_size, text):
        if re.match(r"^\d+\.\d+\.\d+\s+", text):
            return 3
        elif re.match(r"^\d+\.\d+\s+", text):
            return 2
        elif re.match(r"^\d+\s+", text):
            return 1

        if font_size > 16:
            return 1
        elif font_size > 12:
            return 2
        else:
            return 3

class DOCXParser(Parser):
    def basic_parse(self) -> str:
        content = []

        doc_bytes = io.BytesIO(self.file)
        doc = Document(doc_bytes)
        image_id = 1
        # Iterate through document elements (paragraphs, tables, and images) in order
        for block in self._iter_block_elements(doc):
            if isinstance(block, Paragraph):
                content.append(self._convert_paragraph(block))
            elif isinstance(block, Table):
                content.append(self._convert_table_to_markdown(block))
            elif isinstance(block, bytes):  # If the block is image bytes
                image_bytes = io.BytesIO(block)
                image_description = self._generate_image_description(image_bytes)
                content.append(f"\n\n![Figure {image_id}]: {image_description}\n")
                image_id = image_id + 1

        return "\n\n".join(content)

    def _iter_block_elements(self, doc):
        # Iterate through paragraphs, tables, and images in the document body in the correct order
        for element in doc.element.body:
            if isinstance(element, CT_P):
                yield Paragraph(element, doc)
            elif isinstance(element, CT_Tbl):
                yield Table(element, doc)

        # Extract images from the document using relationships
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_data = rel.target_part.blob
                yield image_data

    def _convert_paragraph(self, para):
        if para.style.name.startswith('Heading'):
            level = int(para.style.name.split()[-1])
            return f"{'#' * level} {para.text.strip()}"
        elif para.style.name == 'Title':
            return f"# {para.text.strip()}"
        elif self._is_list_item(para):
            return self._convert_list_item(para)
        else:
            return self._convert_paragraph_to_markdown(para)

    def _convert_paragraph_to_markdown(self, para):
        markdown = ""
        for run in para.runs:
            text = run.text.strip()
            if not text:
                continue

            if run.bold and run.italic:
                markdown += f"***{text}***"
            elif run.bold:
                markdown += f"**{text}**"
            elif run.italic:
                markdown += f"*{text}*"
            else:
                markdown += text

        return markdown

    def _is_list_item(self, para):
        return 'List' in para.style.name

    def _convert_list_item(self, para):
        list_type = 'ordered' if self._is_ordered_list_item(para) else 'unordered'
        level = self._get_list_level(para)
        indent = '  ' * (level - 1)

        if list_type == 'unordered':
            prefix = '- '
        else:
            prefix = f"{level}. "

        return f"{indent}{prefix}{self._convert_paragraph_to_markdown(para)}"

    def _is_ordered_list_item(self, para):
        numPr = para._element.xpath('w:pPr/w:numPr')
        return bool(numPr)

    def _get_list_level(self, para):
        if 'Bullet' in para.style.name or 'Number' in para.style.name:
            try:
                return int(para.style.name.split()[-1])
            except (ValueError, IndexError):
                return 1
        return 1

    def _convert_table_to_markdown(self, table):
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)

        table_md = []
        table_md.append('| ' + ' | '.join(rows[0]) + ' |')
        table_md.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')
        for row in rows[1:]:
            table_md.append('| ' + ' | '.join(row) + ' |')

        return "\n".join(table_md)

    @cache
    def _generate_image_description(self, image_bytes):
        # Use Azure Vision API to generate description
        try:
            description_result = vision_client.analyze(image_data=image_bytes.getvalue(), visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ])
            caption = description_result.caption.text if description_result.caption and description_result.caption.text else "Image description unavailable"
            ocr_text = " ".join([line.text for block in description_result.read.blocks for line in block.lines]) if description_result.read else ""
            return f"{caption} - {ocr_text}" if ocr_text else caption
        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return "Image description unavailable"
        
class CSVParser(Parser):
    def basic_parse(self) -> str:
        if self.file is None:
            raise ValueError("No file data is configured")
        df = pd.read_csv(io.BytesIO(self.file))
        res = tabulate(df, tablefmt="pipe", headers="keys")
        return res

    def advanced_parse(self) -> str:
        if self.file is None:
            raise ValueError("No file data is configured")
        df = pd.read_csv(io.BytesIO(self.file))
        res = tabulate(df, tablefmt="pipe", headers="keys")
        return res
    
class HTMLParser(Parser):
    def basic_parse(self) -> str:
        if self.file is None:
            raise ValueError("No file data is configured")
        content = self.file
        soup = BeautifulSoup(content, 'html.parser')

        # Determine the base URL if available
        base_url = soup.find('base', href=True)
        base_url = base_url['href'] if base_url else ''

        markdown_content = []
        # Iterate over all tags in the HTML content
        for element in soup.descendants:
            if element.name == 'img' and element.has_attr('src'):
                # Handle image tags
                image_url = element['src']
                if image_url.startswith('//'):
                    # Convert protocol-relative URLs to absolute URLs
                    image_url = 'https:' + image_url
                elif not image_url.startswith(('http://', 'https://')) and base_url:
                    # Convert relative URLs to absolute URLs using the base URL
                    image_url = base_url.rstrip('/') + '/' + image_url.lstrip('/')
                
                image_description = self._generate_image_description_from_url(image_url)
                if image_description != "Image description unavailable":
                    markdown_content.append(f"\n\n![Image: {image_description}]\n")
            elif element.name is not None:
                # Convert other HTML elements to markdown
                markdown_content.append(md(str(element)))

        return "\n".join(markdown_content)

    def _generate_image_description_from_url(self, image_url: str) -> str:
        # Use Azure Vision API to generate description from URL
        try:
            description_result = vision_client.analyze_from_url(
                image_url=image_url,
                visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
                gender_neutral_caption=True
            )
            caption = description_result.caption.text if description_result.caption and description_result.caption.text else "Image description unavailable"
            ocr_text = " ".join([line.text for block in description_result.read.blocks for line in block.lines]) if description_result.read else ""
            return f"{caption} - OCR: {ocr_text}" if ocr_text else caption
        except Exception as e:
            logger.error(f"Error generating image description from URL {image_url}: {e}")
            return "Image description unavailable"

    def advanced_parse(self) -> str:
        if self.data is None:
            raise ValueError("No file data is configured")
        content = self.data
        soup = BeautifulSoup(content, 'html.parser')

        # Determine the base URL if available
        base_url = soup.find('base', href=True)
        base_url = base_url['href'] if base_url else ''

        markdown_content = []
        # Iterate over all tags in the HTML content
        for element in soup.descendants:
            if element.name == 'img' and element.has_attr('src'):
                # Handle image tags
                image_url = element['src']
                if image_url.startswith('//'):
                    # Convert protocol-relative URLs to absolute URLs
                    image_url = 'https:' + image_url
                elif not image_url.startswith(('http://', 'https://')) and base_url:
                    # Convert relative URLs to absolute URLs using the base URL
                    image_url = base_url.rstrip('/') + '/' + image_url.lstrip('/')
                
                image_description = self._generate_image_description_from_url(image_url)
                markdown_content.append(f"\n\n![Image: {image_description}]\n")
            elif element.name is not None:
                # Convert other HTML elements to markdown
                markdown_content.append(md(str(element)))

        return "\n".join(markdown_content)

# Factory class to return appropriate parser based on file type
class ParserFactory:
    @staticmethod
    def get_parser(file_extension: str) -> Parser:
        if file_extension == ".pdf":
            return PDFParser()
        elif file_extension == ".docx":
            return DOCXParser()
        elif file_extension == ".csv":
            return CSVParser()
        elif file_extension == ".html":
            return HTMLParser()
        else:
            raise ValueError("Unsupported file type")