"""
Email Order Parser Agent using LangChain with Ollama (Free, CPU-optimized for macOS)
Parses email text and creates structured order JSON
"""

from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import re


# Define the order structure using Pydantic
class OrderItem(BaseModel):
    """Individual item in an order"""
    product_name: str = Field(description="Name of the product")
    quantity: int = Field(description="Quantity ordered")
    unit_price: Optional[float] = Field(description="Price per unit", default=None)


class Order(BaseModel):
    """Complete order structure"""
    customer_name: str = Field(description="Name of the customer")
    customer_email: Optional[str] = Field(description="Email of the customer", default=None)
    customer_phone: Optional[str] = Field(description="Phone number", default=None)
    delivery_address: Optional[str] = Field(description="Delivery address", default=None)
    items: List[OrderItem] = Field(description="List of items in the order")
    special_instructions: Optional[str] = Field(description="Any special instructions", default=None)
    total_amount: Optional[float] = Field(description="Total order amount", default=None)


class EmailOrderParser:
    """Agent to parse email text and extract order information using Ollama"""
    
    def __init__(self, 
                 model_name: str = "llama3.2",
                 base_url: str = "http://localhost:11434"):
        """
        Initialize the parser with LangChain and Ollama
        
        Args:
            model_name: Name of the Ollama model to use
                       Recommended for macOS CPU:
                       - "llama3.2" (3B) - Fast, good quality
                       - "llama3.2:1b" - Very fast, lighter
                       - "phi3" - Microsoft's efficient model
                       - "mistral" (7B) - Better quality, slower
                       - "gemma2:2b" - Google's efficient model
            base_url: Ollama server URL (default: localhost)
        """
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,
            num_predict=1024  # Max tokens to generate
        )
        
        # Set up the output parser
        self.parser = JsonOutputParser(pydantic_object=Order)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_template("""You are an expert at extracting order information from emails.
Extract all relevant order details from the email text and return ONLY a valid JSON object.

Required JSON structure:
{{
  "customer_name": "string",
  "customer_email": "string or null",
  "customer_phone": "string or null",
  "delivery_address": "string or null",
  "items": [
    {{
      "product_name": "string",
      "quantity": number,
      "unit_price": number or null
    }}
  ],
  "special_instructions": "string or null",
  "total_amount": number or null
}}

Instructions:
- Extract customer name, contact details, and delivery address
- Identify ALL product items with quantities and prices
- Use null for missing information
- Calculate total_amount if prices are available
- Return ONLY valid JSON, no explanations

Email text:
{email_text}

JSON:""")
        
        # Create the chain
        self.chain = self.prompt | self.llm
    
    def _clean_json_response(self, response: str) -> str:
        """Clean the LLM response to extract valid JSON"""
        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Remove any text before the first {
        start_idx = response.find('{')
        if start_idx != -1:
            response = response[start_idx:]
        
        # Remove any text after the last }
        end_idx = response.rfind('}')
        if end_idx != -1:
            response = response[:end_idx + 1]
        
        return response.strip()
    
    def parse_email(self, email_text: str) -> dict:
        """
        Parse email text and return structured order JSON
        
        Args:
            email_text: Raw email text containing order information
            
        Returns:
            Dictionary containing structured order data
        """
        try:
            # Get response from LLM
            response = self.chain.invoke({"email_text": email_text})
            
            # Clean and parse JSON
            cleaned_response = self._clean_json_response(response)
            order = json.loads(cleaned_response)
            
            # Validate structure
            if not isinstance(order, dict):
                raise ValueError("Response is not a valid JSON object")
            
            return order
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Cleaned response: {cleaned_response if 'cleaned_response' in locals() else 'N/A'}")
            return {
                "error": "Failed to parse JSON from LLM response",
                "raw_response": response if 'response' in locals() else None,
                "raw_text": email_text
            }
        except Exception as e:
            return {
                "error": str(e),
                "raw_text": email_text
            }


# Example usage
if __name__ == "__main__":
    # Sample email text
    sample_email = """
    Hi there,
    
    I'd like to place an order for delivery to 123 Main Street, Springfield.
    
    My name is John Doe and you can reach me at john.doe@email.com or 555-0123.
    
    I need:
    - 3 boxes of Premium Coffee Beans at $15.99 each
    - 1 Coffee Grinder at $45.00
    - 2 Ceramic Mugs at $12.50 each
    
    Please deliver between 2-5 PM if possible. Also, please leave the package at the 
    back door if I'm not home.
    
    Thanks!
    John
    """
    
    print("=" * 60)
    print("EMAIL ORDER PARSER - Using Ollama on macOS CPU")
    print("=" * 60)
    print("\nMake sure Ollama is installed and running:")
    print("1. Install: brew install ollama")
    print("2. Start: ollama serve")
    print("3. Pull model: ollama pull llama3.2")
    print("=" * 60)
    
    # Initialize parser with a CPU-efficient model
    # Using qwen2.5:1.5b-instruct (fast and efficient for macOS)
    parser = EmailOrderParser(model_name="qwen2.5:1.5b-instruct-q4_1")
    
    # Alternative models you have:
    # parser = EmailOrderParser(model_name="llama2:latest")  # Larger, better quality but slower
    # parser = EmailOrderParser(model_name="qwen2.5-coder:1.5b-base-q4_K_M")  # For code-related tasks
    
    # Parse the email
    print("\nParsing email...\n")
    order = parser.parse_email(sample_email)
    
    # Display the result
    print("=" * 60)
    print("EXTRACTED ORDER:")
    print("=" * 60)
    print(json.dumps(order, indent=2))
    print("=" * 60)
    
    # Example: Process the order
    if "error" not in order:
        print(f"\n✓ Order successfully parsed!")
        print(f"  Customer: {order.get('customer_name')}")
        print(f"  Items: {len(order.get('items', []))}")
        
        total = order.get('total_amount')
        if total is not None:
            print(f"  Total: ${total:.2f}")
        else:
            # Calculate total from items if not provided
            items = order.get('items', [])
            calculated_total = sum(
                item.get('quantity', 0) * item.get('unit_price', 0) 
                for item in items 
                if item.get('unit_price') is not None
            )
            if calculated_total > 0:
                print(f"  Total: ${calculated_total:.2f} (calculated)")
            else:
                print(f"  Total: Not available")
    else:
        print(f"\n✗ Error: {order['error']}")