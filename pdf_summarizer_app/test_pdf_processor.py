#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.pdf_processor import PDFProcessor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile

def create_test_pdf():
    """Create a simple test PDF for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Create a simple PDF with some text
    c = canvas.Canvas(temp_path, pagesize=letter)
    width, height = letter
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Test Document: AI and Machine Learning")
    
    # Add content
    c.setFont("Helvetica", 12)
    content = [
        "This is a test document about artificial intelligence and machine learning.",
        "Machine learning is a subset of artificial intelligence that focuses on algorithms",
        "that can learn and make decisions from data without being explicitly programmed.",
        "",
        "Key benefits of machine learning include:",
        "- Automated decision making",
        "- Pattern recognition in large datasets", 
        "- Predictive analytics capabilities",
        "- Improved efficiency in data processing",
        "",
        "Important considerations when implementing machine learning solutions:",
        "Data quality is critical for successful machine learning implementations.",
        "Model training requires significant computational resources and time.",
        "Regular model validation and testing is essential for maintaining accuracy.",
        "",
        "In conclusion, machine learning represents a significant advancement in",
        "computational capabilities and offers tremendous potential for solving",
        "complex problems across various industries and applications."
    ]
    
    y_position = height - 150
    for line in content:
        c.drawString(100, y_position, line)
        y_position -= 20
    
    c.save()
    return temp_path

def test_pdf_processor():
    """Test the PDF processor functionality."""
    print("Testing PDF Processor...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    print(f"Created test PDF: {test_pdf_path}")
    
    try:
        # Initialize processor
        processor = PDFProcessor()
        
        # Process the PDF
        result = processor.process_pdf(test_pdf_path, "test_document.pdf")
        
        print("\n=== PDF Processing Results ===")
        print(f"Title: {result['title']}")
        print(f"\nSummary: {result['summary']}")
        print(f"\nKey Messages:")
        for i, message in enumerate(result['key_messages'], 1):
            print(f"{i}. {message}")
        
        print(f"\nText Length: {len(result['text'])} characters")
        print(f"First 200 characters of text: {result['text'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error testing PDF processor: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists(test_pdf_path):
            os.unlink(test_pdf_path)

if __name__ == "__main__":
    success = test_pdf_processor()
    if success:
        print("\n✅ PDF Processor test completed successfully!")
    else:
        print("\n❌ PDF Processor test failed!")
        sys.exit(1)

