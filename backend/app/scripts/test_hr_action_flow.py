"""
Test Script: HR Action Flow Testing

Tests the complete agentic flow for HR chatbot actions:
1. Intent detection
2. Parameter extraction (regex and AI)
3. Confirmation flow
4. Action execution

Usage:
    cd backend
    python -m app.scripts.test_hr_action_flow
"""

import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from app.services.hr_action_service import HRActionService, hr_action_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test queries for user creation
USER_CREATION_TEST_QUERIES = [
    # Clear intent queries
    "Create a new user for John Smith with email john.smith@example.com as an employee",
    "Add user Jane Doe jane.doe@company.com",
    "I need to create an account for Michael Johnson michael.j@test.org as hr manager",
    "Please add a new employee named Sarah Williams sarah.w@firm.com",

    # Natural language queries
    "Can you create a user for alex brown? His email is alex.brown@startup.io",
    "I want to onboard emily davis as a new hire, her email is emily.d@corp.com",
    "Set up a new user account for Robert Chen, email: robert.chen@business.net, role should be viewer",

    # Minimal info queries
    "Create user test@example.com",
    "Add employee john.doe@company.com",

    # Complex queries
    "We have a new hire starting Monday - Lisa Anderson, lisa.a@enterprise.com, she'll be an HR admin",
    "Please create an account for our new team member David Kim (david.kim@techfirm.com) as an employee",
]

# Test queries for document upload
DOC_UPLOAD_TEST_QUERIES = [
    "Upload a passport for John Smith",
    "Add the I9 form for employee Jane Doe",
    "I need to upload a driver's license for Michael Johnson",
    "Store a contract document for Sarah Williams in the contracts folder",
    "Upload resume for alex.brown@startup.io",
]

# Non-action queries (should NOT trigger action flow)
NON_ACTION_QUERIES = [
    "How many employees do we have?",
    "Show me expiring documents",
    "What is the status of John's I9 form?",
    "List all users in the system",
]


async def test_intent_detection():
    """Test intent detection for various queries"""
    print("\n" + "=" * 60)
    print("TESTING INTENT DETECTION")
    print("=" * 60)

    service = HRActionService()

    print("\n--- User Creation Queries (should detect 'create_user') ---")
    for query in USER_CREATION_TEST_QUERIES[:5]:
        result = await service.detect_intent(query, 'hr_admin')
        intent = result.get('intent')
        confidence = result.get('confidence', 0)
        status = "[OK]" if intent == 'create_user' else "[FAIL]"
        print(f"{status} Intent: {intent or 'None'} (conf: {confidence:.2f}) - \"{query[:50]}...\"")

    print("\n--- Document Upload Queries (should detect 'upload_document') ---")
    for query in DOC_UPLOAD_TEST_QUERIES[:3]:
        result = await service.detect_intent(query, 'hr_admin')
        intent = result.get('intent')
        confidence = result.get('confidence', 0)
        status = "[OK]" if intent == 'upload_document' else "[FAIL]"
        print(f"{status} Intent: {intent or 'None'} (conf: {confidence:.2f}) - \"{query[:50]}...\"")

    print("\n--- Non-Action Queries (should NOT detect any intent) ---")
    for query in NON_ACTION_QUERIES:
        result = await service.detect_intent(query, 'hr_admin')
        intent = result.get('intent')
        status = "[OK]" if intent is None else "[FAIL]"
        print(f"{status} Intent: {intent or 'None'} - \"{query[:50]}...\"")


