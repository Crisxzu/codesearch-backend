"""
Document processing service for extracting text from various file formats.
"""
import os
from typing import Optional

import markdown
from docx import Document
from PyPDF2 import PdfReader


class DocumentService:
    """Service for extracting text content from various document formats."""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'docx',
        '.txt': 'text',
        '.md': 'markdown',
        '.markdown': 'markdown',
    }
    
    @staticmethod
    def is_supported(file_path: str) -> bool:
        """Check if file extension is supported."""
        _, ext = os.path.splitext(file_path.lower())
        return ext in DocumentService.SUPPORTED_EXTENSIONS
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        from io import BytesIO
        
        try:
            pdf = PdfReader(BytesIO(file_bytes))
            text_parts = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            raise
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from DOCX bytes."""
        from io import BytesIO
        
        try:
            doc = Document(BytesIO(file_bytes))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            print(f"Failed to extract text from DOCX: {e}")
            raise
    
    @staticmethod
    def extract_text_from_markdown(file_bytes: bytes) -> str:
        """
        Extract text from Markdown.
        Converts to plain text while preserving structure.
        """
        try:
            md_text = file_bytes.decode('utf-8')
            # Convert markdown to HTML then strip tags for plain text
            html = markdown.markdown(md_text)
            # Simple HTML tag removal (or use BeautifulSoup for more robust parsing)
            import re
            text = re.sub(r'<[^>]+>', '', html)
            return text
        except Exception as e:
            print(f"Failed to process Markdown: {e}")
            # Fallback: return raw markdown
            return file_bytes.decode('utf-8', errors='ignore')
    
    @staticmethod
    def extract_text_from_text(file_bytes: bytes) -> str:
        """Extract text from plain text file."""
        return file_bytes.decode('utf-8', errors='ignore')
    
    @classmethod
    def extract_text(cls, file_path: str, file_bytes: bytes) -> str:
        """
        Extract text from a document based on its file extension.
        
        Args:
            file_path: Path/name of the file (used to determine type)
            file_bytes: Raw file bytes
        
        Returns:
            Extracted text content
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if not cls.is_supported(file_path):
            raise ValueError(f"Unsupported file type: {ext}")
        
        file_type = cls.SUPPORTED_EXTENSIONS[ext]
        
        if file_type == 'pdf':
            return cls.extract_text_from_pdf(file_bytes)
        elif file_type == 'docx':
            return cls.extract_text_from_docx(file_bytes)
        elif file_type == 'markdown':
            return cls.extract_text_from_markdown(file_bytes)
        elif file_type == 'text':
            return cls.extract_text_from_text(file_bytes)
        else:
            raise ValueError(f"Handler not implemented for type: {file_type}")
