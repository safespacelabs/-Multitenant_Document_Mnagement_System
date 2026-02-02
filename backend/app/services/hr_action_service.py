"""
HR Action Service - AI-powered intent detection and action execution for HR chatbot
Handles user creation, document uploads, and other HR operations through natural language
"""

import uuid
import logging
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models_company import User
from app.models_document_analysis import HRChatAction, BulkUserImport
from app.auth import get_password_hash
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

# Try to import Anthropic for AI-powered extraction
try:
    import anthropic
    from app.config import ANTHROPIC_API_KEY
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available - using regex-based extraction only")


class HRActionService:
    """AI-powered HR action detection and execution service"""

    # Intent keywords for different HR actions
    CREATE_USER_KEYWORDS = [
        'create user', 'add user', 'new user', 'create employee', 'add employee',
        'onboard', 'hire', 'add new employee', 'create account for', 'add account for',
        'register user', 'register employee', 'set up user', 'setup user',
        'new employee', 'new hire', 'add a user', 'create a user',
        'create an account', 'need to create', 'want to create', 'please create'
    ]

    UPLOAD_DOCUMENT_KEYWORDS = [
        'upload document', 'upload file', 'add document', 'attach document',
        'upload for user', 'upload for employee', 'add file to', 'store document',
        'upload a passport', 'upload passport', 'upload a license', 'upload license',
        'upload i9', 'upload a i9', 'upload the i9', 'add i9', 'add the i9',
        'upload w4', 'upload a w4', 'add w4', 'upload contract', 'upload resume',
        'upload certificate', "upload driver's license", 'upload a driver'
    ]

    BULK_IMPORT_KEYWORDS = [
        'bulk import', 'import users', 'bulk create', 'import employees',
        'upload csv', 'upload excel', 'batch create'
    ]

    # Role mappings for natural language
    ROLE_MAPPINGS = {
        'admin': 'hr_admin',
        'hr admin': 'hr_admin',
        'hr administrator': 'hr_admin',
        'manager': 'hr_manager',
        'hr manager': 'hr_manager',
        'employee': 'employee',
        'staff': 'employee',
        'user': 'employee',
        'viewer': 'viewer',
        'read only': 'viewer',
        'customer': 'customer'
    }

    def __init__(self):
        self.action_timeout_minutes = 15  # Actions expire after 15 minutes
        self.anthropic_client = None
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized for HR action service")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

    async def detect_intent(
        self,
        query: str,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Detect the intent from a user's chat query

        Args:
            query: The user's chat message
            user_role: The role of the user making the request

        Returns:
            Intent detection result with action type and confidence
        """
        query_lower = query.lower().strip()

        # Check for create user intent
        if any(keyword in query_lower for keyword in self.CREATE_USER_KEYWORDS):
            return {
                'intent': 'create_user',
                'confidence': 0.9,
                'requires_confirmation': True,
                'allowed': user_role in ['hr_admin', 'hr_manager']
            }

        # Check for document upload intent
        if any(keyword in query_lower for keyword in self.UPLOAD_DOCUMENT_KEYWORDS):
            return {
                'intent': 'upload_document',
                'confidence': 0.85,
                'requires_confirmation': True,
                'allowed': user_role in ['hr_admin', 'hr_manager']
            }

        # Check for bulk import intent
        if any(keyword in query_lower for keyword in self.BULK_IMPORT_KEYWORDS):
            return {
                'intent': 'bulk_import',
                'confidence': 0.85,
                'requires_confirmation': True,
                'allowed': user_role in ['hr_admin']
            }

        return {
            'intent': None,
            'confidence': 0.0,
            'requires_confirmation': False,
            'allowed': True
        }

    async def extract_user_params(
        self,
        query: str
    ) -> Dict[str, Any]:
        """
        Extract user creation parameters from natural language query
        Uses AI when available, falls back to regex-based extraction

        Args:
            query: The user's chat message containing user details

        Returns:
            Extracted parameters for user creation
        """
        # Try AI-powered extraction first
        if self.anthropic_client:
            try:
                ai_params = await self._extract_user_params_with_ai(query)
                if ai_params and (ai_params.get('full_name') or ai_params.get('email')):
                    logger.info(f"AI extracted user params: {ai_params}")
                    return ai_params
            except Exception as e:
                logger.warning(f"AI extraction failed, using regex fallback: {e}")

        # Fallback to regex-based extraction
        return self._extract_user_params_regex(query)

    async def _extract_user_params_with_ai(self, query: str) -> Dict[str, Any]:
        """Use Claude to extract user creation parameters from natural language"""
        prompt = f"""Extract user creation details from this HR request. Return a JSON object with these fields:
- full_name: The person's full name (first and last name)
- email: Their email address
- role: Their role (one of: hr_admin, hr_manager, employee, viewer, customer). Default to "employee" if not specified.
- username: Suggested username (lowercase, underscores for spaces)

HR Request: "{query}"

Important:
- If a field is not mentioned, set it to null
- For names, use proper capitalization (e.g., "John Doe" not "john doe")
- For email, extract any valid email format
- For role, map common terms: "admin" -> "hr_admin", "manager" -> "hr_manager", "staff" -> "employee"
- Generate username from email prefix or name if not explicitly stated

Respond with ONLY the JSON object, no other text."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            # Handle cases where AI might wrap in markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            params = json.loads(response_text)

            # Ensure all required fields exist
            return {
                'full_name': params.get('full_name'),
                'email': params.get('email'),
                'role': params.get('role', 'employee'),
                'username': params.get('username')
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            raise
        except Exception as e:
            logger.warning(f"AI extraction error: {e}")
            raise

    def _extract_user_params_regex(self, query: str) -> Dict[str, Any]:
        """Fallback regex-based extraction for user parameters"""
        params = {
            'full_name': None,
            'email': None,
            'role': 'employee',  # Default role
            'username': None
        }

        # Extract email using regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, query)
        if email_match:
            params['email'] = email_match.group()

        # Extract role from query
        query_lower = query.lower()
        for keyword, role in self.ROLE_MAPPINGS.items():
            if keyword in query_lower:
                params['role'] = role
                break

        # Try to extract full name - common patterns (case insensitive for flexibility)
        name_patterns = [
            r'(?:named?|called?|for)\s+([A-Za-z]+(?:\s+[A-Za-z]+)+)',  # "named John Doe"
            r'(?:user|employee|account)\s+([A-Za-z]+(?:\s+[A-Za-z]+)+)',  # "user John Doe"
            r'create\s+(?:a\s+)?(?:user|employee|account)\s+(?:for\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)+)',  # "create user John Doe"
            r'add\s+(?:a\s+)?(?:user|employee)\s+(?:for\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)+)',  # "add user John Doe"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+as\s+|\s+with\s+|\s+@)',  # "John Doe as employee" or "John Doe with email"
        ]

        for pattern in name_patterns:
            name_match = re.search(pattern, query, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                # Proper case the name
                params['full_name'] = ' '.join(word.title() for word in name.split())
                break

        # If no name found but email exists, extract from email
        if not params['full_name'] and params['email']:
            email_name = params['email'].split('@')[0]
            # Convert email prefix to name (e.g., john.doe -> John Doe)
            name_parts = re.split(r'[._-]', email_name)
            params['full_name'] = ' '.join(part.title() for part in name_parts)

        # Generate username from email or name
        if params['email']:
            params['username'] = params['email'].split('@')[0].lower().replace('.', '_')
        elif params['full_name']:
            params['username'] = params['full_name'].lower().replace(' ', '_')

        return params

    async def extract_document_upload_params(
        self,
        query: str,
        company_db: Session
    ) -> Dict[str, Any]:
        """
        Extract document upload parameters from natural language query
        Uses AI when available for better extraction

        Args:
            query: The user's chat message
            company_db: Company database session

        Returns:
            Extracted parameters for document upload
        """
        # Try AI-powered extraction first
        if self.anthropic_client:
            try:
                ai_params = await self._extract_doc_params_with_ai(query)
                if ai_params:
                    # Resolve user from AI-extracted name/email
                    await self._resolve_user_for_doc_upload(ai_params, company_db)
                    if ai_params.get('target_user_id') or ai_params.get('document_type'):
                        logger.info(f"AI extracted doc params: {ai_params}")
                        return ai_params
            except Exception as e:
                logger.warning(f"AI doc extraction failed, using regex fallback: {e}")

        # Fallback to regex-based extraction
        return await self._extract_doc_params_regex(query, company_db)

    async def _extract_doc_params_with_ai(self, query: str) -> Dict[str, Any]:
        """Use Claude to extract document upload parameters"""
        prompt = f"""Extract document upload details from this HR request. Return a JSON object with these fields:
- target_user_name: The name of the person/employee the document is for
- target_user_email: Their email if mentioned
- folder_name: The folder/category to upload to (if mentioned)
- document_type: Type of document (e.g., passport, license, i9, w4, contract, resume, certificate, id_card)

HR Request: "{query}"

Important:
- If a field is not mentioned, set it to null
- For document_type, normalize to one of: passport, license, id_card, contract, resume, certificate, i9, w4, other
- Extract the person's name even if phrased informally

Respond with ONLY the JSON object, no other text."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            params = json.loads(response_text)

            return {
                'target_user_id': None,  # Will be resolved later
                'target_user_name': params.get('target_user_name'),
                'target_user_email': params.get('target_user_email'),
                'folder_name': params.get('folder_name'),
                'document_type': params.get('document_type')
            }

        except Exception as e:
            logger.warning(f"AI doc param extraction error: {e}")
            raise

    async def _resolve_user_for_doc_upload(self, params: Dict[str, Any], company_db: Session):
        """Resolve user ID from name or email"""
        # Try email first
        if params.get('target_user_email'):
            user = company_db.query(User).filter(
                User.email == params['target_user_email']
            ).first()
            if user:
                params['target_user_id'] = str(user.id)
                params['target_user_name'] = user.full_name
                params['target_user_email'] = user.email
                return

        # Try name search
        if params.get('target_user_name'):
            user = company_db.query(User).filter(
                User.full_name.ilike(f"%{params['target_user_name']}%")
            ).first()
            if user:
                params['target_user_id'] = str(user.id)
                params['target_user_name'] = user.full_name
                params['target_user_email'] = user.email

    async def _extract_doc_params_regex(self, query: str, company_db: Session) -> Dict[str, Any]:
        """Fallback regex-based extraction for document upload parameters"""
        params = {
            'target_user_id': None,
            'target_user_name': None,
            'target_user_email': None,
            'folder_name': None,
            'document_type': None
        }

        query_lower = query.lower()

        # Try to find user by email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, query)
        if email_match:
            email = email_match.group()
            user = company_db.query(User).filter(User.email == email).first()
            if user:
                params['target_user_id'] = str(user.id)
                params['target_user_name'] = user.full_name
                params['target_user_email'] = user.email

        # Try to find user by name if no email match
        if not params['target_user_id']:
            name_patterns = [
                r"(?:for|to)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)",
                r"(?:user|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)"
            ]

            for pattern in name_patterns:
                name_match = re.search(pattern, query, re.IGNORECASE)
                if name_match:
                    search_name = name_match.group(1).strip()
                    # Search for user by name
                    user = company_db.query(User).filter(
                        User.full_name.ilike(f'%{search_name}%')
                    ).first()
                    if user:
                        params['target_user_id'] = str(user.id)
                        params['target_user_name'] = user.full_name
                        params['target_user_email'] = user.email
                        break

        # Extract folder name
        folder_patterns = [
            r'(?:in|to)\s+(?:folder|directory)\s+["\']?([^"\']+)["\']?',
            r'(?:folder|directory)\s+["\']?([^"\']+)["\']?'
        ]

        for pattern in folder_patterns:
            folder_match = re.search(pattern, query_lower)
            if folder_match:
                params['folder_name'] = folder_match.group(1).strip()
                break

        # Extract document type
        doc_types = ['passport', 'license', 'id card', 'contract', 'resume', 'certificate', 'i9', 'w4']
        for doc_type in doc_types:
            if doc_type in query_lower:
                params['document_type'] = doc_type
                break

        return params

    async def create_pending_action(
        self,
        company_db: Session,
        company_id: str,
        hr_user_id: str,
        session_id: Optional[str],
        action_type: str,
        extracted_params: Dict[str, Any]
    ) -> Tuple[HRChatAction, str]:
        """
        Create a pending action that requires user confirmation

        Args:
            company_db: Company database session
            company_id: Company ID
            hr_user_id: HR user ID who initiated the action
            session_id: Chat session ID
            action_type: Type of action (create_user, upload_document, etc.)
            extracted_params: Parameters extracted from query

        Returns:
            Tuple of (HRChatAction, confirmation_message)
        """
        action_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=self.action_timeout_minutes)

        # Generate confirmation message based on action type
        if action_type == 'create_user':
            confirmation_message = self._generate_user_creation_confirmation(extracted_params)
        elif action_type == 'upload_document':
            confirmation_message = self._generate_document_upload_confirmation(extracted_params)
        else:
            confirmation_message = f"Please confirm you want to perform this action: {action_type}"

        action = HRChatAction(
            id=action_id,
            company_id=company_id,
            session_id=session_id,
            hr_user_id=hr_user_id,
            action_type=action_type,
            action_status='pending',
            extracted_params=extracted_params,
            confirmation_message=confirmation_message,
            expires_at=expires_at
        )

        company_db.add(action)
        company_db.commit()
        company_db.refresh(action)

        return action, confirmation_message

    def _generate_user_creation_confirmation(self, params: Dict[str, Any]) -> str:
        """Generate user-friendly confirmation message for user creation"""
        message = "**Create New User Confirmation**\n\n"
        message += f"I'll create a new user with these details:\n\n"
        message += f"- **Name:** {params.get('full_name', 'Not specified')}\n"
        message += f"- **Email:** {params.get('email', 'Not specified')}\n"
        message += f"- **Username:** {params.get('username', 'Will be generated')}\n"
        message += f"- **Role:** {params.get('role', 'employee').replace('_', ' ').title()}\n\n"

        if not params.get('email'):
            message += "**Note:** Please provide an email address for the new user.\n\n"

        message += "Reply with **'yes'** to create this user, **'no'** to cancel, or provide corrections."

        return message

    def _generate_document_upload_confirmation(self, params: Dict[str, Any]) -> str:
        """Generate user-friendly confirmation message for document upload"""
        message = "**Document Upload Confirmation**\n\n"
        message += f"I'll upload a document with these details:\n\n"

        if params.get('target_user_name'):
            message += f"- **For User:** {params.get('target_user_name')} ({params.get('target_user_email', 'N/A')})\n"
        else:
            message += "- **For User:** Not specified (please provide user name or email)\n"

        if params.get('folder_name'):
            message += f"- **Folder:** {params.get('folder_name')}\n"

        if params.get('document_type'):
            message += f"- **Document Type:** {params.get('document_type').title()}\n"

        message += "\nPlease attach the document file to proceed."
        message += "\n\nReply with **'yes'** to proceed or **'no'** to cancel."

        return message

    async def execute_user_creation(
        self,
        company_db: Session,
        company_id: str,
        params: Dict[str, Any],
        created_by_id: str,
        created_by_name: str,
        company_name: str,
        s3_bucket_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute user creation after confirmation

        Args:
            company_db: Company database session
            company_id: Company ID
            params: User creation parameters
            created_by_id: ID of the HR user who created the user
            created_by_name: Name of the HR user
            company_name: Company name
            s3_bucket_name: S3 bucket name for user folder

        Returns:
            Result of user creation
        """
        try:
            # Validate required fields
            if not params.get('email'):
                return {
                    'success': False,
                    'error': 'Email is required for user creation',
                    'missing_fields': ['email']
                }

            if not params.get('full_name'):
                return {
                    'success': False,
                    'error': 'Full name is required for user creation',
                    'missing_fields': ['full_name']
                }

            # Check if email already exists
            existing_user = company_db.query(User).filter(
                User.email == params['email']
            ).first()

            if existing_user:
                return {
                    'success': False,
                    'error': f"User with email {params['email']} already exists",
                    'existing_user': existing_user.full_name
                }

            # Generate username if not provided
            username = params.get('username')
            if not username:
                username = params['email'].split('@')[0].lower().replace('.', '_')

            # Check if username exists
            existing_username = company_db.query(User).filter(
                User.username == username
            ).first()

            if existing_username:
                # Append number to make unique
                base_username = username
                counter = 1
                while existing_username:
                    username = f"{base_username}{counter}"
                    existing_username = company_db.query(User).filter(
                        User.username == username
                    ).first()
                    counter += 1

            # Generate temporary password
            import secrets
            temp_password = secrets.token_urlsafe(12)
            hashed_password = get_password_hash(temp_password)

            # Create the user
            new_user = User(
                username=username,
                email=params['email'],
                hashed_password=hashed_password,
                full_name=params['full_name'],
                role=params.get('role', 'employee'),
                s3_folder=f"users/{username}/",
                company_id=company_id,
                created_by=created_by_id,
                password_set=False,  # User needs to set their own password
                is_active=True
            )

            company_db.add(new_user)
            company_db.commit()
            company_db.refresh(new_user)

            # Create S3 folder if bucket exists
            if s3_bucket_name:
                try:
                    from app.services.aws_service import aws_service
                    await aws_service.create_user_folder(s3_bucket_name, str(new_user.id))
                except Exception as e:
                    logger.warning(f"Failed to create S3 folder for user {new_user.id}: {e}")

            # Send welcome email with temporary password
            try:
                await email_service.send_user_created_notification(
                    user_email=new_user.email,
                    user_name=new_user.full_name,
                    created_by_name=created_by_name,
                    company_name=company_name,
                    role=new_user.role,
                    temp_password=temp_password
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome email to {new_user.email}: {e}")

            return {
                'success': True,
                'user_id': str(new_user.id),
                'username': new_user.username,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'role': new_user.role,
                'message': f"User {new_user.full_name} created successfully! A welcome email has been sent with login instructions."
            }

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            company_db.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    async def process_confirmation(
        self,
        company_db: Session,
        action_id: str,
        user_response: str,
        hr_user_id: str
    ) -> Dict[str, Any]:
        """
        Process user confirmation response for a pending action

        Args:
            company_db: Company database session
            action_id: ID of the pending action
            user_response: User's response (yes/no/modifications)
            hr_user_id: HR user ID confirming the action

        Returns:
            Result of processing the confirmation
        """
        # Find the pending action
        action = company_db.query(HRChatAction).filter(
            HRChatAction.id == action_id,
            HRChatAction.hr_user_id == hr_user_id,
            HRChatAction.action_status == 'pending'
        ).first()

        if not action:
            return {
                'success': False,
                'error': 'Pending action not found or expired'
            }

        # Check if action has expired
        if action.expires_at and action.expires_at < datetime.utcnow():
            action.action_status = 'expired'
            company_db.commit()
            return {
                'success': False,
                'error': 'Action has expired. Please start again.'
            }

        response_lower = user_response.lower().strip()

        if response_lower in ['yes', 'y', 'confirm', 'proceed', 'ok']:
            action.user_response = 'yes'
            action.action_status = 'confirmed'
            action.confirmed_at = datetime.utcnow()
            company_db.commit()

            return {
                'success': True,
                'status': 'confirmed',
                'action_id': action_id,
                'action_type': action.action_type,
                'params': action.extracted_params
            }

        elif response_lower in ['no', 'n', 'cancel', 'abort']:
            action.user_response = 'no'
            action.action_status = 'cancelled'
            company_db.commit()

            return {
                'success': True,
                'status': 'cancelled',
                'message': 'Action cancelled.'
            }

        else:
            # User provided modifications - try to update params
            action.user_response = 'modified'

            # Try to extract updated parameters from the response
            if action.action_type == 'create_user':
                updated_params = await self.extract_user_params(user_response)
                # Merge with existing params (keep existing values if not updated)
                for key, value in updated_params.items():
                    if value:
                        action.extracted_params[key] = value

            elif action.action_type == 'upload_document':
                updated_params = await self.extract_document_upload_params(user_response, company_db)
                for key, value in updated_params.items():
                    if value:
                        action.extracted_params[key] = value

            company_db.commit()

            # Generate new confirmation message with updated params
            if action.action_type == 'create_user':
                new_confirmation = self._generate_user_creation_confirmation(action.extracted_params)
            else:
                new_confirmation = self._generate_document_upload_confirmation(action.extracted_params)

            return {
                'success': True,
                'status': 'modified',
                'action_id': action_id,
                'updated_params': action.extracted_params,
                'confirmation_message': new_confirmation
            }

    async def get_pending_action(
        self,
        company_db: Session,
        session_id: str,
        hr_user_id: str
    ) -> Optional[HRChatAction]:
        """
        Get the most recent pending action for a chat session

        Args:
            company_db: Company database session
            session_id: Chat session ID
            hr_user_id: HR user ID

        Returns:
            The pending action if found, None otherwise
        """
        return company_db.query(HRChatAction).filter(
            HRChatAction.session_id == session_id,
            HRChatAction.hr_user_id == hr_user_id,
            HRChatAction.action_status == 'pending',
            HRChatAction.expires_at > datetime.utcnow()
        ).order_by(HRChatAction.created_at.desc()).first()

    async def search_users(
        self,
        company_db: Session,
        search_query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for users by name or email

        Args:
            company_db: Company database session
            search_query: Search string
            limit: Maximum results to return

        Returns:
            List of matching users
        """
        users = company_db.query(User).filter(
            (User.full_name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.username.ilike(f'%{search_query}%'))
        ).limit(limit).all()

        return [
            {
                'id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'username': user.username,
                'role': user.role
            }
            for user in users
        ]


# Create global service instance
hr_action_service = HRActionService()
