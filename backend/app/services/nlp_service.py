import spacy
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app import models
import json

class NLPService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, use blank model
            self.nlp = spacy.blank("en")
    
    def process_query(self, query: str, user_id: str, company_id: str, db: Session) -> str:
        """Process user query and return relevant answer"""
        try:
            # Analyze the query
            doc = self.nlp(query.lower())
            
            # Extract keywords and entities
            keywords = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            # Search for relevant documents
            relevant_docs = self._search_documents(keywords, entities, user_id, company_id, db)
            
            # Generate response based on found documents
            if relevant_docs:
                response = self._generate_response(query, relevant_docs, keywords)
            else:
                response = "I couldn't find any relevant documents to answer your question. Please try rephrasing your query or upload more documents."
            
            return response
            
        except Exception as e:
            return f"Sorry, I encountered an error processing your query: {str(e)}"
    
    def _search_documents(
        self, 
        keywords: List[str], 
        entities: List[tuple], 
        user_id: str, 
        company_id: str, 
        db: Session
    ) -> List[models.Document]:
        """Search for relevant documents based on keywords and entities"""
        
        # Get user's documents and company-wide documents if admin
        user = db.query(models.User).filter(models.User.id == user_id).first()
        
        if user is not None and user.role == "admin":
            # Admin can access all company documents
            base_query = db.query(models.Document).filter(
                models.Document.company_id == company_id,
                models.Document.processed == True
            )
        else:
            # Regular users can only access their own documents
            base_query = db.query(models.Document).filter(
                models.Document.user_id == user_id,
                models.Document.processed == True
            )
        
        documents = base_query.all()
        relevant_docs = []
        
        for doc in documents:
            if doc.metadata_json:
                metadata = doc.metadata_json
                
                # Check if keywords match document content
                doc_text = (
                    metadata.get('title', '') + ' ' +
                    metadata.get('summary', '') + ' ' +
                    ' '.join(metadata.get('keywords', [])) + ' ' +
                    ' '.join(metadata.get('key_topics', []))
                ).lower()
                
                # Calculate relevance score
                score = 0
                for keyword in keywords:
                    if keyword in doc_text:
                        score += 1
                
                # Check entity matches
                for entity_text, entity_type in entities:
                    entity_lower = entity_text.lower()
                    for entity_list in ['people', 'organizations', 'locations']:
                        if entity_list in metadata.get('entities', {}):
                            for entity in metadata['entities'][entity_list]:
                                if entity_lower in entity.lower():
                                    score += 2
                
                if score > 0:
                    relevant_docs.append((doc, score))
        
        # Sort by relevance score and return top 5
        relevant_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in relevant_docs[:5]]
    
    def _generate_response(
        self, 
        query: str, 
        documents: List[models.Document], 
        keywords: List[str]
    ) -> str:
        """Generate response based on relevant documents"""
        
        if not documents:
            return "No relevant documents found."
        
        # Collect information from documents
        doc_info = []
        for doc in documents:
            metadata = doc.metadata_json
            info = {
                'filename': doc.original_filename,
                'title': metadata.get('title', doc.original_filename),
                'summary': metadata.get('summary', 'No summary available'),
                'topics': metadata.get('key_topics', []),
                'type': metadata.get('document_type', 'Unknown')
            }
            doc_info.append(info)
        
        # Generate response
        response_parts = [
            f"Based on your query about '{query}', I found {len(documents)} relevant document(s):\n"
        ]
        
        for i, info in enumerate(doc_info, 1):
            response_parts.append(
                f"{i}. **{info['title']}** ({info['filename']})\n"
                f"   - Type: {info['type']}\n"
                f"   - Summary: {info['summary']}\n"
                f"   - Key Topics: {', '.join(info['topics'])}\n"
            )
        
        response_parts.append(
            f"\nThese documents contain information related to your keywords: {', '.join(keywords)}"
        )
        
        return '\n'.join(response_parts)

nlp_service = NLPService() 