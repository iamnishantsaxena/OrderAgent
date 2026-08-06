"""
PDF Processing Module
Handles PDF parsing, text extraction, and intelligent chunking
"""

import io
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    raise ImportError("Please install PDF processing libraries: pip install pypdf2 pdfplumber")

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF Processing with multiple extraction strategies
    """
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Initialize PDF processor
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def process_pdf(self, pdf_file) -> Dict[str, any]:
        """
        Main PDF processing method
        
        Args:
            pdf_file: File path or file-like object
            
        Returns:
            Dictionary with extracted text, metadata, and chunks
        """
        try:
            # Extract text using primary method
            text, metadata = self._extract_text_pypdf(pdf_file)
            
            # Fallback to pdfplumber if pypdf fails
            if not text or len(text.strip()) < 50:
                logger.info("PyPDF extraction minimal, trying pdfplumber...")
                text, metadata = self._extract_text_pdfplumber(pdf_file)
            
            # Extract tables if present
            tables = self._extract_tables(pdf_file)
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            # Create intelligent chunks
            chunks = self._create_chunks(text)
            
            return {
                "text": text,
                "metadata": metadata,
                "chunks": chunks,
                "tables": tables,
                "total_length": len(text),
                "num_chunks": len(chunks),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                "text": "",
                "metadata": {},
                "chunks": [],
                "tables": [],
                "error": str(e),
                "success": False
            }
    
    def _extract_text_pypdf(self, pdf_file) -> Tuple[str, Dict]:
        """Extract text using PyPDF2"""
        try:
            if isinstance(pdf_file, (str, Path)):
                pdf_reader = PyPDF2.PdfReader(str(pdf_file))
            else:
                # Handle file-like objects (Streamlit uploads)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            metadata = {
                "num_pages": len(pdf_reader.pages),
                "extractor": "pypdf2"
            }
            
            # Add PDF metadata if available
            if pdf_reader.metadata:
                metadata.update({
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                })
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
            
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return "", {}
    
    def _extract_text_pdfplumber(self, pdf_file) -> Tuple[str, Dict]:
        """Extract text using pdfplumber (better for complex layouts)"""
        try:
            if isinstance(pdf_file, (str, Path)):
                pdf = pdfplumber.open(str(pdf_file))
            else:
                # Reset file pointer for Streamlit uploads
                pdf_file.seek(0)
                pdf = pdfplumber.open(pdf_file)
            
            text_parts = []
            metadata = {
                "num_pages": len(pdf.pages),
                "extractor": "pdfplumber"
            }
            
            # Extract text from each page
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
            
            pdf.close()
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return "", {}
    
    def _extract_tables(self, pdf_file) -> List[List[List[str]]]:
        """Extract tables from PDF using pdfplumber"""
        tables = []
        
        try:
            if isinstance(pdf_file, (str, Path)):
                pdf = pdfplumber.open(str(pdf_file))
            else:
                pdf_file.seek(0)
                pdf = pdfplumber.open(pdf_file)
            
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
            
            pdf.close()
            logger.info(f"Extracted {len(tables)} tables from PDF")
            
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return tables
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Rejoin with single newlines
        text = '\n'.join(lines)
        
        # Remove page break markers if they're standalone
        text = text.replace('\n--- Page', '\n\nPage')
        
        # Normalize common PDF artifacts
        text = text.replace('\x00', '')  # Remove null bytes
        text = text.replace('\uf0b7', '•')  # Fix bullet points
        
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[Dict[str, any]]:
        """
        Create intelligent chunks from text
        Tries to split on natural boundaries (paragraphs, sentences)
        """
        if not text or len(text) <= self.chunk_size:
            return [{
                "text": text,
                "chunk_id": 0,
                "start_pos": 0,
                "end_pos": len(text)
            }]
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If we're not at the end of the text, try to break at a natural boundary
            if end < len(text):
                # Try to break at paragraph
                break_pos = text.rfind('\n\n', start, end)
                if break_pos == -1:
                    # Try to break at sentence
                    for delimiter in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                        break_pos = text.rfind(delimiter, start, end)
                        if break_pos != -1:
                            break_pos += len(delimiter)
                            break
                
                if break_pos != -1 and break_pos > start:
                    end = break_pos
            
            # Create chunk
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "chunk_id": chunk_id,
                    "start_pos": start,
                    "end_pos": end,
                    "length": len(chunk_text)
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loops
            if start <= chunks[-1]["start_pos"] if chunks else False:
                start = end
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def format_tables_as_text(self, tables: List[List[List[str]]]) -> str:
        """Convert extracted tables to formatted text"""
        if not tables:
            return ""
        
        formatted = []
        for table_idx, table in enumerate(tables):
            formatted.append(f"\n--- Table {table_idx + 1} ---")
            for row in table:
                # Filter out None values and join
                row_text = " | ".join([str(cell) if cell else "" for cell in row])
                formatted.append(row_text)
        
        return "\n".join(formatted)
    
    def get_summary(self, pdf_result: Dict) -> str:
        """Get a summary of the PDF processing results"""
        if not pdf_result.get("success"):
            return f"PDF processing failed: {pdf_result.get('error', 'Unknown error')}"
        
        summary_parts = [
            f"Pages: {pdf_result['metadata'].get('num_pages', 'unknown')}",
            f"Text length: {pdf_result['total_length']} characters",
            f"Chunks: {pdf_result['num_chunks']}",
            f"Tables: {len(pdf_result['tables'])}",
            f"Extractor: {pdf_result['metadata'].get('extractor', 'unknown')}"
        ]
        
        return " | ".join(summary_parts)


class PDFValidator:
    """Validate PDF files before processing"""
    
    @staticmethod
    def is_valid_pdf(file) -> Tuple[bool, str]:
        """
        Check if file is a valid PDF
        
        Returns:
            (is_valid, error_message)
        """
        try:
            if isinstance(file, (str, Path)):
                with open(file, 'rb') as f:
                    header = f.read(4)
            else:
                # File-like object
                file.seek(0)
                header = file.read(4)
                file.seek(0)
            
            if header != b'%PDF':
                return False, "File is not a valid PDF (incorrect header)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating PDF: {e}"
    
    @staticmethod
    def check_file_size(file, max_size_mb: float = 10.0) -> Tuple[bool, str]:
        """
        Check if PDF file size is within limits
        
        Args:
            file: File object or path
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            (is_valid, error_message)
        """
        try:
            if isinstance(file, (str, Path)):
                size = Path(file).stat().st_size
            else:
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset
            
            size_mb = size / (1024 * 1024)
            
            if size_mb > max_size_mb:
                return False, f"File size ({size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error checking file size: {e}"


# Convenience function
def process_pdf_file(pdf_file, chunk_size: int = 2000) -> Dict:
    """
    Process a PDF file and return extracted data
    
    Args:
        pdf_file: File path or file-like object
        chunk_size: Size of text chunks
        
    Returns:
        Dictionary with extraction results
    """
    processor = PDFProcessor(chunk_size=chunk_size)
    return processor.process_pdf(pdf_file)
