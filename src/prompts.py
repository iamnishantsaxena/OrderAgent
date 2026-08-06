"""
LLM Prompts for Order Extraction
Contains all prompt templates used by the agent
"""

SYSTEM_PROMPT = """You are an expert order processing assistant. Your job is to extract structured order information from unstructured text, emails, or documents.

You have access to tools that help you:
1. Extract specific fields from text
2. Validate extracted data
3. Calculate confidence scores

Guidelines:
- Be thorough but concise
- Only extract information that is explicitly present
- Don't make assumptions or hallucinate data
- If information is ambiguous, note it with low confidence
- Pay attention to units, currencies, and quantities
- Distinguish between shipping and billing addresses
- Extract dates in YYYY-MM-DD format when possible

Critical fields needed for a valid order:
- Customer name or company name
- At least one item with name and quantity

Nice-to-have fields:
- Contact information (email, phone)
- Addresses
- Payment terms
- Dates
- Reference numbers"""


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


FIELD_EXTRACTION_PROMPT = """Extract the following specific field from the text:

Field to extract: {field_name}
Description: {field_description}

Text:
{text}

Instructions:
- Extract only the {field_name}
- Return null if not found
- Be precise and don't include extra information
- For numerical fields, return only the number
- For date fields, use YYYY-MM-DD format

Response:"""


VALIDATION_PROMPT = """Validate the following extracted order data:

Extracted Order:
{order_data}

Validation Checks:
1. Are all critical fields present? (customer_name, items)
2. Are numerical values reasonable? (no negative quantities, realistic prices)
3. Are dates in valid format?
4. Are items properly structured?
5. Is there any contradictory information?

Respond with:
{{
  "is_valid": true/false,
  "issues": ["list of issues found"],
  "suggestions": ["suggestions to fix issues"],
  "confidence": 0.0-1.0
}}"""


ITEM_EXTRACTION_PROMPT = """Extract all items/products from the following text. Focus on finding:
- Product names
- Quantities (numbers)
- Prices (if mentioned)
- Units (pcs, kg, boxes, etc.)

Text:
{text}

Look for patterns like:
- "5 laptops at $1000 each"
- "10kg of coffee beans"
- "Product X, qty: 20"
- "2 boxes of widgets - $50/box"

Extract each item as:
{{
  "name": "product name",
  "quantity": number,
  "price": number or null,
  "unit": "unit type or 'unit'"
}}

Return a JSON list of all items found. If no items found, return an empty list []."""


CUSTOMER_EXTRACTION_PROMPT = """Extract customer information from the following text:

Text:
{text}

Look for:
- Names (person or company)
- Email addresses
- Phone numbers
- Company names

Common patterns:
- "From: John Doe <john@example.com>"
- "Customer: Acme Corp"
- "Contact: Jane Smith, +1-555-0123"
- "Bill to: Company Name"

Return JSON:
{{
  "customer_name": "name or null",
  "customer_email": "email or null",
  "customer_phone": "phone or null",
  "company_name": "company or null",
  "contact_person": "contact or null"
}}"""


ADDRESS_EXTRACTION_PROMPT = """Extract addresses from the following text:

Text:
{text}

Look for:
- Shipping address (delivery address, ship to)
- Billing address (bill to, invoice address)

Common patterns:
- "Ship to: 123 Main St, City, State 12345"
- "Delivery address: ..."
- "Billing: [address]"

Return JSON:
{{
  "shipping_address": "full address or null",
  "billing_address": "full address or null"
}}

If billing address is "same as shipping" or similar, copy the shipping address."""


CONFIDENCE_ASSESSMENT_PROMPT = """Assess the confidence of the extracted data:

Extracted Data:
{extracted_data}

Original Text:
{original_text}

For each field, rate confidence based on:
- HIGH (0.8-1.0): Explicitly stated, unambiguous
- MEDIUM (0.5-0.7): Implied, partially stated, or requires minor interpretation
- LOW (0.0-0.4): Ambiguous, uncertain, or inferred

Return JSON:
{{
  "field_confidence": {{
    "customer_name": 0.0-1.0,
    "customer_email": 0.0-1.0,
    "items": 0.0-1.0,
    "shipping_address": 0.0-1.0,
    "total_amount": 0.0-1.0
  }},
  "overall_confidence": 0.0-1.0,
  "reasoning": "brief explanation of confidence assessment"
}}"""


MISSING_FIELDS_PROMPT = """Identify which critical fields are missing from the extracted order:

Extracted Order:
{order_data}

Critical fields required:
- customer_name OR company_name
- items (at least one)

Important fields (nice to have):
- customer_email
- customer_phone
- shipping_address
- total_amount
- order_date

Return JSON:
{{
  "missing_critical": ["list of missing critical fields"],
  "missing_important": ["list of missing important fields"],
  "can_create_order": true/false
}}

An order can be created if all critical fields are present."""


DISAMBIGUATION_PROMPT = """The following information is ambiguous. Please clarify:

Ambiguous Data:
{ambiguous_data}

Context:
{context}

Questions to resolve:
{questions}

Provide your best interpretation and confidence level:
{{
  "interpretation": "your interpretation",
  "confidence": 0.0-1.0,
  "alternative_interpretations": ["other possible meanings"]
}}"""


FINAL_VALIDATION_PROMPT = """Perform final validation of the complete extracted order:

Order Data:
{order_json}

Validation Checklist:
✓ Customer identification present
✓ At least one item with valid quantity
✓ Numerical values are reasonable
✓ No contradictory information
✓ Date formats valid (if present)
✓ Currency specified
✓ Addresses complete (if present)

Issues found (if any):
{issues}

Final Assessment:
{{
  "can_create_order": true/false,
  "confidence": 0.0-1.0,
  "quality_score": 0.0-1.0,
  "ready_for_processing": true/false,
  "recommendations": ["any recommendations for improvement"]
}}"""


# Fallback prompt when extraction fails
FALLBACK_PROMPT = """The initial extraction attempt was not successful. Let's try a simpler approach.

Text:
{text}

Please answer these simple questions:
1. Who is ordering? (customer name or company)
2. What are they ordering? (list items)
3. How many of each item?
4. Where should it be delivered? (if mentioned)
5. Any other important details?

Provide answers in simple text format."""


# Prompt for handling different input types
INPUT_TYPE_DETECTION_PROMPT = """Analyze the input and determine what type of document this is:

Input:
{input_preview}

Possible types:
- email (has from/to/subject headers)
- invoice (has invoice number, itemized billing)
- purchase_order (has PO number, formal order structure)
- casual_message (informal, chat-style, WhatsApp-like)
- quote (has quote number, estimated prices)
- other

Return JSON:
{{
  "document_type": "type",
  "confidence": 0.0-1.0,
  "characteristics": ["list of identifying features"]
}}

This will help us use the right extraction strategy."""


def get_extraction_prompt(input_text: str) -> str:
    """Get the main extraction prompt with input filled in"""
    return EXTRACTION_PROMPT.format(input_text=input_text)


def get_field_extraction_prompt(field_name: str, field_description: str, text: str) -> str:
    """Get prompt for extracting a specific field"""
    return FIELD_EXTRACTION_PROMPT.format(
        field_name=field_name,
        field_description=field_description,
        text=text
    )


def get_validation_prompt(order_data: str) -> str:
    """Get validation prompt with order data filled in"""
    return VALIDATION_PROMPT.format(order_data=order_data)
