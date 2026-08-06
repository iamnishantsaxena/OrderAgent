"""
Test script for Order Extraction Agent
Tests the agent with sample inputs
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import OrderExtractionAgent


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result_summary(result: dict):
    """Print a summary of the extraction result"""
    print(f"✓ Can Create Order: {result['can_create_order']}")
    print(f"✓ Confidence: {result['confidence']:.2%}")
    print(f"✓ Missing Fields: {', '.join(result['missing_fields']) if result['missing_fields'] else 'None'}")
    print(f"\nOrder Details:")
    print(f"  - Customer: {result['order'].get('customer_name', 'N/A')}")
    print(f"  - Items: {len(result['order'].get('items', []))}")
    print(f"  - Total: ${result['order'].get('total_amount', 0):.2f} {result['order'].get('currency', 'USD')}")
    
    if result['order'].get('items'):
        print(f"\nItems:")
        for idx, item in enumerate(result['order']['items'], 1):
            print(f"  {idx}. {item['name']} - Qty: {item['quantity']} @ ${item.get('price', 0):.2f}")


def test_sample_file(agent: OrderExtractionAgent, file_path: Path):
    """Test a sample input file"""
    print_section(f"Testing: {file_path.name}")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Input length: {len(text)} characters\n")
        
        # Extract order
        print("Extracting order...")
        result = agent.extract_order(text, source_type="text")
        
        # Print summary
        print_result_summary(result)
        
        # Save result
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{file_path.stem}_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✓ Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print_section("Order Extraction Agent - Test Suite")
    
    # Initialize agent
    print("Initializing agent...")
    try:
        agent = OrderExtractionAgent(
            model_name="llama3.2:latest",
            temperature=0.1,
            verbose=False
        )
        print("✓ Agent initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        print("\nMake sure:")
        print("1. Ollama is running (check with: ollama list)")
        print("2. llama3.2:latest is installed (run: ollama pull llama3.2:latest)")
        return
    
    # Get sample files
    sample_dir = Path(__file__).parent / "sample_inputs"
    sample_files = list(sample_dir.glob("*.txt"))
    
    if not sample_files:
        print("✗ No sample files found in tests/sample_inputs/")
        return
    
    print(f"Found {len(sample_files)} sample files\n")
    
    # Test each sample
    results = []
    for sample_file in sorted(sample_files):
        success = test_sample_file(agent, sample_file)
        results.append((sample_file.name, success))
        print()  # Blank line between tests
    
    # Final summary
    print_section("Test Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    for filename, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {filename}")
    
    print()
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
