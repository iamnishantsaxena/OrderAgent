"""
LLM Prompts for Order Extraction
Contains the prompt template used by the agent
"""

EXTRACTION_PROMPT = """Extract order information from the following input. Be precise and only extract what is clearly stated.

Input Text:
{input_text}

Instructions:
1. Identify customer information (name, company, email, phone)
2. Extract all items mentioned with their quantities and prices
3. Find addresses (shipping and billing)
4. Extract dates (order date, delivery date)
5. Identify payment terms and financial information
6. Extract reference numbers (PO, invoice, order numbers)
7. Note any special instructions or comments

For each field you extract, mentally assess your confidence:
- HIGH (0.8-1.0): Information is explicitly stated and clear
- MEDIUM (0.5-0.7): Information is implied or partially stated
- LOW (0.0-0.4): Information is ambiguous or uncertain

Output Format:
Provide a JSON object with the following structure:
{{
  "customer_name": "extracted name or null",
  "customer_email": "extracted email or null",
  "customer_phone": "extracted phone or null",
  "company_name": "extracted company or null",
  "items": [
    {{
      "name": "item name",
      "quantity": number,
      "price": number or null,
      "unit": "unit type"
    }}
  ],
  "shipping_address": "full address or null",
  "billing_address": "full address or null",
  "order_date": "YYYY-MM-DD or null",
  "delivery_date": "YYYY-MM-DD or null",
  "payment_terms": "terms or null",
  "total_amount": number or null,
  "currency": "USD/EUR/etc",
  "order_number": "PO/order number or null",
  "notes": "any special instructions or null",
  "confidence_scores": {{
    "customer_name": 0.0-1.0,
    "items": 0.0-1.0,
    "addresses": 0.0-1.0
  }}
}}

Remember: Only extract what is present. Use null for missing information."""


def get_extraction_prompt(input_text: str) -> str:
    """Get the main extraction prompt with input filled in"""
    return EXTRACTION_PROMPT.format(input_text=input_text)
