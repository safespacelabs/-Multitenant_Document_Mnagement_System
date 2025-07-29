import groq
import json
from typing import Dict, Any
from datetime import datetime
from app.config import GROQ_API_KEY, GROQ_MODEL

class GroqService:
    def __init__(self):
        self.client = groq.Groq(
            api_key=GROQ_API_KEY
        )
        self.model = GROQ_MODEL
    
    async def extract_document_metadata(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract metadata from document using Groq API"""
        try:
            # Convert bytes to text (assuming text documents for now)
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_content.decode('utf-8', errors='ignore')
            
            # Limit content size for API (Groq has token limits)
            if len(text_content) > 30000:
                text_content = text_content[:30000] + "..."
            
            prompt = f"""
            Please analyze the following document and extract metadata in JSON format:
            
            Filename: {filename}
            
            Document Content:
            {text_content}
            
            Please provide a JSON response with the following structure:
            {{
                "title": "document title or main subject",
                "summary": "brief summary of the document",
                "key_topics": ["topic1", "topic2", "topic3"],
                "document_type": "type of document (report, contract, email, etc.)",
                "entities": {{
                    "people": ["person names mentioned"],
                    "organizations": ["organization names"],
                    "locations": ["locations mentioned"],
                    "dates": ["important dates"]
                }},
                "keywords": ["relevant keywords"],
                "language": "detected language",
                "word_count": "estimated_word_count",
                "sentiment": "positive/negative/neutral"
            }}
            
            Only respond with valid JSON, no additional text.
            """
            
            # Create chat completion
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            
            try:
                # Parse JSON response
                metadata = json.loads(response_text)
                
                # Add extraction timestamp
                metadata['extracted_at'] = datetime.utcnow().isoformat()
                metadata['ai_model'] = self.model
                
                return metadata
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "title": filename,
                    "summary": "AI extraction failed - JSON parse error",
                    "key_topics": [],
                    "document_type": "unknown",
                    "entities": {
                        "people": [],
                        "organizations": [],
                        "locations": [],
                        "dates": []
                    },
                    "keywords": [],
                    "language": "unknown",
                    "word_count": len(text_content.split()),
                    "sentiment": "neutral",
                    "extracted_at": datetime.utcnow().isoformat(),
                    "ai_model": self.model,
                    "error": "Failed to parse AI response as JSON"
                }
                
        except Exception as e:
            # Fallback metadata if extraction fails
            return {
                "title": filename,
                "summary": f"AI extraction failed: {str(e)}",
                "key_topics": [],
                "document_type": "unknown",
                "entities": {
                    "people": [],
                    "organizations": [],
                    "locations": [],
                    "dates": []
                },
                "keywords": [],
                "language": "unknown",
                "word_count": 0,
                "sentiment": "neutral",
                "extracted_at": datetime.utcnow().isoformat(),
                "ai_model": self.model,
                "error": str(e)
            }

    async def chat_with_document(self, query: str, document_content: str, document_metadata: Dict[str, Any]) -> str:
        """Chat with a document using Groq AI"""
        try:
            # Limit document content for context
            if len(document_content) > 20000:
                document_content = document_content[:20000] + "..."
            
            prompt = f"""
            You are an AI assistant helping users understand and interact with documents.
            
            Document Information:
            - Title: {document_metadata.get('title', 'Unknown')}
            - Type: {document_metadata.get('document_type', 'Unknown')}
            - Summary: {document_metadata.get('summary', 'No summary available')}
            
            Document Content:
            {document_content}
            
            User Question: {query}
            
            Please provide a helpful and accurate answer based on the document content.
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=500
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your question: {str(e)}"

    def test_connection(self) -> Dict[str, Any]:
        """Test Groq API connection"""
        try:
            # Simple test call
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": "Say 'Groq API test successful' if you can read this."}
                ],
                model=self.model,
                temperature=0,
                max_tokens=50
            )
            
            response = chat_completion.choices[0].message.content.strip()
            
            return {
                "success": True,
                "response": response,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model
            }

# Create a global instance for use across the application
groq_service = GroqService() 