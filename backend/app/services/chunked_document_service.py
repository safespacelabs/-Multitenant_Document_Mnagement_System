"""
Service for managing chunked documents and multi-chunk search
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import and_, or_
from app.services.document_chunking_service import document_chunking_service
from app.services.anthropic_service import anthropic_service
from app.models_chunked_documents import Base as ChunkedBase, ChunkedDocument, DocumentChunk, ChunkedDocumentAnalysis, ChunkedDocumentChat
from app.config import ANTHROPIC_API_KEY


class ChunkedDocumentService:
    def __init__(self):
        self.max_search_chunks = 10  # Maximum chunks to search for a single query
        self.max_chunks_for_answer = 5  # Cap chunks concatenated for LLM call to avoid rate limits
        self.max_combined_chars = 80000  # Hard cap on combined context size sent to LLM
        
    def ensure_chunked_tables(self, company_db: Session) -> None:
        """Ensure chunked document tables exist"""
        try:
            # Create tables if they don't exist using the module Base
            ChunkedBase.metadata.create_all(company_db.bind)
        except Exception as e:
            print(f"ensure_chunked_tables warning: {e}")

    def ensure_chunked_columns_migrated(self, company_db: Session) -> None:
        """Best-effort migration for legacy schemas where user_id was INTEGER.
        Converts to TEXT so UUIDs insert successfully.
        Safe to run repeatedly.
        """
        try:
            company_db.execute(text(
                """
                DO $$
                BEGIN
                    BEGIN
                        ALTER TABLE chunked_documents
                          ALTER COLUMN user_id TYPE text USING user_id::text;
                    EXCEPTION WHEN others THEN
                        -- ignore if column already text or table absent
                        NULL;
                    END;

                    BEGIN
                        ALTER TABLE chunked_document_chats
                          ALTER COLUMN user_id TYPE text USING user_id::text;
                    EXCEPTION WHEN others THEN
                        NULL;
                    END;
                END$$;
                """
            ))
            company_db.commit()
        except Exception as e:
            # Do not block processing if migration isn't possible (no-op)
            print(f"ensure_chunked_columns_migrated warning: {e}")
    
    async def process_large_document_upload(
        self, 
        file_content: bytes, 
        filename: str, 
        folder_name: str,
        user_id: int,
        user_name: str,
        user_email: str,
        company_db: Session
    ) -> Dict[str, Any]:
        """Process a large document upload with automatic chunking"""
        try:
            # Ensure tables exist
            self.ensure_chunked_tables(company_db)
            
            print(f"🔍 Processing large document upload: {filename}")
            
            # Process the document with chunking
            metadata = await document_chunking_service.process_large_document(
                file_content, filename, folder_name
            )
            
            if metadata.get('is_large_document', False):
                # Ensure legacy schemas are compatible
                self.ensure_chunked_tables(company_db)
                self.ensure_chunked_columns_migrated(company_db)
                # Create chunked document record
                chunked_doc = ChunkedDocument(
                    filename=filename,
                    original_filename=filename,
                    file_size=len(file_content),
                    file_type=filename.split('.')[-1].lower() if '.' in filename else 'unknown',
                    folder_name=folder_name,
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    total_pages=metadata.get('page_count', 0),
                    total_chunks=metadata.get('chunk_count', 0),
                    total_characters=metadata.get('word_count', 0),
                    processing_status='processing',
                    metadata_json=metadata
                )
                
                company_db.add(chunked_doc)
                company_db.commit()
                company_db.refresh(chunked_doc)
                
                # Store individual chunks
                chunks_data = metadata.get('chunks', [])
                for i, chunk_metadata in enumerate(chunks_data):
                    chunk = DocumentChunk(
                        chunked_document_id=chunked_doc.id,
                        chunk_number=i + 1,
                        chunk_id=chunk_metadata.get('chunk_id', str(uuid.uuid4())),
                        start_page=chunk_metadata.get('start_page', 0),
                        end_page=chunk_metadata.get('end_page', 0),
                        page_count=chunk_metadata.get('page_count', 0),
                        extracted_text=chunk_metadata.get('extracted_text', ''),
                        character_count=len(chunk_metadata.get('extracted_text', '')),
                        word_count=chunk_metadata.get('word_count', 0),
                        metadata_json=chunk_metadata,
                        processing_status='completed',
                        processed_at=datetime.utcnow()
                    )
                    company_db.add(chunk)
                
                # Update master document status
                chunked_doc.processing_status = 'completed'
                chunked_doc.processing_completed_at = datetime.utcnow()
                company_db.commit()
                
                print(f"✅ Successfully stored chunked document with {len(chunks_data)} chunks")
                
                return {
                    'success': True,
                    'chunked_document_id': chunked_doc.id,
                    'total_pages': chunked_doc.total_pages,
                    'total_chunks': chunked_doc.total_chunks,
                    'processing_status': 'completed'
                }
            else:
                # Small document, process normally
                return {
                    'success': True,
                    'is_small_document': True,
                    'metadata': metadata
                }
                
        except Exception as e:
            print(f"❌ Error processing large document upload: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def search_across_chunks(
        self, 
        chunked_document_id: str, 
        query: str, 
        company_db: Session
    ) -> Dict[str, Any]:
        """Search across all chunks of a document and provide comprehensive answer"""
        try:
            # Get the chunked document
            chunked_doc = company_db.query(ChunkedDocument).filter(
                ChunkedDocument.id == chunked_document_id
            ).first()
            
            if not chunked_doc:
                return {'error': 'Chunked document not found'}
            
            # Get all chunks
            chunks = company_db.query(DocumentChunk).filter(
                and_(
                    DocumentChunk.chunked_document_id == chunked_document_id,
                    DocumentChunk.is_active == True
                )
            ).order_by(DocumentChunk.chunk_number).all()
            
            if not chunks:
                return {'error': 'No chunks found for document'}
            
            # Search for relevant chunks
            relevant_chunks = await self._find_relevant_chunks(chunks, query)
            
            if not relevant_chunks:
                return {
                    'answer': f"I couldn't find information about '{query}' in the document '{chunked_doc.filename}'. The document contains {chunked_doc.total_pages} pages across {chunked_doc.total_chunks} chunks, but none of them appear to contain relevant information for your query.",
                    'relevant_chunks': [],
                    'search_method': 'no_results'
                }
            
            # Generate comprehensive answer from relevant chunks
            answer = await self._generate_comprehensive_answer(
                relevant_chunks, query, chunked_doc.filename
            )
            
            # Store chat history
            chat_record = ChunkedDocumentChat(
                chunked_document_id=chunked_document_id,
                user_id=0,  # Will be set by caller
                question=query,
                answer=answer,
                relevant_chunks=[chunk.chunk_id for chunk in relevant_chunks],
                search_method='multi_chunk_search',
                model_used=anthropic_service.model,
                processing_time_seconds=None
            )
            company_db.add(chat_record)
            company_db.commit()
            
            return {
                'answer': answer,
                'relevant_chunks': [
                    {
                        'chunk_id': chunk.chunk_id,
                        'chunk_number': chunk.chunk_number,
                        'pages': f"{chunk.start_page}-{chunk.end_page}",
                        'page_count': chunk.page_count
                    } for chunk in relevant_chunks
                ],
                'search_method': 'multi_chunk_search',
                'total_chunks_searched': len(chunks),
                'relevant_chunks_found': len(relevant_chunks)
            }
            
        except Exception as e:
            print(f"❌ Error searching across chunks: {e}")
            return {'error': str(e)}
    
    async def _find_relevant_chunks(self, chunks: List[DocumentChunk], query: str) -> List[DocumentChunk]:
        """Find chunks that are most relevant to the query"""
        try:
            # Simple keyword-based search for now
            # In production, you might want to use semantic search or embeddings
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            chunk_scores = []
            
            for chunk in chunks:
                chunk_text_lower = chunk.extracted_text.lower()
                
                # Calculate relevance score
                score = 0
                for word in query_words:
                    if word in chunk_text_lower:
                        score += chunk_text_lower.count(word)
                
                # Boost score for exact phrase matches
                if query_lower in chunk_text_lower:
                    score += 10
                
                if score > 0:
                    chunk_scores.append((chunk, score))
            
            # Sort by score and return top chunks
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            relevant_chunks = [chunk for chunk, score in chunk_scores[:self.max_search_chunks]]
            
            return relevant_chunks
            
        except Exception as e:
            print(f"❌ Error finding relevant chunks: {e}")
            return []
    
    async def _generate_comprehensive_answer(
        self, 
        relevant_chunks: List[DocumentChunk], 
        query: str, 
        filename: str
    ) -> str:
        """Generate a comprehensive answer from multiple relevant chunks"""
        try:
            if not ANTHROPIC_API_KEY:
                return self._create_fallback_answer(relevant_chunks, query, filename)
            
            # Limit number of chunks to control token usage
            limited_chunks = relevant_chunks[: self.max_chunks_for_answer]

            # Combine text from limited chunks with a strict size cap
            combined_text = ""
            chunk_info = []
            for chunk in limited_chunks:
                section = f"\n\n--- Pages {chunk.start_page}-{chunk.end_page} ---\n{chunk.extracted_text}"
                if len(combined_text) + len(section) > self.max_combined_chars:
                    # Truncate section if needed to not exceed the cap
                    remaining = max(0, self.max_combined_chars - len(combined_text))
                    section = section[:remaining]
                    combined_text += section
                    chunk_info.append(f"Pages {chunk.start_page}-{chunk.end_page}")
                    break
                combined_text += section
                chunk_info.append(f"Pages {chunk.start_page}-{chunk.end_page}")
            
            # Final safety cap
            if len(combined_text) > self.max_combined_chars:
                combined_text = combined_text[: self.max_combined_chars] + "..."
            
            # Create comprehensive prompt
            prompt = f"""
