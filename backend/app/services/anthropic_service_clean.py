"""
Anthropic AI Service for Document Analysis
Handles both text and image document processing with comprehensive extraction
"""

import json
import anthropic
from datetime import datetime, date
from typing import Dict, Any
from app.config import ANTHROPIC_API_KEY

class AnthropicService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY
        )
        self.model = "claude-3-haiku-20240307"  # Claude Haiku model - more cost-effective
    
    async def extract_document_metadata(self, file_content: bytes, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Extract comprehensive metadata from document using Anthropic API"""
        try:
            print(f"🔍 Starting AI extraction for: {filename}")
            print(f"🔍 Content length: {len(file_content)} bytes")
            
            # Check if this is an image file
            is_image = filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
            
            if is_image:
                print(f"🔍 Processing image document: {filename}")
                # For images, we need to use vision capabilities
                # Convert image to base64 for API
                import base64
                image_base64 = base64.b64encode(file_content).decode('utf-8')
                
                # Use vision API for image documents
                return await self._extract_from_image(image_base64, filename, folder_name)
            else:
                # For text documents, convert bytes to text
                try:
                    text_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    text_content = file_content.decode('utf-8', errors='ignore')
                
                print(f"🔍 Text content: {text_content[:100]}...")
                
                # Limit content size for API (Anthropic has token limits)
                if len(text_content) > 100000:  # Increased limit for better analysis
                    text_content = text_content[:100000] + "..."
                
                return await self._extract_from_text(text_content, filename, folder_name)
            
        except Exception as e:
            # Fallback metadata if extraction fails
            print(f"❌ Anthropic API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))
    
    async def _extract_from_image(self, image_base64: str, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Extract metadata from image documents using vision API"""
        try:
            prompt = f"""
            You are an advanced document analysis AI. Your task is to analyze this document image and extract ALL information visible in the document.
            
            Filename: {filename}
            Folder: {folder_name or 'Unknown'}
            
            MANDATORY REQUIREMENTS:
            1. SCAN EVERY ELEMENT: Look at every part of the document image
            2. EXTRACT ALL TEXT: Read and extract ALL text visible in the document
            3. EXTRACT ALL DATA: Get all names, dates, numbers, addresses, and details
            4. COMPREHENSIVE ANALYSIS: Analyze every section, field, and element
            5. COMPLETE COVERAGE: Don't miss any information, no matter how small
            
            ANALYSIS INSTRUCTIONS:
            - Look at the entire document image carefully
            - Extract every piece of text and data visible
            - Identify all fields, sections, and information blocks
            - Extract all names, dates, numbers, addresses, and details
            - Create a comprehensive summary that mentions everything
            - Don't summarize - provide complete details
            
            Please provide a JSON response with the following structure:
            {{
                "title": "exact document title or main subject",
                "summary": "COMPREHENSIVE summary that covers EVERY detail visible in the document. Include all text, data, names, dates, and information. This should be a complete overview of everything in the document.",
                "document_type": "type of document (passport, military_id, green_card, driver_license, contract, report, email, etc.)",
                "folder_name": "{folder_name or 'Unknown'}",
                "key_topics": ["ALL main topics, sections, and subjects visible in the document"],
                "entities": {{
                    "people": ["ALL person names visible in the document"],
                    "organizations": ["ALL organization names visible"],
                    "locations": ["ALL locations, addresses, and places visible"],
                    "dates": ["ALL important dates visible in the document"],
                    "expiry_dates": ["ALL expiry dates if any"],
                    "issue_dates": ["ALL issue dates if any"]
                }},
                "keywords": ["ALL relevant keywords, terms, and phrases visible in the document"],
                "language": "detected language",
                "word_count": "exact word count of all text visible",
                "sentiment": "positive/negative/neutral",
                "expiry_detected": true/false,
                "expiry_date": "YYYY-MM-DD format if expiry detected, null otherwise",
                "expiry_type": "passport/military_id/green_card/driver_license/other if expiry detected",
                "urgency_level": "high/medium/low based on expiry proximity",
                "extracted_text": "COMPLETE extracted text content - include EVERYTHING visible in the document exactly as it appears",
                "important_notes": ["ALL important information, warnings, or special instructions visible"],
                "compliance_requirements": ["ALL compliance or legal requirements visible"],
                "document_sections": ["list of all sections, fields, and content blocks visible in the document"],
                "key_findings": ["ALL key findings, important details, and significant information visible in the document"],
                "data_points": ["ALL numerical data, statistics, measurements, and quantitative information visible"],
                "action_items": ["ALL action items, tasks, requirements, and next steps visible"]
            }}
            
            CRITICAL INSTRUCTIONS: 
            - Look at the ENTIRE document image
            - Extract EVERY piece of text and information visible
            - The summary must cover ALL visible content in detail
            - Include ALL names, dates, numbers, addresses, and details visible
            - Don't miss any information, no matter how small
            - Look for expiry dates in documents like passports, military IDs, green cards, driver licenses
            - Set expiry_detected to true if any expiry date is found
            - Calculate urgency_level based on how soon the expiry date is
            - Extract all important dates and categorize them properly
            - Only respond with valid JSON, no additional text.
            """
            
            # Create message for Anthropic API with image
            print(f"🔍 Making vision API call to Anthropic with model: {self.model}")
            print(f"🔍 Prompt length: {len(prompt)} characters")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            )
            
            print(f"🔍 Vision API call successful, processing response...")
            
            response_text = message.content[0].text.strip()
            print(f"🔍 Raw API response: {response_text[:200]}...")
            
            try:
                # Parse JSON response
                metadata = json.loads(response_text)
                print(f"🔍 JSON parsed successfully!")
                
                # Add extraction timestamp and processing info
                metadata['extracted_at'] = datetime.utcnow().isoformat()
                metadata['ai_model'] = self.model
                metadata['processing_status'] = 'success'
                
                # Validate and clean expiry date
                if metadata.get('expiry_detected') and metadata.get('expiry_date'):
                    try:
                        expiry_date = datetime.strptime(metadata['expiry_date'], '%Y-%m-%d').date()
                        metadata['expiry_date'] = expiry_date.isoformat()
                        
                        today = date.today()
                        days_until_expiry = (expiry_date - today).days
                        
                        if days_until_expiry < 30:
                            metadata['urgency_level'] = 'high'
                        elif days_until_expiry < 90:
                            metadata['urgency_level'] = 'medium'
                        else:
                            metadata['urgency_level'] = 'low'
                            
                    except ValueError:
                        metadata['expiry_date'] = None
                        metadata['expiry_detected'] = False
                        metadata['urgency_level'] = 'low'
                
                return metadata
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"❌ JSON Parse Error: {e}")
                print(f"❌ Response text: {response_text}")
                return self._create_fallback_metadata(filename, folder_name, f"JSON parse error: {e}", f"JSON parse error: {e}")
                
        except Exception as e:
            # Fallback metadata if extraction fails
            print(f"❌ Vision API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))
    
    async def _extract_from_text(self, text_content: str, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Extract metadata from text documents"""
        try:
            prompt = f"""
            You are an advanced document analysis AI. Your task is to scan and analyze the ENTIRE document content and extract comprehensive information.
            
            Filename: {filename}
            Folder: {folder_name or 'Unknown'}
            
            DOCUMENT CONTENT TO ANALYZE:
            {text_content}
            
            MANDATORY REQUIREMENTS:
            1. SCAN EVERY WORD: Read and analyze the ENTIRE document content word by word
            2. EXTRACT ALL TEXT: Copy the complete text content exactly as it appears
            3. COMPREHENSIVE SUMMARY: Create a detailed summary that covers EVERY section, paragraph, and detail
            4. DETAILED ANALYSIS: Extract every piece of information, data, and content
            5. COMPLETE COVERAGE: Don't miss any information, no matter how small
            
            ANALYSIS INSTRUCTIONS:
            - Read the document from start to finish
            - Extract every single piece of text
            - Identify all sections, paragraphs, and content blocks
            - Extract all names, dates, numbers, addresses, and details
            - Create a comprehensive summary that mentions everything
            - Don't summarize - provide complete details
            
            Please provide a JSON response with the following structure:
            {{
                "title": "exact document title or main subject",
                "summary": "COMPREHENSIVE summary that covers EVERY detail in the document. Include all sections, paragraphs, data, names, dates, and information. This should be a complete overview of everything in the document.",
                "document_type": "type of document (passport, military_id, green_card, driver_license, contract, report, email, etc.)",
                "folder_name": "{folder_name or 'Unknown'}",
                "key_topics": ["ALL main topics, sections, and subjects covered in the document"],
                "entities": {{
                    "people": ["ALL person names mentioned in the document"],
                    "organizations": ["ALL organization names mentioned"],
                    "locations": ["ALL locations, addresses, and places mentioned"],
                    "dates": ["ALL important dates found in the document"],
                    "expiry_dates": ["ALL expiry dates if any"],
                    "issue_dates": ["ALL issue dates if any"]
                }},
                "keywords": ["ALL relevant keywords, terms, and phrases from the document"],
                "language": "detected language",
                "word_count": "exact word count of the document",
                "sentiment": "positive/negative/neutral",
                "expiry_detected": true/false,
                "expiry_date": "YYYY-MM-DD format if expiry detected, null otherwise",
                "expiry_type": "passport/military_id/green_card/driver_license/other if expiry detected",
                "urgency_level": "high/medium/low based on expiry proximity",
                "extracted_text": "COMPLETE extracted text content - include EVERYTHING from the document exactly as it appears, preserve all formatting, structure, and content",
                "important_notes": ["ALL important information, warnings, or special instructions"],
                "compliance_requirements": ["ALL compliance or legal requirements mentioned"],
                "document_sections": ["list of all sections, paragraphs, and content blocks in the document"],
                "key_findings": ["ALL key findings, important details, and significant information from the document"],
                "data_points": ["ALL numerical data, statistics, measurements, and quantitative information"],
                "action_items": ["ALL action items, tasks, requirements, and next steps mentioned"]
            }}
            
            CRITICAL INSTRUCTIONS: 
            - Scan the ENTIRE document content
            - Extract EVERY piece of text and information
            - The summary must cover ALL content in detail
            - Include ALL names, dates, numbers, addresses, and details
            - Don't miss any information, no matter how small
            - Look for expiry dates in documents like passports, military IDs, green cards, driver licenses
            - Set expiry_detected to true if any expiry date is found
            - Calculate urgency_level based on how soon the expiry date is
            - Extract all important dates and categorize them properly
            - Only respond with valid JSON, no additional text.
            """
            
            # Create message for Anthropic API
            print(f"🔍 Making API call to Anthropic with model: {self.model}")
            print(f"🔍 Prompt length: {len(prompt)} characters")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            print(f"🔍 API call successful, processing response...")
            
            response_text = message.content[0].text.strip()
            print(f"🔍 Raw API response: {response_text[:200]}...")
            
            try:
                # Parse JSON response
                metadata = json.loads(response_text)
                print(f"🔍 JSON parsed successfully!")
                
                # Add extraction timestamp and processing info
                metadata['extracted_at'] = datetime.utcnow().isoformat()
                metadata['ai_model'] = self.model
                metadata['processing_status'] = 'success'
                
                # Validate and clean expiry date
                if metadata.get('expiry_detected') and metadata.get('expiry_date'):
                    try:
                        expiry_date = datetime.strptime(metadata['expiry_date'], '%Y-%m-%d').date()
                        metadata['expiry_date'] = expiry_date.isoformat()
                        
                        today = date.today()
                        days_until_expiry = (expiry_date - today).days
                        
                        if days_until_expiry < 30:
                            metadata['urgency_level'] = 'high'
                        elif days_until_expiry < 90:
                            metadata['urgency_level'] = 'medium'
                        else:
                            metadata['urgency_level'] = 'low'
                            
                    except ValueError:
                        metadata['expiry_date'] = None
                        metadata['expiry_detected'] = False
                        metadata['urgency_level'] = 'low'
                
                return metadata
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"❌ JSON Parse Error: {e}")
                print(f"❌ Response text: {response_text}")
                return self._create_fallback_metadata(filename, folder_name, f"JSON parse error: {e}", f"JSON parse error: {e}")
                
        except Exception as e:
            # Fallback metadata if extraction fails
            print(f"❌ Text API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))
    
    def _create_fallback_metadata(self, filename: str, folder_name: str, text_content: str, error: str) -> Dict[str, Any]:
        """Create fallback metadata when AI extraction fails"""
        return {
            "title": filename,
            "summary": f"Document processing failed: {error}",
            "document_type": "unknown",
            "folder_name": folder_name or "Unknown",
            "key_topics": [],
            "entities": {"people": [], "organizations": [], "locations": [], "dates": [], "expiry_dates": [], "issue_dates": []},
            "keywords": [],
            "language": "unknown",
            "word_count": 0,
            "sentiment": "neutral",
            "expiry_detected": False,
            "expiry_date": None,
            "expiry_type": None,
            "urgency_level": "low",
            "extracted_text": text_content,
            "important_notes": [],
            "compliance_requirements": [],
            "document_sections": [],
            "key_findings": [],
            "data_points": [],
            "action_items": [],
            "extracted_at": datetime.utcnow().isoformat(),
            "ai_model": self.model,
            "processing_status": "failed",
            "error": error
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the Anthropic API connection"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": "Test connection"
                    }
                ]
            )
            
            return {
                "success": True,
                "response": "Anthropic API test successful",
                "model": self.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model
            }

# Create service instance
anthropic_service = AnthropicService()
