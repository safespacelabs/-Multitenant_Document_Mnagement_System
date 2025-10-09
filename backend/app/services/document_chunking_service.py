"""
Enhanced Document Processing Service with Automatic Chunking
Handles large documents by automatically dividing them into manageable chunks
"""

import json
import uuid
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.anthropic_service import anthropic_service
from app.config import ANTHROPIC_API_KEY


class DocumentChunkingService:
    def __init__(self):
        self.chunk_size = 50000  # Characters per chunk (~10-15 pages)
        self.overlap_size = 5000  # Character overlap between chunks
        self.max_chunks_per_document = 50  # Maximum chunks to prevent abuse
        
    def extract_text_with_page_info(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with page-by-page information"""
        try:
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            pages_data = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and len(page_text.strip()) > 10:
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text': page_text.strip(),
                        'char_count': len(page_text)
                    })
            
            print(f"🔍 Extracted {len(pages_data)} pages from PDF")
            return pages_data
            
        except Exception as e:
            print(f"❌ Error extracting PDF with page info: {e}")
            return []
    
    def create_intelligent_chunks(self, pages_data: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Create intelligent chunks from page data with overlap"""
        if not pages_data:
            return []
        
        chunks = []
        current_chunk = {
            'chunk_id': str(uuid.uuid4()),
            'filename': filename,
            'pages': [],
            'text': '',
            'char_count': 0,
            'start_page': 0,
            'end_page': 0
        }
        
        for page_data in pages_data:
            page_text = page_data['text']
            page_num = page_data['page_number']
            
            # Check if adding this page would exceed chunk size
            if current_chunk['char_count'] + len(page_text) > self.chunk_size and current_chunk['pages']:
                # Finalize current chunk
                current_chunk['end_page'] = current_chunk['pages'][-1]['page_number']
                chunks.append(current_chunk.copy())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk['text'])
                current_chunk = {
                    'chunk_id': str(uuid.uuid4()),
                    'filename': filename,
                    'pages': [],
                    'text': overlap_text,
                    'char_count': len(overlap_text),
                    'start_page': page_num,
                    'end_page': page_num
                }
            
            # Add page to current chunk
            current_chunk['pages'].append(page_data)
            current_chunk['text'] += f"\n\n--- Page {page_num} ---\n{page_text}"
            current_chunk['char_count'] += len(page_text)
            current_chunk['end_page'] = page_num
        
        # Add final chunk if it has content
        if current_chunk['pages']:
            current_chunk['end_page'] = current_chunk['pages'][-1]['page_number']
            chunks.append(current_chunk)
        
        print(f"🔍 Created {len(chunks)} chunks from {len(pages_data)} pages")
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of previous chunk"""
        if len(text) <= self.overlap_size:
            return text
        
        # Get last part of text, trying to break at sentence boundaries
        overlap_text = text[-self.overlap_size:]
        
        # Try to find a good break point
        sentence_endings = ['.', '!', '?', '\n\n']
        for ending in sentence_endings:
            if ending in overlap_text:
                # Find the last occurrence
                last_ending = overlap_text.rfind(ending)
                if last_ending > self.overlap_size // 2:  # Don't make overlap too small
                    return overlap_text[last_ending + 1:].strip()
        
        return overlap_text.strip()
    
    async def process_chunk_with_ai(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single chunk with AI to extract metadata"""
        try:
            if not ANTHROPIC_API_KEY:
                return self._create_fallback_chunk_metadata(chunk)
            
            # Extract metadata for this chunk
            metadata = await anthropic_service._extract_from_text(
                chunk['text'], 
                f"{chunk['filename']}_chunk_{chunk['chunk_id'][:8]}",
                None
            )
            
            # Add chunk-specific information
            metadata.update({
                'chunk_id': chunk['chunk_id'],
                'start_page': chunk['start_page'],
                'end_page': chunk['end_page'],
                'page_count': len(chunk['pages']),
                'is_chunk': True,
                'parent_filename': chunk['filename']
            })
            
            return metadata
            
        except Exception as e:
            print(f"❌ Error processing chunk with AI: {e}")
            return self._create_fallback_chunk_metadata(chunk)
    
    def _create_fallback_chunk_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback metadata for a chunk"""
        return {
            'chunk_id': chunk['chunk_id'],
            'title': f"{chunk['filename']} (Pages {chunk['start_page']}-{chunk['end_page']})",
            'summary': f"Document chunk containing pages {chunk['start_page']} through {chunk['end_page']}",
            'document_type': 'chunk',
            'extracted_text': chunk['text'],
            'word_count': len(chunk['text'].split()),
            'start_page': chunk['start_page'],
            'end_page': chunk['end_page'],
            'page_count': len(chunk['pages']),
            'is_chunk': True,
            'parent_filename': chunk['filename'],
            'processing_status': 'chunk_fallback',
            'extracted_at': datetime.utcnow().isoformat()
        }
    
    async def process_large_document(self, file_content: bytes, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Process a large document by chunking it and extracting metadata for each chunk"""
        try:
            print(f"🔍 Processing large document: {filename}")
            
            # Extract pages with text
            pages_data = self.extract_text_with_page_info(file_content, filename)
            
            if not pages_data:
                return self._create_fallback_metadata(filename, folder_name, "No text extracted", "No text extracted")
            
            # Check if document needs chunking
            total_chars = sum(page['char_count'] for page in pages_data)
            
            if total_chars <= self.chunk_size:
                # Small document, process normally
                print(f"🔍 Document is small ({total_chars} chars), processing normally")
                full_text = '\n'.join(page['text'] for page in pages_data)
                return await anthropic_service._extract_from_text(full_text, filename, folder_name)
            
            # Large document, create chunks
            print(f"🔍 Document is large ({total_chars} chars), creating chunks")
            chunks = self.create_intelligent_chunks(pages_data, filename)
            
            if len(chunks) > self.max_chunks_per_document:
                print(f"⚠️ Document has too many chunks ({len(chunks)}), limiting to {self.max_chunks_per_document}")
                chunks = chunks[:self.max_chunks_per_document]
            
            # Process each chunk with AI
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                print(f"🔍 Processing chunk {i+1}/{len(chunks)} (pages {chunk['start_page']}-{chunk['end_page']})")
                metadata = await self.process_chunk_with_ai(chunk)
                chunk_metadata.append(metadata)
            
            # Create master document metadata
            master_metadata = {
                'title': filename,
                'summary': f"Large document with {len(pages_data)} pages, processed in {len(chunks)} chunks",
                'document_type': 'large_document',
                'extracted_text': f"[LARGE DOCUMENT - {len(pages_data)} pages processed in {len(chunks)} chunks]",
                'word_count': sum(page['char_count'] for page in pages_data),
                'page_count': len(pages_data),
                'chunk_count': len(chunks),
                'chunks': chunk_metadata,
                'is_large_document': True,
                'folder_name': folder_name,
                'processing_status': 'chunked',
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            print(f"✅ Successfully processed large document into {len(chunks)} chunks")
            return master_metadata
            
        except Exception as e:
            print(f"❌ Error processing large document: {e}")
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))
    
    def _create_fallback_metadata(self, filename: str, folder_name: str, error: str, details: str) -> Dict[str, Any]:
        """Create fallback metadata for failed processing"""
        return {
            'title': filename,
            'summary': f"Document processing failed: {error}",
            'document_type': 'unknown',
            'extracted_text': f"Processing failed: {details}",
            'word_count': 0,
            'page_count': 0,
            'chunk_count': 0,
            'is_large_document': False,
            'folder_name': folder_name,
            'processing_status': 'failed',
            'error': error,
            'extracted_at': datetime.utcnow().isoformat()
        }


# Create global instance
document_chunking_service = DocumentChunkingService()