You are an expert document assistant analyzing a large document that has been divided into chunks. 
Use the content from the relevant chunks below to answer the user's question comprehensively.

DOCUMENT: {filename}
RELEVANT CHUNKS: {', '.join(chunk_info)}

<document_content>
{combined_text}
</document_content>

QUESTION: {query}

INSTRUCTIONS:
1. Provide a comprehensive answer using information from ALL relevant chunks
2. If information spans multiple chunks, synthesize it into a coherent response
3. If the answer is not found in the provided chunks, clearly state this
4. Include page references when relevant
5. Be thorough but concise

ANSWER:
"""
            
            # Retry/backoff on rate-limit errors
            import time
            backoff = 1.0
            for attempt in range(1, 4):
                try:
                    msg = anthropic_service.client.messages.create(
                        model=anthropic_service.model,
                        max_tokens=1500,
                        temperature=0.0,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return msg.content[0].text.strip()
                except Exception as e:
                    err_text = str(e)
                    if "rate_limit" in err_text or "429" in err_text:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    raise
            
        except Exception as e:
            print(f"❌ Error generating comprehensive answer: {e}")
            return self._create_fallback_answer(relevant_chunks, query, filename)
    
    def _create_fallback_answer(
        self, 
        relevant_chunks: List[DocumentChunk], 
        query: str, 
        filename: str
    ) -> str:
        """Create a fallback answer when AI processing fails"""
        chunk_info = [f"Pages {chunk.start_page}-{chunk.end_page}" for chunk in relevant_chunks]
        
        return f"""Based on the document '{filename}', I found relevant information in the following sections: {', '.join(chunk_info)}.

