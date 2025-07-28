import anthropic
import json
from typing import Dict, Any
from datetime import datetime
from app.config import ANTHROPIC_API_KEY

class AnthropicService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY
        )
    
    async def extract_document_metadata(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract metadata from document using Anthropic API"""
        try:
            # Convert bytes to text (assuming text documents for now)
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_content.decode('utf-8', errors='ignore')
            
            # Limit content size for API
            if len(text_content) > 50000:
                text_content = text_content[:50000] + "..."
            
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
                "word_count": estimated_word_count,
                "sentiment": "positive/negative/neutral"
            }}
            
            Only return the JSON, no other text.
            """
            
            # Use the correct messages API for Claude 3
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the JSON response
            response_text = response.content[0].text if response.content else ""
            metadata = json.loads(response_text)
            metadata["processed_at"] = str(datetime.now())
            metadata["filename"] = filename
            
            return metadata
            
        except Exception as e:
            # Return basic metadata if processing fails
            return {
                "title": filename,
                "summary": "Failed to process document",
                "error": str(e),
                "processed_at": str(datetime.now()),
                "filename": filename
            }

anthropic_service = AnthropicService() 