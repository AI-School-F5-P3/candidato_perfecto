"""Pruebas para el módulo file_handler"""
import pytest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
import io
from typing import Union
from src.utils.file_handler import FileHandler

class MockUploadedFile:
    """Clase simulada para archivos subidos en pruebas"""
    def __init__(self, name: str, content: Union[str, bytes], is_bytes: bool = False):
        self.name = name
        self._content = content if is_bytes else str(content).encode()

    def read(self):
        return self._content

@pytest.fixture
def file_handler():
    """Fixture que proporciona una instancia de FileHandler"""
    return FileHandler()

@pytest.fixture
def mock_text_file():
    """Fixture que proporciona un archivo de texto simulado"""
    return MockUploadedFile(
        name="test.txt",
        content="This is a test text file\nWith multiple lines\n"
    )

@pytest.fixture
def mock_pdf_file():
    """Fixture que proporciona un archivo PDF simulado"""
    return MockUploadedFile(
        name="test.pdf",
        content=b"%PDF-1.4\nTest PDF content",
        is_bytes=True
    )

@pytest.mark.asyncio
async def test_read_text_file_content(file_handler, mock_text_file):
    """Prueba la lectura de contenido de un archivo de texto"""
    content = await file_handler.read_text_content(mock_text_file)
    assert isinstance(content, str)
    assert "This is a test text file" in content
    assert "With multiple lines" in content

@pytest.mark.asyncio
async def test_read_pdf_content(file_handler, mock_pdf_file):
    """Prueba la lectura de contenido de un archivo PDF"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        # Simula una página de PDF con texto
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_pdf_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert "Extracted PDF content" in content
        mock_pdf_reader.assert_called_once()

@pytest.mark.asyncio
async def test_read_file_content_txt(file_handler, mock_text_file):
    """Prueba read_file_content con un archivo de texto"""
    content = await file_handler.read_file_content(mock_text_file)
    assert isinstance(content, str)
    assert "This is a test text file" in content

@pytest.mark.asyncio
async def test_read_file_content_pdf(file_handler, mock_pdf_file):
    """Prueba read_file_content con un archivo PDF"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_file_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert "Extracted PDF content" in content

@pytest.mark.asyncio
async def test_read_file_content_no_file(file_handler):
    """Prueba read_file_content sin archivo"""
    with pytest.raises(ValueError) as exc_info:
        await file_handler.read_file_content(None)
    assert "No file provided" in str(exc_info.value)

@pytest.mark.asyncio
async def test_read_file_content_invalid_extension(file_handler):
    """Prueba read_file_content con una extensión de archivo inválida"""
    invalid_file = MockUploadedFile(
        name="test.invalid",
        content="Some content"
    )
    
    # Debería usar el manejo de archivos de texto por defecto
    content = await file_handler.read_file_content(invalid_file)
    assert isinstance(content, str)
    assert "Some content" in content

@pytest.mark.asyncio
async def test_read_text_content_with_encoding_error(file_handler):
    """Prueba la lectura de contenido de texto con error de codificación"""
    # Crea un archivo con contenido binario que causaría un error de decodificación
    binary_file = MockUploadedFile(
        name="binary.txt",
        content=b'\x80\x81\x82\x83',
        is_bytes=True
    )
    
    # Debería manejar el error de decodificación correctamente
    content = await file_handler.read_text_content(binary_file)
    assert isinstance(content, str)
    assert len(content) > 0  # El contenido debería ser decodificado con la opción 'ignore'

@pytest.mark.asyncio
async def test_read_pdf_content_with_extraction_error(file_handler, mock_pdf_file):
    """Prueba la lectura de contenido PDF cuando falla la extracción de texto"""
    with patch('PyPDF2.PdfReader') as mock_pdf_reader:
        # Simula una página de PDF que falla al extraer texto
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_pdf_reader.return_value.pages = [mock_page]
        
        content = await file_handler.read_pdf_content(mock_pdf_file)
        
        assert isinstance(content, str)
        assert content.strip() == ""  # Debería devolver una cadena vacía en caso de error