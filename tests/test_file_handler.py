"""Tests for the FileHandler class"""
import pytest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
import io
from typing import Union
from src.utils.file_handler import FileHandler

class MockUploadedFile:
    """Mock class to simulate uploaded files in tests"""
    def __init__(self, name: str, content: Union[str, bytes], is_bytes: bool = False):
        self.name = name
        self._content = content if is_bytes else str(content).encode()

    def read(self):
        return self._content

@pytest.fixture
def file_handler():
    return FileHandler()

@pytest.fixture
def mock_text_file():
    return MockUploadedFile(
        name="test.txt",
        content="This is a test text file\nWith multiple lines\n"
    )

@pytest.fixture
def mock_pdf_file():
    return MockUploadedFile(
        name="test.pdf",
        content=b"%PDF-1.4\nTest PDF content",
        is_bytes=True
    )

@pytest.mark.asyncio
async def test_read_text_file_content(file_handler, mock_text_file):
    """Test reading content from a text file"""
    content = await file_handler.read_text_content(mock_text_file)
    assert isinstance(content, str)
    assert "This is a test text file" in content
    assert "With multiple lines" in content

@pytest.mark.asyncio
async def test_read_pdf_content(file_handler, mock_pdf_file):
    """Test reading content from a PDF file"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        # Mock PDF pages
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_pdf_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert "Extracted PDF content" in content
        mock_pdf_reader.assert_called_once()

@pytest.mark.asyncio
async def test_read_file_content_txt(file_handler, mock_text_file):
    """Test read_file_content with a text file"""
    content = await file_handler.read_file_content(mock_text_file)
    assert isinstance(content, str)
    assert "This is a test text file" in content

@pytest.mark.asyncio
async def test_read_file_content_pdf(file_handler, mock_pdf_file):
    """Test read_file_content with a PDF file"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_file_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert "Extracted PDF content" in content

@pytest.mark.asyncio
async def test_read_file_content_no_file(file_handler):
    """Test read_file_content with no file provided"""
    with pytest.raises(ValueError) as exc_info:
        await file_handler.read_file_content(None)
    assert "No file provided" in str(exc_info.value)

@pytest.mark.asyncio
async def test_read_file_content_invalid_extension(file_handler):
    """Test read_file_content with an invalid file extension"""
    invalid_file = MockUploadedFile(
        name="test.invalid",
        content="Some content"
    )
    
    # Should default to text file handling
    content = await file_handler.read_file_content(invalid_file)
    assert isinstance(content, str)
    assert "Some content" in content

@pytest.mark.asyncio
async def test_read_text_content_with_encoding_error(file_handler):
    """Test reading text content with encoding error"""
    # Create a file with binary content that would cause a decode error
    binary_file = MockUploadedFile(
        name="binary.txt",
        content=b'\x80\x81\x82\x83',
        is_bytes=True
    )
    
    # Should handle the decode error gracefully
    content = await file_handler.read_text_content(binary_file)
    assert isinstance(content, str)
    assert len(content) > 0  # Content should be decoded with 'ignore' option

@pytest.mark.asyncio
async def test_read_pdf_content_with_extraction_error(file_handler):
    """Test reading PDF content when text extraction fails"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        # Mock PDF page that fails to extract text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_pdf_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert content.strip() == ""  # Should return empty string for failed extraction