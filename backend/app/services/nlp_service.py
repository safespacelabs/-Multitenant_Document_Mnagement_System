import spacy
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models_company import User as CompanyUser, Document as CompanyDocument
from app.services.groq_service import groq_service
from app.services.intelligent_ai_service import intelligent_ai_service
import json

class NLPService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, use blank model
            self.nlp = spacy.blank("en")
    
    def process_query(self, query: str, user_id: str, company_id: str, db: Session) -> str:
        """Process a query for company users with document context."""
        try:
            # For now, return a simple response
            # In the future, this could use the groq service to provide more intelligent responses
            
            context = self._get_document_context(user_id, company_id, db)
            
            # Simple keyword-based responses
            query_lower = query.lower()
            
            if "document" in query_lower:
                return f"I can help you with document management. You have {len(context.get('documents', []))} documents available."
            elif "upload" in query_lower:
                return "To upload documents, use the Documents section and click the upload button."
            elif "help" in query_lower:
                return "I'm here to help! You can ask me about your documents, how to use the system, or any other questions."
            else:
                return "I understand you're asking about: " + query + ". I'm still learning, but I'm here to help with your document management needs!"
                
        except Exception as e:
            return f"I apologize, but I encountered an error processing your request: {str(e)}"

    def process_system_query(self, query: str, user_id: str, management_db: Session) -> str:
        """Process a query for system administrators with enhanced AI and task execution capabilities."""
        try:
            # Use the intelligent AI service for both responses and task execution
            result = intelligent_ai_service.process_system_query(query, user_id, management_db)
            
            # Return just the response text for backward compatibility
            return result["response"]
                
        except Exception as e:
            return f"I apologize, but I encountered an error processing your system query: {str(e)}"

    def _process_system_query_with_ai(self, query: str, context: dict) -> str:
        """Process system query using Groq AI with system context."""
        try:
            system_prompt = f"""You are a System Administrator Assistant for a multi-tenant document management system with comprehensive knowledge of all system sections.

Current System Status:
- Total Companies: {context.get('total_companies', 0)}
- Active Companies: {context.get('active_companies', 0)}
- Estimated Users: {context.get('total_users', 0)}
- System Health: {context.get('system_health', 'operational')}

SYSTEM SECTIONS AND CAPABILITIES:

🔹 **Overview Section**
- System statistics and health monitoring
- Company overview and activity tracking  
- Real-time system metrics
- Multi-tenant architecture status

🔹 **System Admins Section**
- Create and manage system administrator accounts
- Configure admin privileges and permissions
- Automatic S3 storage setup for new admins
- Admin activity monitoring and security

🔹 **Companies Section**
- Multi-tenant company management with database isolation
- Create companies with dedicated databases
- Monitor company statistics and health
- Test database connections and performance
- Company activation/deactivation controls

🔹 **Documents Section (System-Level)**
- System administrator document management
- Separate from company-specific documents
- System-wide file storage and organization
- Document processing and metadata extraction

🔹 **AI Assistant Section**
- Intelligent system administration guidance
- Context-aware responses using real system data
- Multi-topic assistance covering all system areas
- Integration with Groq AI for advanced responses

🔹 **Analytics Section**
- System-wide analytics and reporting
- Company performance metrics
- User activity insights across all tenants
- Storage usage and system resource monitoring
- Custom time-range analysis (week/month/quarter/year)

🔹 **Settings Section**
- System configuration management
- Profile and security settings
- System-wide preferences and policies
- Password and authentication controls
- File upload and processing settings

🔹 **Testing Section**
- Comprehensive system testing interface
- API endpoint testing and validation
- Role-based access control testing
- Database connection testing
- Real-time test execution and reporting

TECHNICAL CAPABILITIES:
- True database isolation per company
- Neon PostgreSQL database management
- AWS S3 multi-tenant storage
- Role-based access control (System Admin, HR Admin, HR Manager, Employee, Customer)
- Real-time system monitoring and health checks
- Automated company onboarding and setup

Please provide helpful, accurate responses about any of these system areas. Be professional and specific.
If asked about specific data or statistics, use the provided system status information.
"""

            # Create a simple prompt for the AI
            prompt = f"""
{system_prompt}

User Query: {query}

Please provide a helpful response as a System Administrator Assistant.
"""

            # Use the groq service to generate a response
            response = groq_service.client.chat.completions.create(
                model=groq_service.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract text from the response content
            response_text = response.choices[0].message.content if response.choices else ""
            return response_text or "I apologize, but I couldn't generate a response at this time."
            
        except Exception as e:
            # Fall back to basic responses if AI fails
            return self._get_fallback_system_response(query, context)

    def _get_fallback_system_response(self, query: str, context: dict) -> str:
        """Fallback system responses when AI is unavailable."""
        query_lower = query.lower()
        
        # System-level responses
        if any(word in query_lower for word in ["company", "companies"]):
            total_companies = context.get('total_companies', 0)
            active_companies = context.get('active_companies', 0)
            return f"System currently manages {total_companies} companies, with {active_companies} active companies. You can view detailed company information in the Companies section."
        
        elif any(word in query_lower for word in ["user", "users"]):
            total_users = context.get('total_users', 0)
            return f"Across all companies, there are approximately {total_users} users in the system. Use the Companies section to view user details for specific companies."
        
        elif any(word in query_lower for word in ["system", "health", "status"]):
            return f"System Status: Operational\n• Database: Connected\n• Companies: {context.get('total_companies', 0)} managed\n• Active Companies: {context.get('active_companies', 0)}\n• System Health: All services running normally"
        
        elif any(word in query_lower for word in ["help", "what can you do"]):
            return """As a System Administrator Assistant, I can help you with:

• **Company Management**: View statistics, manage companies, monitor activity
• **System Monitoring**: Check system health, database status, performance metrics  
• **User Overview**: Get insights across all companies and users
• **Administrative Tasks**: Guidance on system administration and configuration
• **Troubleshooting**: Help with system-level issues and maintenance

Try asking: "Show system status", "How many companies are active?", or "What administrative tasks need attention?"""
        
        elif any(word in query_lower for word in ["database", "db"]):
            return f"Database Status: Connected and operational\n• Total Companies: {context.get('total_companies', 0)}\n• Management Database: Healthy\n• Company Databases: All accessible"
        
        elif any(word in query_lower for word in ["admin", "administration"]):
            return """System Administration Guide:

• **Company Management**: Create, activate, or deactivate companies
• **System Monitoring**: Regular health checks and performance monitoring
• **User Oversight**: Monitor user activity across all companies
• **Security**: Ensure proper access controls and permissions
• **Maintenance**: Database maintenance and system updates

Use the Companies section for detailed management tasks."""
        
        elif any(word in query_lower for word in ["stats", "statistics", "metrics"]):
            return f"""System Statistics:

**Companies**
• Total: {context.get('total_companies', 0)}
• Active: {context.get('active_companies', 0)}
• Inactive: {context.get('total_companies', 0) - context.get('active_companies', 0)}

**System Health**
• Database: Operational
• Services: All running
• Status: Healthy

For detailed company statistics, visit the Companies section."""
        
        else:
            return f"I understand you're asking about: {query}\n\nAs your System Administrator Assistant, I can help with company management, system monitoring, user oversight, and administrative tasks. Try asking about system status, company statistics, or administrative guidance."

    def _get_document_context(self, user_id: str, company_id: str, db: Session) -> dict:
        """Get document context for company users."""
        try:
            from app.models_company import Document
            documents = db.query(Document).filter(
                Document.user_id == user_id
            ).limit(10).all()
            
            return {
                "documents": [{"id": str(doc.id), "filename": doc.original_filename} for doc in documents]
            }
        except Exception:
            return {"documents": []}

    def _get_system_context(self, management_db: Session) -> dict:
        """Get system-level context for system administrators."""
        try:
            from app import models
            
            # Get company statistics
            total_companies = management_db.query(models.Company).count()
            active_companies = management_db.query(models.Company).filter(
                models.Company.is_active == True
            ).count()
            
            # Get rough user count (would need to query individual company databases for exact count)
            # For now, estimate based on companies
            estimated_users = active_companies * 5  # Rough estimate
            
            return {
                "total_companies": total_companies,
                "active_companies": active_companies,
                "total_users": estimated_users,
                "system_health": "operational"
            }
        except Exception as e:
            return {
                "total_companies": 0,
                "active_companies": 0,
                "total_users": 0,
                "system_health": "unknown",
                "error": str(e)
            }
    
    def _search_documents(
        self, 
        keywords: List[str], 
        entities: List[tuple], 
        user_id: str, 
        db: Session
    ) -> List[CompanyDocument]:
        """Search for relevant documents based on keywords and entities in company database"""
        
        # Get user's documents and company-wide documents if admin
        user = db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
        
        if user is not None and user.role in ["hr_admin", "hr_manager"]:
            # Admins can access all company documents
            base_query = db.query(CompanyDocument).filter(
                CompanyDocument.processed == True
            )
        else:
            # Regular users can only access their own documents
            base_query = db.query(CompanyDocument).filter(
                CompanyDocument.user_id == user_id,
                CompanyDocument.processed == True
            )
        
        documents = base_query.all()
        relevant_docs = []
        
        for doc in documents:
            if doc.metadata_json is not None:
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
        documents: List[CompanyDocument], 
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