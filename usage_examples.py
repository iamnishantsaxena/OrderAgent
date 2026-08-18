"""
Example: Using the Order Extraction Agent Programmatically

This script demonstrates how to use the agent in your own code
"""

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import OrderExtractionPipeline
from src.database import OrderDatabase


def example_1_basic_extraction():
    """Example 1: Basic text extraction"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Text Extraction")
    print("=" * 80 + "\n")
    
    # Initialize agent
    agent = OrderExtractionPipeline()
    
    # Sample order text
    text = """
    Order from: Tech Solutions Inc.
    Contact: Sarah Chen (sarah@techsolutions.com)
    
    Items:
    - 5 Laptops @ $1200 each
    - 5 Wireless Mice @ $50 each
    
    Ship to:
    123 Tech Street
    San Francisco, CA 94105
    
    Total: $6,250
    Payment: Net 30
    """
    
    # Extract order
    result = agent.extract_order(text)
    
    # Display results
    print(f"Order Valid: {result['can_create_order']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Customer: {result['order']['customer_name']}")
    print(f"Items: {len(result['order']['items'])}")
    print(f"Total: ${result['order']['total_amount']}")
    print()


def example_2_pdf_processing():
    """Example 2: Processing PDF file"""
    print("=" * 80)
    print("EXAMPLE 2: PDF Processing")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    
    # Check if sample PDF exists
    pdf_path = Path("tests/sample_inputs/sample_invoice.pdf")
    
    if pdf_path.exists():
        # Process PDF
        result = agent.process_pdf(pdf_path)
        
        print(f"PDF Pages: {result['extraction_metadata'].get('pdf_info', {}).get('num_pages', 'N/A')}")
        print(f"Order Valid: {result['can_create_order']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print()
    else:
        print("Sample PDF not found. Skipping PDF example.")
        print()


def example_3_streaming():
    """Example 3: Streaming extraction with progress updates"""
    print("=" * 80)
    print("EXAMPLE 3: Streaming Extraction")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    
    text = """
    Purchase Order: PO-2024-123
    From: Acme Corporation
    Contact: John Doe (john@acme.com)
    
    Order:
    10 Widget A @ $25 = $250
    5 Widget B @ $50 = $250
    
    Total: $500
    Ship to: 456 Business Ave, City, State 12345
    """
    
    # Process with streaming
    print("Processing with streaming updates:\n")
    
    for update in agent.extract_order_streaming(text):
        status = update.get("status")
        
        if status == "starting":
            print("→ Starting extraction...")
        
        elif status in ["extracting", "refining", "validating", "scoring", "finalizing"]:
            print(f"→ {update.get('message')}")
        
        elif status == "complete":
            result = update.get("result")
            print("\n✓ Extraction complete!")
            print(f"  Order Valid: {result['can_create_order']}")
            print(f"  Confidence: {result['confidence']:.2%}")
        
        elif status == "error":
            print(f"\n✗ Error: {update.get('error')}")
    
    print()


def example_4_database_storage():
    """Example 4: Storing results in database"""
    print("=" * 80)
    print("EXAMPLE 4: Database Storage")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    db = OrderDatabase("database/example_orders.db")
    
    # Extract order
    text = """
    Order from: Jane Smith
    Email: jane@example.com
    3 Tablets @ $600 = $1800
    Ship to: 789 Customer Lane, Town, State 67890
    """
    
    result = agent.extract_order(text)
    
    # Save to database
    order_id = db.save_order(result)
    print(f"✓ Order saved with ID: {order_id}")
    
    # Retrieve order
    saved_order = db.get_order(order_id)
    print(f"✓ Retrieved order: {saved_order['customer_name']}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total Orders: {stats['total_orders']}")
    print(f"  Valid Orders: {stats['valid_orders']}")
    print(f"  Total Value: ${stats['total_value']:.2f}")
    print(f"  Avg Confidence: {stats['avg_confidence']:.2%}")
    
    db.close()
    print()


def example_5_batch_processing():
    """Example 5: Batch processing multiple orders"""
    print("=" * 80)
    print("EXAMPLE 5: Batch Processing")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    
    # Multiple orders
    orders = [
        "Order: 5 laptops @ $1000, Customer: Alice",
        "Order: 10 mice @ $50, Customer: Bob",
        "Order: 3 monitors @ $300, Customer: Charlie"
    ]
    
    results = []
    
    print("Processing batch of orders:\n")
    for idx, text in enumerate(orders, 1):
        print(f"Processing order {idx}/{len(orders)}...", end=" ")
        result = agent.extract_order(text)
        results.append(result)
        
        if result['can_create_order']:
            print(f"✓ Valid (Confidence: {result['confidence']:.0%})")
        else:
            print(f"✗ Invalid")
    
    # Summary
    valid_count = sum(1 for r in results if r['can_create_order'])
    total_value = sum(r['order']['total_amount'] or 0 for r in results)
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    
    print(f"\nBatch Summary:")
    print(f"  Valid Orders: {valid_count}/{len(orders)}")
    print(f"  Total Value: ${total_value:.2f}")
    print(f"  Avg Confidence: {avg_confidence:.2%}")
    print()


def example_6_custom_validation():
    """Example 6: Custom validation logic"""
    print("=" * 80)
    print("EXAMPLE 6: Custom Validation")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    
    text = "Order: 100 expensive items @ $10000 each from Suspicious Customer"
    
    result = agent.extract_order(text)
    
    # Custom validation rules
    order = result['order']
    warnings = []
    
    # Check for large orders
    if order['total_amount'] and order['total_amount'] > 50000:
        warnings.append("⚠️ Large order - requires manager approval")
    
    # Check for missing contact info
    if not order['customer_email'] and not order['customer_phone']:
        warnings.append("⚠️ No contact information - cannot confirm order")
    
    # Check for missing address
    if not order['shipping_address']:
        warnings.append("⚠️ No shipping address provided")
    
    # Display results
    print(f"Order Extracted: {result['can_create_order']}")
    print(f"Custom Validation Warnings:")
    for warning in warnings:
        print(f"  {warning}")
    
    if warnings:
        print("\n→ Order requires manual review")
    else:
        print("\n✓ Order passed all validations")
    print()


def example_7_confidence_filtering():
    """Example 7: Filtering by confidence threshold"""
    print("=" * 80)
    print("EXAMPLE 7: Confidence-Based Filtering")
    print("=" * 80 + "\n")
    
    agent = OrderExtractionPipeline()
    
    # Orders with varying clarity
    test_orders = [
        "Clear order: 5 laptops @ $1000 from john@email.com",
        "Maybe order? Something something 5 things",
        "Urgent! Need 10 widgets ASAP - contact Sarah at acme corp"
    ]
    
    confidence_threshold = 0.6
    
    print(f"Filtering orders with confidence >= {confidence_threshold:.0%}\n")
    
    accepted = []
    rejected = []
    
    for idx, text in enumerate(test_orders, 1):
        result = agent.extract_order(text)
        confidence = result['confidence']
        
        if confidence >= confidence_threshold:
            accepted.append(result)
            print(f"✓ Order {idx}: ACCEPTED (Confidence: {confidence:.0%})")
        else:
            rejected.append(result)
            print(f"✗ Order {idx}: REJECTED (Confidence: {confidence:.0%})")
    
    print(f"\nResults:")
    print(f"  Accepted: {len(accepted)}")
    print(f"  Rejected: {len(rejected)}")
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Order Extraction Agent Examples" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        # Run examples
        example_1_basic_extraction()
        example_2_pdf_processing()
        example_3_streaming()
        example_4_database_storage()
        example_5_batch_processing()
        example_6_custom_validation()
        example_7_confidence_filtering()
        
        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
