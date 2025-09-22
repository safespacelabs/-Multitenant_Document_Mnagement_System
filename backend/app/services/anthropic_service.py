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
        self.model = "claude-3-haiku-20240307"  # Primary model (cost-effective)
        self.fallback_model = "claude-3-5-sonnet-20241022"  # Higher-accuracy fallback for tough OCR
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text content from PDF file with multiple methods"""
        try:
            print(f"🔍 Extracting text from PDF...")
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            
            # If no text extracted, try alternative method
            if len(text_content.strip()) < 10:
                print(f"🔍 Trying alternative PDF text extraction...")
                try:
                    # Try with different extraction method
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        # Try different extraction approaches
                        page_text = page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text)
                        if page_text:
                            text_content += page_text + "\n"
                except Exception as e:
                    print(f"🔍 Alternative extraction failed: {e}")
            
            print(f"🔍 Extracted {len(text_content)} characters from PDF")
            
            # If still no meaningful text, create a descriptive fallback
            if len(text_content.strip()) < 10:
                print(f"🔍 PDF appears to be image-based, creating descriptive fallback")
                text_content = f"PDF Document: {len(pdf_reader.pages)} page(s) - appears to contain scanned images or non-extractable text. Document requires visual analysis for text extraction."
            
            return text_content.strip()
        except Exception as e:
            print(f"❌ Error extracting PDF text: {e}")
            return f"PDF Document - text extraction failed: {str(e)}"
    
    def _convert_pdf_to_image(self, file_content: bytes) -> bytes:
        """Convert PDF to image for vision API processing"""
        try:
            print(f"🔍 Converting PDF to image...")
            import io
            # First try PyMuPDF (no external poppler dependency)
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=file_content, filetype="pdf")
                if doc.page_count > 0:
                    page = doc.load_page(0)
                    pix = page.get_pixmap(dpi=300)
                    img_data = pix.tobytes("png")
                    print(f"🔍 PDF converted to image via PyMuPDF: {len(img_data)} bytes")
                    return img_data
            except ImportError:
                print("❌ PyMuPDF not installed, will try pdf2image")
            except Exception as e:
                print(f"❌ PyMuPDF conversion failed: {e}")

            # Fallback to pdf2image (requires poppler)
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(file_content, first_page=1, last_page=1, dpi=300)
                if images:
                    img_buffer = io.BytesIO()
                    images[0].save(img_buffer, format='PNG')
                    img_data = img_buffer.getvalue()
                    print(f"🔍 PDF converted to image via pdf2image: {len(img_data)} bytes")
                    return img_data
                else:
                    print(f"❌ No images generated from PDF (pdf2image)")
                    return None
            except ImportError:
                print(f"❌ pdf2image not installed, cannot convert PDF to image")
                return None
        except Exception as e:
            print(f"❌ Error converting PDF to image: {e}")
            return None
    
    async def extract_document_metadata(self, file_content: bytes, filename: str, folder_name: str = None) -> Dict[str, Any]:
        """Extract comprehensive metadata from document using Anthropic API"""
        try:
            print(f"🔍 Starting AI extraction for: {filename}")
            print(f"🔍 Content length: {len(file_content)} bytes")
            
            # Check file type and process accordingly
            is_image = filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
            is_pdf = filename.lower().endswith('.pdf')
            
            if is_image:
                print(f"🔍 Processing image document with vision: {filename}")
                # For images, use vision capabilities to extract text directly
                import base64
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                
                # Use vision API for image processing
                return await self._extract_from_image(file_base64, filename, folder_name)
            elif is_pdf:
                print(f"🔍 Processing PDF document: {filename}")
                # For PDFs, try text extraction first, then convert to image if needed
                text_content = self._extract_text_from_pdf(file_content)
                
                print(f"🔍 Extracted text: {text_content[:200]}...")
                
                # If we got meaningful text, process it with text API
                if len(text_content.strip()) > 20 and not text_content.startswith("PDF Document:"):
                    print(f"🔍 Processing extracted PDF text with AI...")
                    # Limit content size for API
                    if len(text_content) > 100000:
                        text_content = text_content[:100000] + "..."
                    
                    return await self._extract_from_text(text_content, filename, folder_name)
                else:
                    print(f"🔍 PDF text extraction limited, converting PDF to image for vision analysis...")
                    # Convert PDF to image and use vision API
                    try:
                        image_data = self._convert_pdf_to_image(file_content)
                        if image_data:
                            import base64
                            image_base64 = base64.b64encode(image_data).decode('utf-8')
                            print(f"🔍 PDF converted to image, using vision API...")
                            return await self._extract_from_image(image_base64, filename, folder_name)
                        else:
                            print(f"❌ PDF to image conversion failed, using fallback...")
                            return await self._extract_from_text(text_content, filename, folder_name)
                    except Exception as e:
                        print(f"❌ PDF to image conversion error: {e}, using fallback...")
                        return await self._extract_from_text(text_content, filename, folder_name)
            else:
                print(f"🔍 Processing text document: {filename}")
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
    
    def _is_sparse_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Heuristic to detect weak/empty extraction results."""
        try:
            extracted_text = (metadata or {}).get("extracted_text") or ""
            word_count = (metadata or {}).get("word_count") or 0
            entities = (metadata or {}).get("entities") or {}
            key_value_pairs = (metadata or {}).get("key_value_pairs") or {}
            # Sparse if no words, no entities, or extremely short text
            if isinstance(word_count, str):
                try:
                    word_count = int(word_count)
                except Exception:
                    word_count = 0
            no_entities = all(not v for v in entities.values()) if isinstance(entities, dict) else True
            too_short = len(extracted_text.strip()) < 50
            no_kv = len(key_value_pairs) == 0
            return (word_count == 0 or too_short) and no_entities and no_kv
        except Exception:
            return True

    async def _extract_from_image(self, file_base64: str, filename: str, folder_name: str = None, *, model_override: str = None) -> Dict[str, Any]:
        """Extract metadata from image and PDF documents using vision API"""
        try:
            prompt = f"""
            You are an advanced document analysis AI. Your task is to analyze this document (image or PDF) and extract ALL information visible in the document.
            
            Filename: {filename}
            Folder: {folder_name or 'Unknown'}
            
            MANDATORY REQUIREMENTS:
            1. SCAN EVERY ELEMENT: Look at every part of the document
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
            - For government IDs (passport, military id, green card, driver license), PAY SPECIAL ATTENTION to expiry and issue dates and card numbers
            - On US Permanent Resident Cards ("Green Card"), specifically extract fields labeled "Card Expires", "Resident Since", "Category", and the A-number (Alien Registration Number)
            
            HARD CONSTRAINTS (no exceptions):
            - Never invent values. Only return fields that are visibly present.
            - Transcribe text VERBATIM, including letter-case, hyphens and spacing.
            - If a field is not clearly visible, set it to null and add a warning in "warnings".
            - Prefer machine-readable values but do not convert numbers that appear with separators.

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
                "action_items": ["ALL action items, tasks, requirements, and next steps visible"],
                "verbatim_extracted_text": "ALL text transcribed line-by-line as seen",
                "key_value_pairs": {"Auto-detected labeled fields mapped to values (e.g., 'Surname': 'STEVENS')"},
                "tables": [{"caption": "optional", "headers": ["..."], "rows": [["..."]] }],
                "warnings": ["list any uncertainty or missing fields"]
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
            
            selected_model = model_override or self.model
            message = self.client.messages.create(
                model=selected_model,
                max_tokens=4000,
                temperature=0.0,
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
                                    "media_type": "image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "image/png",
                                    "data": file_base64
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
                metadata['ai_model'] = selected_model
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
                
                # Post-process dates if green card-like document
                metadata = self._normalize_and_enhance_metadata(metadata)
                # If result is sparse, retry with fallback model and stricter schema (esp. for IDs/passports)
                if self._is_sparse_metadata(metadata):
                    strict_extra = """
                    IMPORTANT: The initial pass returned sparse data. You MUST extract detailed, verbatim content.
                    When the document appears to be an ID (passport, driver license, green card, military ID), populate key_value_pairs with:
                    - passport_number / id_number
                    - surname
                    - given_names
                    - nationality
                    - date_of_birth (YYYY-MM-DD)
                    - sex
                    - place_of_birth
                    - date_of_issue (YYYY-MM-DD)
                    - date_of_expiry (YYYY-MM-DD)
                    - issuing_country / authority
                    - mrz_lines (array of MRZ lines if present)
                    Do NOT omit fields if visible. Transcribe exactly as printed.
                    """
                    retry_prompt = prompt + "\n\n" + strict_extra
                    retry_msg = self.client.messages.create(
                        model=self.fallback_model,
                        max_tokens=4000,
                        temperature=0.0,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": retry_prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else "image/png",
                                            "data": file_base64
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                    retry_text = retry_msg.content[0].text.strip()
                    try:
                        retry_metadata = json.loads(retry_text)
                    except Exception:
                        # attempt minimal cleanup
                        import re
                        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', retry_text)
                        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                        retry_metadata = json.loads(cleaned)
                    retry_metadata['extracted_at'] = datetime.utcnow().isoformat()
                    retry_metadata['ai_model'] = self.fallback_model
                    retry_metadata['processing_status'] = 'success'
                    retry_metadata = self._normalize_and_enhance_metadata(retry_metadata)
                    return retry_metadata
                return metadata
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"❌ JSON Parse Error: {e}")
                print(f"❌ Response text: {response_text}")
                # Try to clean the response
                try:
                    import re
                    # Remove control characters and fix common JSON issues
                    cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
                    # Fix common JSON issues
                    cleaned_response = cleaned_response.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    # Remove any trailing commas before closing braces/brackets
                    cleaned_response = re.sub(r',(\s*[}\]])', r'\1', cleaned_response)
                    metadata = json.loads(cleaned_response)
                    print(f"🔍 JSON parsed after cleaning!")
                    metadata = self._normalize_and_enhance_metadata(metadata)
                    return metadata
                except Exception as clean_error:
                    print(f"❌ JSON cleaning failed: {clean_error}")
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
            - For government IDs and forms, ensure you extract clearly labeled fields (expiry, issue date, ID numbers)
            
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
                
                metadata = self._normalize_and_enhance_metadata(metadata)
                return metadata
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                print(f"❌ JSON Parse Error: {e}")
                print(f"❌ Response text: {response_text}")
                # Try to clean the response
                try:
                    import re
                    # Remove control characters and fix common JSON issues
                    cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
                    # Fix common JSON issues
                    cleaned_response = cleaned_response.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    # Remove any trailing commas before closing braces/brackets
                    cleaned_response = re.sub(r',(\s*[}\]])', r'\1', cleaned_response)
                    metadata = json.loads(cleaned_response)
                    print(f"🔍 JSON parsed after cleaning!")
                    metadata = self._normalize_and_enhance_metadata(metadata)
                    return metadata
                except Exception as clean_error:
                    print(f"❌ JSON cleaning failed: {clean_error}")
                    return self._create_fallback_metadata(filename, folder_name, f"JSON parse error: {e}", f"JSON parse error: {e}")
                
        except Exception as e:
            # Fallback metadata if extraction fails
            print(f"❌ Text API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_metadata(filename, folder_name, str(e), str(e))

    def _normalize_and_enhance_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Improve metadata by extracting dates from text when model misses them, and set urgency.
        Keeps existing values if already provided.
        """
        try:
            # Ensure processing flags
            metadata.setdefault('processing_status', 'success')
            extracted_text = metadata.get('extracted_text') or ''

            # If expiry not detected, try simple regex over text
            if not metadata.get('expiry_detected'):
                import re
                # Match common US date formats
                date_candidates = re.findall(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4})\b", extracted_text)
                # Prefer lines containing keywords
                labelled = re.findall(r"(Card\s*Expires|Expiration|Expiry)[^\n\r]*?(\d{2}[\/-]\d{2}[\/-]\d{4})", extracted_text, flags=re.IGNORECASE)
                chosen = None
                if labelled:
                    chosen = labelled[0][1]
                elif date_candidates:
                    # Heuristic: take the latest date as expiry
                    from datetime import datetime
                    def parse_date(d):
                        for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
                            try:
                                return datetime.strptime(d, fmt)
                            except Exception:
                                continue
                        return None
                    parsed = [(d, parse_date(d)) for d in date_candidates]
                    parsed = [p for p in parsed if p[1] is not None]
                    if parsed:
                        chosen = max(parsed, key=lambda x: x[1])[0]
                if chosen:
                    # Normalize to YYYY-MM-DD
                    from datetime import datetime
                    for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
                        try:
                            dt = datetime.strptime(chosen, fmt)
                            metadata['expiry_date'] = dt.date().isoformat()
                            metadata['expiry_detected'] = True
                            break
                        except Exception:
                            continue

            # Set urgency if we have an expiry date
            if metadata.get('expiry_detected') and metadata.get('expiry_date'):
                from datetime import date, datetime as dtt
                try:
                    exp = dtt.strptime(metadata['expiry_date'], "%Y-%m-%d").date()
                    days = (exp - date.today()).days
                    if days < 30:
                        metadata['urgency_level'] = 'high'
                    elif days < 90:
                        metadata['urgency_level'] = 'medium'
                    else:
                        metadata['urgency_level'] = 'low'
                except Exception:
                    pass
        except Exception as e:
            print(f"Normalization error: {e}")
        return metadata
    
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
