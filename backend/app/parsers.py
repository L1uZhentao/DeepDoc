from fastapi import UploadFile
import pdfminer
import docx
import pandas as pd
from tabulate import tabulate
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import io
import logging
import numpy as np
import re
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LAParams, LTFigure
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LTFigure, LAParams


logger = logging.getLogger(__name__)
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

    def basic_parse(self, file: UploadFile) -> str:
        raise NotImplementedError("Basic parse method not implemented")

    def advanced_parse(self, file: UploadFile) -> str:
        raise NotImplementedError("Advanced parse method not implemented")

class PDFParser(Parser):
    def __init__(self):
        super().__init__()
        self.text_blocks = []  # Store all text blocks and their features
        self.font_size_threshold = 0
        self.max_text_length = 100  # Set a threshold for maximum allowed text length for headings
        self.figure_count = 0  # Track the number of figures (images)

    # Main function to parse the PDF into markdown format
    def basic_parse(self) -> str:
        # Step 1: Collect text features and calculate the 80th percentile for font size
        self.collect_text_features()

        # Step 2: Process the text blocks and generate Markdown output
        markdown_output = self.process_text_blocks()

        return markdown_output

    # Step 1: Collect font size and other features from the document, including images (figures)
    def collect_text_features(self):
        doc_bytes = io.BytesIO(self.file)
        font_sizes = []

        # Collect text blocks and their font sizes
        for page_layout in extract_pages(doc_bytes, laparams=LAParams()):
            for element in page_layout:
                if isinstance(element, (LTTextBox, LTTextLine)):
                    for line in element:
                        if isinstance(line, LTTextLine):
                            font_size = None
                            text_content = line.get_text().strip()

                            # Extract the font size from the first LTChar in the LTTextLine
                            for char in line:
                                if isinstance(char, LTChar):
                                    font_size = char.size
                                    break

                            if font_size:
                                # Store the text block and its font size
                                self.text_blocks.append([font_size, text_content])
                                font_sizes.append(font_size)

                # Handle image (figure) detection
                elif isinstance(element, LTFigure):
                    self.figure_count += 1
                    figure_id = f"Figure {self.figure_count}"
                    self.text_blocks.append([None, figure_id])  # Store figure ID as a text block

        # Calculate the 80th percentile font size once for all text blocks
        if font_sizes:
            self.font_size_threshold = np.percentile(font_sizes, 80)

    # Step 2: Process the text blocks and determine which ones are headings or images
    def process_text_blocks(self):
        markdown_output = []
        heading_candidates = self.find_heading_candidates()
        heading_candidates = self.filter_long_text_blocks(heading_candidates)  # New filter for long text blocks

        # Process and format the text blocks
        for index, block in enumerate(self.text_blocks):
            font_size, text_content = block
            if text_content == "-":
                continue

            # Handle headings
            if index in heading_candidates:
                heading_level = self.determine_heading_level(font_size, text_content)
                markdown_output.append(f"{'#' * heading_level} {text_content} {'\n'}")
            # Handle images (figures)
            elif "Figure" in text_content:
                markdown_output.append(f"![{text_content}]({'#figure'})\n")  # Markdown figure syntax
            else:
                markdown_output.append(text_content)

        return "\n".join(markdown_output)

    # Identify heading candidates based on font size (above 80th percentile)
    def find_heading_candidates(self):
        heading_candidates = []

        for i, (font_size, _) in enumerate(self.text_blocks):
            if font_size and font_size > self.font_size_threshold:
                heading_candidates.append(i)

        return heading_candidates

    # Filter out blocks where the text length is too long (i.e., not likely to be a heading)
    def filter_long_text_blocks(self, heading_candidates):
        valid_headings = []

        for i in heading_candidates:
            text_content = self.text_blocks[i][1]
            if len(text_content) <= self.max_text_length:
                valid_headings.append(i)

        return valid_headings

    # Determine the heading level based on the font size
    def determine_heading_level(self, font_size, text):
        # If the text starts with a numbering pattern, use it to determine the heading level
        if re.match(r"^\d+\.\d+\.\d+\s+", text):
            return 3  # e.g., 1.1.1 -> Level 3
        elif re.match(r"^\d+\.\d+\s+", text):
            return 2  # e.g., 1.1 -> Level 2
        elif re.match(r"^\d+\s+", text):
            return 1  # e.g., 1 -> Level 1

        # Fallback to font size-based classification
        if font_size > 16:
            return 1  # Level 1 heading
        elif font_size > 12:
            return 2  # Level 2 heading
        else:
            return 3  # Level 3 heading


