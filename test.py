"""
Test script for the Document QA System
"""

import os
from app.utils.testing import run_test_suite

if __name__ == "__main__":
    print("Document QA System Test Script")
    print("=============================")
    
    # Check if the API is running
    print("Testing API connection...")
    run_test_suite()
    
    # Optionally test with a document
    test_file = input("\nEnter path to a test document (or press Enter to skip): ").strip()
    if test_file and os.path.exists(test_file):
        print(f"\nTesting with document: {test_file}")
        run_test_suite(test_file)
    elif test_file:
        print(f"File not found: {test_file}")
