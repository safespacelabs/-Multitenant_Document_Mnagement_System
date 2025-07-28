#!/usr/bin/env python3
"""
Test script to verify the system admin AI assistant is working properly.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.nlp_service import nlp_service
from app.database import get_management_db
from app.config import ANTHROPIC_API_KEY
import asyncio

def test_system_ai():
    """Test the system admin AI assistant"""
    
    print("🧪 Testing System Admin AI Assistant...")
    print("=" * 50)
    
    # Check if API key is configured
    if not ANTHROPIC_API_KEY:
        print("❌ ERROR: ANTHROPIC_API_KEY is not set!")
        print("Please set the ANTHROPIC_API_KEY environment variable.")
        return False
    
    print("✅ Anthropic API key is configured")
    
    # Test database connection
    try:
        db_gen = get_management_db()
        db = next(db_gen)
        
        # Test with sample queries
        test_queries = [
            "Show me system status",
            "How many companies are active?",
            "What can you help me with?",
            "Give me system statistics"
        ]
        
        print("\n🤖 Testing AI responses...")
        print("-" * 30)
        
        for query in test_queries:
            try:
                print(f"\n❓ Query: {query}")
                response = nlp_service.process_system_query(query, "test_user", db)
                print(f"🤖 Response: {response[:200]}...")
                
                # Check if response is not empty
                if response and len(response) > 10:
                    print("✅ Response generated successfully")
                else:
                    print("❌ Response too short or empty")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                
        db.close()
        print("\n✅ System AI Assistant test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_system_ai()
    sys.exit(0 if success else 1) 