import anthropic
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from app.config import ANTHROPIC_API_KEY

class AnthropicService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY
        )
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
    
    async def extract_document_metadata(self, file_content: bytes, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Extract comprehensive metadata from document using Anthropic API"""
        try:
            # Convert bytes to text (assuming text documents for now)
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_content.decode('utf-8', errors='ignore')
            
            # Limit content size for API (Anthropic has token limits)
            if len(text_content) > 100000:  # Increased limit for better analysis
                text_content = text_content[:100000] + "..."
            
            prompt = f"""
            Please analyze the following document and extract comprehensive metadata in JSON format.
            
            Filename: {filename}
            Folder: {folder_name or 'Unknown'}
            
            Document Content:
            {text_content}
            
            Please provide a JSON response with the following structure:
            {{
                "title": "document title or main subject",
                "summary": "detailed summary of the document content",
                "document_type": "type of document (passport, military_id, green_card, driver_license, contract, report, email, etc.)",
                "folder_name": "{folder_name or 'Unknown'}",
                "key_topics": ["topic1", "topic2", "topic3"],
                "entities": {{
                    "people": ["person names mentioned"],
                    "organizations": ["organization names"],
                    "locations": ["locations mentioned"],
                    "dates": ["important dates"],
                    "expiry_dates": ["expiry dates if any"],
                    "issue_dates": ["issue dates if any"]
                }},
                "keywords": ["relevant keywords"],
                "language": "detected language",
                "word_count": "estimated_word_count",
                "sentiment": "positive/negative/neutral",
                "expiry_detected": true/false,
                "expiry_date": "YYYY-MM-DD format if expiry detected, null otherwise",
                "expiry_type": "passport/military_id/green_card/driver_license/other if expiry detected",
                "urgency_level": "high/medium/low based on expiry proximity",
                "extracted_text": "full extracted text content",
                "important_notes": ["any important information or warnings"],
                "compliance_requirements": ["any compliance or legal requirements mentioned"]
            }}
            
            IMPORTANT: 
            - Look for expiry dates in documents like passports, military IDs, green cards, driver licenses
            - Set expiry_detected to true if any expiry date is found
            - Calculate urgency_level based on how soon the expiry date is
            - Extract all important dates and categorize them properly
            - Only respond with valid JSON, no additional text.
            """
            
            # Create message for Anthropic API
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
            
            response_text = message.content[0].text.strip()
            
            try:
                # Parse JSON response
                metadata = json.loads(response_text)
                
                # Add extraction timestamp and processing info
                metadata['extracted_at'] = datetime.utcnow().isoformat()
                metadata['ai_model'] = self.model
                metadata['processing_status'] = 'success'
                
                # Validate and clean expiry date
                if metadata.get('expiry_detected') and metadata.get('expiry_date'):
                    try:
                        # Parse and validate date format
                        expiry_date = datetime.strptime(metadata['expiry_date'], '%Y-%m-%d').date()
                        metadata['expiry_date'] = expiry_date.isoformat()
                        
                        # Calculate urgency level
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
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._create_fallback_metadata(filename, folder_name, text_content, "JSON parse error")
                
        except Exception as e:
            # Fallback metadata if extraction fails
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))
    
    def _create_fallback_metadata(self, filename: str, folder_name: str, content: str, error: str) -> Dict[str, Any]:
        """Create fallback metadata when AI extraction fails"""
        return {
            "title": filename,
            "summary": f"AI extraction failed: {error}",
            "document_type": "unknown",
            "folder_name": folder_name or "Unknown",
            "key_topics": [],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "expiry_dates": [],
                "issue_dates": []
            },
            "keywords": [],
            "language": "unknown",
            "word_count": len(content.split()) if isinstance(content, str) else 0,
            "sentiment": "neutral",
            "expiry_detected": False,
            "expiry_date": None,
            "expiry_type": None,
            "urgency_level": "low",
            "extracted_text": content if isinstance(content, str) else str(content),
            "important_notes": [f"Processing error: {error}"],
            "compliance_requirements": [],
            "extracted_at": datetime.utcnow().isoformat(),
            "ai_model": self.model,
            "processing_status": "failed",
            "error": error
        }
    
    async def chat_with_document(self, query: str, document_metadata: Dict[str, Any]) -> str:
        """Chat with a document using extracted metadata"""
        try:
            prompt = f"""
            You are an AI assistant helping users understand and interact with documents.
            
            Document Information:
            - Title: {document_metadata.get('title', 'Unknown')}
            - Type: {document_metadata.get('document_type', 'Unknown')}
            - Summary: {document_metadata.get('summary', 'No summary available')}
            - Folder: {document_metadata.get('folder_name', 'Unknown')}
            - Expiry Status: {document_metadata.get('expiry_detected', False)}
            - Expiry Date: {document_metadata.get('expiry_date', 'N/A')}
            
            Extracted Text:
            {document_metadata.get('extracted_text', 'No content available')[:5000]}
            
            User Question: {query}
            
            Please provide a helpful and accurate answer based on the document content and metadata.
            If the document has expiry information, mention it prominently.
            """
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    async def process_hr_admin_query(self, query: str, context: Dict[str, Any]) -> str:
        """Process HR admin queries with comprehensive database context"""
        try:
            # Format the context data for the AI
            context_text = self._format_hr_admin_context(context)
            
            prompt = f"""
            You are an AI assistant for HR administrators with access to comprehensive company database information.
            
            Company Database Context:
            {context_text}
            
            HR Admin Query: {query}
            
            Please provide a comprehensive and helpful response based on the available data. 
            You have access to:
            - User information and statistics
            - Document analytics and insights
            - Compliance status and violations
            - E-signature status and pending items
            - Document expiry information
            - User activity and login history
            
            Provide specific data points, insights, and actionable recommendations where appropriate.
            If the query requires specific user information, document details, or compliance data, 
            reference the exact information from the database context.
            
            Format your response in a clear, professional manner suitable for HR administrators.
            """
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            return f"Error processing HR admin query: {str(e)}"
    
    def _format_hr_admin_context(self, context: Dict[str, Any]) -> str:
        """Format database context for HR admin queries"""
        try:
            formatted_context = "=== COMPANY OVERVIEW ===\n"
            
            # Company overview
            if "company_overview" in context:
                overview = context["company_overview"]
                if "users" in overview:
                    formatted_context += f"Users: {overview['users']['total']} total, {overview['users']['active']} active, {overview['users']['hr_admins']} HR admins, {overview['users']['employees']} employees\n"
                if "documents" in overview:
                    formatted_context += f"Documents: {overview['documents']['total']} total, {overview['documents']['processed']} processed, {overview['documents']['expiring_soon']} expiring soon\n"
                if "activity" in overview:
                    formatted_context += f"Recent Activity: {overview['activity']['recent_uploads']} uploads, {overview['activity']['recent_logins']} logins (last 7 days)\n"
                if "esignatures" in overview:
                    formatted_context += f"E-signatures: {overview['esignatures']['pending']} pending, {overview['esignatures']['completed']} completed\n"
            
            # Document analytics
            if "document_analytics" in context:
                analytics = context["document_analytics"]
                formatted_context += "\n=== DOCUMENT ANALYTICS ===\n"
                
                if "document_types" in analytics:
                    formatted_context += "Document Types:\n"
                    for doc_type in analytics["document_types"][:5]:  # Top 5
                        formatted_context += f"  - {doc_type['type']}: {doc_type['count']} documents\n"
                
                if "folder_distribution" in analytics:
                    formatted_context += "Folder Distribution:\n"
                    for folder in analytics["folder_distribution"][:5]:  # Top 5
                        formatted_context += f"  - {folder['folder']}: {folder['count']} documents\n"
                
                if "expiry_analysis" in analytics:
                    formatted_context += "Expiry Analysis:\n"
                    for expiry in analytics["expiry_analysis"]:
                        formatted_context += f"  - {expiry['urgency']} urgency: {expiry['count']} documents\n"
                
                if "top_users" in analytics:
                    formatted_context += "Top Users by Document Count:\n"
                    for user in analytics["top_users"][:5]:  # Top 5
                        formatted_context += f"  - {user['user']}: {user['count']} documents\n"
            
            # Compliance status
            if "compliance_status" in context:
                compliance = context["compliance_status"]
                formatted_context += "\n=== COMPLIANCE STATUS ===\n"
                
                if "rules" in compliance:
                    formatted_context += f"Active Compliance Rules: {len(compliance['rules'])}\n"
                
                if "active_violations" in compliance:
                    formatted_context += f"Active Violations: {len(compliance['active_violations'])}\n"
                    for violation in compliance["active_violations"][:3]:  # Top 3
                        formatted_context += f"  - {violation['violation_type']} ({violation['severity']}): {violation['description'][:100]}...\n"
                
                if "resolved_violations" in compliance:
                    formatted_context += f"Recently Resolved: {len(compliance['resolved_violations'])} violations\n"
            
            # E-signature status
            if "esignature_status" in context:
                esignature = context["esignature_status"]
                formatted_context += "\n=== E-SIGNATURE STATUS ===\n"
                
                if "statistics" in esignature:
                    stats = esignature["statistics"]
                    formatted_context += f"Total: {stats['total']}, Pending: {stats['pending']}, Completed: {stats['completed']}\n"
                
                if "pending_signatures" in esignature:
                    formatted_context += f"Pending Signatures: {len(esignature['pending_signatures'])}\n"
                    for sig in esignature["pending_signatures"][:3]:  # Top 3
                        formatted_context += f"  - {sig['title']}: {len(sig['recipients'])} recipients\n"
            
            return formatted_context
            
        except Exception as e:
            return f"Error formatting context: {str(e)}"
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Anthropic API connection"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'Anthropic API test successful' if you can read this."
                    }
                ]
            )
            
            response = message.content[0].text.strip()
            
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
anthropic_service = AnthropicService()