async def test_user_param_extraction():
    """Test user parameter extraction"""
    print("\n" + "=" * 60)
    print("TESTING USER PARAMETER EXTRACTION")
    print("=" * 60)

    service = HRActionService()

    print("\n--- Regex-based Extraction ---")
    for query in USER_CREATION_TEST_QUERIES[:5]:
        params = service._extract_user_params_regex(query)
        print(f"\nQuery: \"{query[:60]}...\"")
        print(f"  Name: {params.get('full_name')}")
        print(f"  Email: {params.get('email')}")
        print(f"  Role: {params.get('role')}")
        print(f"  Username: {params.get('username')}")

    if service.anthropic_client:
        print("\n--- AI-powered Extraction ---")
        for query in USER_CREATION_TEST_QUERIES[:3]:
            try:
                params = await service._extract_user_params_with_ai(query)
                print(f"\nQuery: \"{query[:60]}...\"")
                print(f"  Name: {params.get('full_name')}")
                print(f"  Email: {params.get('email')}")
                print(f"  Role: {params.get('role')}")
                print(f"  Username: {params.get('username')}")
            except Exception as e:
                print(f"\nQuery: \"{query[:60]}...\"")
                print(f"  Error: {e}")
    else:
        print("\n--- AI-powered Extraction (SKIPPED - Anthropic not available) ---")


async def test_full_extraction():
    """Test the full extraction pipeline (AI with regex fallback)"""
    print("\n" + "=" * 60)
    print("TESTING FULL EXTRACTION PIPELINE")
    print("=" * 60)

    service = HRActionService()

    for query in USER_CREATION_TEST_QUERIES:
        params = await service.extract_user_params(query)
        status = "[OK]" if params.get('email') or params.get('full_name') else "[FAIL]"
        print(f"\n{status} Query: \"{query[:60]}...\"")
        print(f"   Name: {params.get('full_name') or 'NOT FOUND'}")
        print(f"   Email: {params.get('email') or 'NOT FOUND'}")
        print(f"   Role: {params.get('role')}")
        print(f"   Username: {params.get('username') or 'NOT GENERATED'}")


async def test_confirmation_message_generation():
    """Test confirmation message generation"""
    print("\n" + "=" * 60)
    print("TESTING CONFIRMATION MESSAGE GENERATION")
    print("=" * 60)

    service = HRActionService()

    # Test user creation confirmation
    params = {
        'full_name': 'John Smith',
        'email': 'john.smith@example.com',
        'role': 'employee',
        'username': 'john_smith'
    }
    msg = service._generate_user_creation_confirmation(params)
    print("\n--- User Creation Confirmation ---")
    print(msg)

    # Test with missing email
    params_no_email = {
        'full_name': 'Jane Doe',
        'email': None,
        'role': 'hr_manager',
        'username': 'jane_doe'
    }
    msg = service._generate_user_creation_confirmation(params_no_email)
    print("\n--- User Creation (Missing Email) ---")
    print(msg)


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("HR ACTION FLOW TEST SUITE")
    print("=" * 70)

    await test_intent_detection()
    await test_user_param_extraction()
    await test_full_extraction()
    await test_confirmation_message_generation()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)


async def interactive_test():
    """Interactive testing mode"""
    print("\n" + "=" * 60)
    print("INTERACTIVE HR ACTION TEST")
    print("=" * 60)
    print("Enter HR commands to test (type 'quit' to exit)")
    print("Examples:")
    print("  - Create user John Doe john@example.com as employee")
    print("  - Upload passport for Jane Smith")
    print("=" * 60)

    service = HRActionService()

    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            # Detect intent
            intent_result = await service.detect_intent(query, 'hr_admin')
            print(f"\nIntent: {intent_result.get('intent')} (confidence: {intent_result.get('confidence', 0):.2f})")

            if intent_result.get('intent') == 'create_user':
                params = await service.extract_user_params(query)
                print(f"\nExtracted Parameters:")
                print(f"  Name: {params.get('full_name')}")
                print(f"  Email: {params.get('email')}")
                print(f"  Role: {params.get('role')}")
                print(f"  Username: {params.get('username')}")

                msg = service._generate_user_creation_confirmation(params)
                print(f"\nConfirmation Message:")
                print(msg)

            elif intent_result.get('intent') == 'upload_document':
                print("\n[Document upload flow - would need database connection]")

            else:
                print("\n[No actionable intent detected - would route to normal chat]")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test HR Action Flow')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--intent', action='store_true', help='Test intent detection only')
    parser.add_argument('--extraction', action='store_true', help='Test parameter extraction only')

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_test())
    elif args.intent:
        asyncio.run(test_intent_detection())
    elif args.extraction:
        asyncio.run(test_full_extraction())
    else:
        asyncio.run(run_all_tests())
