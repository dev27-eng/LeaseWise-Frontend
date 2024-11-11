import magic
import io
from docx import Document as DocxDocument
from pdfminer.high_level import extract_text
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.mime = magic.Magic(mime=True)
        
    def detect_document_type(self, file_path):
        """Detect document type and validate its content"""
        try:
            # Get MIME type
            mime_type = self.mime.from_file(file_path)
            
            # Initialize response
            result = {
                'mime_type': mime_type,
                'document_type': None,
                'is_valid': False,
                'error': None
            }
            
            # Validate based on mime type
            if mime_type == 'application/pdf':
                result['document_type'] = 'pdf'
                result['is_valid'] = self._validate_pdf(file_path)
            elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                result['document_type'] = 'doc' if mime_type == 'application/msword' else 'docx'
                result['is_valid'] = self._validate_docx(file_path)
            else:
                result['error'] = 'Unsupported file type'
                
            return result
            
        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return {
                'mime_type': None,
                'document_type': None,
                'is_valid': False,
                'error': str(e)
            }
    
    def _validate_pdf(self, file_path):
        """Validate PDF file by attempting to extract text"""
        try:
            text = extract_text(file_path)
            # Check if the PDF contains meaningful text (at least 50 characters)
            return len(text.strip()) >= 50
        except Exception as e:
            logger.error(f"Error validating PDF: {str(e)}")
            return False
            
    def _validate_docx(self, file_path):
        """Validate DOCX file by attempting to read its content"""
        try:
            doc = DocxDocument(file_path)
            # Check if document has at least one paragraph
            return len(doc.paragraphs) > 0
        except Exception as e:
            logger.error(f"Error validating DOCX: {str(e)}")
            return False