class DOCXParser(Parser):
    def basic_parse(self) -> str:
        """
        Basic DOCX parsing: Convert a Word document into Markdown format.
        Handles titles, headings, paragraphs, lists, images, and tables while
        maintaining the original order of elements.
        """
        content = []

        # Read the DOCX file into memory
        doc_bytes = io.BytesIO(self.file)
        doc = Document(doc_bytes)

        # Iterate through document elements in order
        for block in self._iter_block_elements(doc):
            if isinstance(block, Paragraph):  # Handle paragraphs
                content.append(self._convert_paragraph(block))
            elif isinstance(block, Table):  # Handle tables
                content.append(self._convert_table_to_markdown(block))

        return "\n\n".join(content)

    def _iter_block_elements(self, doc):
        """
        A generator that iterates through paragraphs and tables in the document body
        in the order they appear, preserving the document's structure.
        """
        for element in doc.element.body:
            if isinstance(element, CT_P):  # If the element is a paragraph
                yield Paragraph(element, doc)
            elif isinstance(element, CT_Tbl):  # If the element is a table
                yield Table(element, doc)

    def _convert_paragraph(self, para):
        """
        Convert a paragraph with inline formatting (bold, italic, etc.) and handle 
        headings, bullet points, and inline images.
        """
        if para.style.name.startswith('Heading'):
            level = int(para.style.name.split()[-1])  # Extract heading level
            return f"{'#' * level} {para.text.strip()}"
        elif para.style.name == 'Title':
            return f"# {para.text.strip()}"
        elif self._is_list_item(para):
            # Handle bullet or numbered lists
            return self._convert_list_item(para)
        else:
            return self._convert_paragraph_to_markdown(para)

    def _convert_paragraph_to_markdown(self, para):
        """
        Convert a paragraph with inline formatting (bold, italic) to Markdown.
        """
        markdown = ""
        for run in para.runs:
            text = run.text.strip()
            if not text:
                continue

            # Handle bold and italic text
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
        """
        Determine if a paragraph is part of a list (bullet or numbered).
        """
        return 'List' in para.style.name

    def _is_ordered_list_item(self, para):
        """
        Determine if a paragraph is part of an ordered list by checking for numbering properties.
        """
        # Check if the paragraph has a numbering property (numPr), indicating an ordered list
        numPr = para._element.xpath('w:pPr/w:numPr')
        return bool(numPr)  # True if numbering properties are found (ordered list)

    def _convert_list_item(self, para):
        """
        Convert a list item (bulleted or numbered) into Markdown format.
        Handles indentation levels for nested lists.
        """
        # Check if the list is ordered (numbered) or unordered (bulleted)
        list_type = 'ordered' if self._is_ordered_list_item(para) else 'unordered'
        level = self._get_list_level(para)
        indent = '  ' * (level - 1)  # Indent based on the list level

        # Unordered or ordered list prefix
        if list_type == 'unordered':
            prefix = '- '
        else:
            prefix = f"{level}. "  # Using the level as the ordered list number

        return f"{indent}{prefix}{self._convert_paragraph_to_markdown(para)}"

    def _get_list_level(self, para):
        """
        Determine the level of a list item based on its style (for nested lists).
        """
        print(para.style.name)
        # Extract list level from the style name (e.g., 'List Bullet 2')
        if 'Bullet' in para.style.name or 'Number' in para.style.name:
            try:
                return int(para.style.name.split()[-1])  # Extract level (1, 2, 3...)
            except (ValueError, IndexError):
                return 1  # Default to level 1 if not found
        return 1  # Default to level 1 for paragraphs that are not lists

    def _convert_table_to_markdown(self, table):
        """
        Convert a DOCX table to Markdown format.
        """
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)

        # Generate Markdown table
        table_md = []
        table_md.append('| ' + ' | '.join(rows[0]) + ' |')  # Header row
        table_md.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')  # Separator
        for row in rows[1:]:
            table_md.append('| ' + ' | '.join(row) + ' |')

        return "\n".join(table_md)
   
# CSV Parser
class CSVParser(Parser):

    def basic_parse(self) -> str:
        # Implement basic CSV to Markdown conversion using pandas
        if self.file is None:
            raise ValueError("No file data is configured")
        # use pandas to load (self.file)
        df = pd.read_csv(io.BytesIO(self.file))
        # Convert DataFrame to Markdown Table
        res = tabulate(df, tablefmt="pipe", headers="keys")
        return res
    
    def advanced_parse(self) -> str:
        # Implement advanced CSV parsing using AI
        if self.file is None:
            raise ValueError("No file data is configured")
       # Load CSV file into DataFrame
        df = pd.read_csv(io.BytesIO(self.file))
        # Convert DataFrame to Markdown Table
        res = print(tabulate(df, tablefmt="pipe", headers="keys"))
        return res
    
# HTML Parser
class HTMLParser(Parser):

    def basic_parse(self) -> str:
        if self.file is None:
            raise ValueError("No file data is configured")
        content = self.file
        soup = BeautifulSoup(content, 'html.parser')
        markdown_content = md(str(soup))

        return markdown_content

    def advanced_parse(self) -> str:
        if self.data is None:
            raise ValueError("No file data is configured")
        content = self.data
        soup = BeautifulSoup(content, 'html.parser')
        markdown_content = md(str(soup))
        return markdown_content
    

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
