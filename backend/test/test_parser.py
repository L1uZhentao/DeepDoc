import sys
import os 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import io
from docx import Document
import pytest
from app.convertor.parser import PDFParser, DOCXParser, HTMLParser, CSVParser
from reportlab.pdfgen import canvas

@pytest.fixture
def sample_pdf():
    # Create a PDF with ReportLab
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "Hello, World!")
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.read()

@pytest.fixture
def sample_docx():
    # Sample DOCX content in bytes (minimal DOCX structure for testing)
    docx_content = io.BytesIO()
    doc = Document()
    doc.add_heading('Hello, World!', level=1)
    doc.save(docx_content)
    docx_content.seek(0)
    return docx_content.read()

@pytest.fixture
def sample_html():
    # Sample HTML content in bytes
    return b'<html><head></head><body><h1>Hello, World!</h1></body></html>'

@pytest.fixture
def sample_csv():
    # Sample CSV content in bytes
    return b'header1,header2\nvalue1,value2\nvalue3,value4'

def test_basic_parse_pdf(sample_pdf):
    parser = PDFParser()
    parser.set_file(bytesFile=io.BytesIO(sample_pdf))
    result = parser.basic_parse()
    expected_output = "Hello, World!"
    assert expected_output in result

def test_advanced_parse_pdf(sample_pdf):
    parser = PDFParser()
    parser.set_file(bytesFile=io.BytesIO(sample_pdf))
    result = parser.advanced_parse()
    expected_output = "Hello, World!"
    assert expected_output in result

def test_basic_parse_docx(sample_docx):
    parser = DOCXParser()
    parser.set_file(bytesFile=io.BytesIO(sample_docx))
    result = parser.basic_parse()
    expected_output = "# Hello, World!"
    assert expected_output in result

def test_advanced_parse_docx(sample_docx):
    parser = DOCXParser()
    parser.set_file(bytesFile=io.BytesIO(sample_docx))
    result = parser.advanced_parse()
    expected_output = "# Hello, World!"
    assert expected_output in result

def test_basic_parse_html(sample_html):
    parser = HTMLParser()
    parser.set_file(bytesFile=io.BytesIO(sample_html))
    result = parser.basic_parse()
    expected_output = "Hello, World!"
    assert expected_output in result

def test_advanced_parse_html(sample_html):
    parser = HTMLParser()
    parser.set_file(bytesFile=io.BytesIO(sample_html))
    result = parser.advanced_parse()
    expected_output = "Hello, World!"
    assert expected_output in result