However, I'm unable to provide a detailed analysis at this time due to processing limitations. The relevant content spans {len(relevant_chunks)} chunks of the document.

To get a more detailed answer, please try:
1. Asking a more specific question
2. Referring to specific page ranges
3. Breaking down your question into smaller parts"""
    
    def get_chunked_document_info(self, chunked_document_id: str, company_db: Session) -> Dict[str, Any]:
        """Get information about a chunked document"""
        try:
            chunked_doc = company_db.query(ChunkedDocument).filter(
                ChunkedDocument.id == chunked_document_id
            ).first()
            
            if not chunked_doc:
                return {'error': 'Chunked document not found'}
            
            chunks = company_db.query(DocumentChunk).filter(
                and_(
                    DocumentChunk.chunked_document_id == chunked_document_id,
                    DocumentChunk.is_active == True
                )
            ).order_by(DocumentChunk.chunk_number).all()
            
            return {
                'id': chunked_doc.id,
                'filename': chunked_doc.filename,
                'total_pages': chunked_doc.total_pages,
                'total_chunks': chunked_doc.total_chunks,
                'total_characters': chunked_doc.total_characters,
                'processing_status': chunked_doc.processing_status,
                'created_at': chunked_doc.created_at,
                'chunks': [
                    {
                        'chunk_id': chunk.chunk_id,
                        'chunk_number': chunk.chunk_number,
                        'pages': f"{chunk.start_page}-{chunk.end_page}",
                        'page_count': chunk.page_count,
                        'character_count': chunk.character_count,
                        'word_count': chunk.word_count
                    } for chunk in chunks
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting chunked document info: {e}")
            return {'error': str(e)}


# Create global instance
chunked_document_service = ChunkedDocumentService()
