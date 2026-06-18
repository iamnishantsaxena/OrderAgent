# API Documentation

## OrderExtractionAgent

Main class for extracting structured order information from unstructured text.

### Initialization

```python
from src.agent import OrderExtractionAgent

agent = OrderExtractionAgent(
    model_name="llama3.2:latest",
    temperature=0.1,
    ollama_base_url="http://localhost:11434",
    verbose=True
)
```

**Parameters:**
- `model_name` (str): Ollama model to use. Default: `"llama3.2:latest"`
- `temperature` (float): LLM temperature (0.0-1.0). Lower = more deterministic. Default: `0.1`
- `ollama_base_url` (str): Ollama API base URL. Default: `"http://localhost:11434"`
- `verbose` (bool): Enable detailed logging. Default: `True`

### Methods

#### extract_order()

Extract order from text input.

```python
result = agent.extract_order(
    input_text="Order from John Doe...",
    source_type="text"
)
```

**Parameters:**
- `input_text` (str): Text to extract order from
- `source_type` (str): Type of input. Options: `"text"`, `"email"`, `"pdf"`. Default: `"text"`

**Returns:** `Dict[str, Any]`

```python
{
    "can_create_order": bool,
    "confidence": float,  # 0.0-1.0
    "missing_fields": List[str],
    "order": {
        "customer_name": str,
        "customer_email": str,
        "items": [
            {
                "name": str,
                "quantity": float,
                "price": float,
                "subtotal": float
            }
        ],
        # ... more fields
    },
    "field_confidence": {
        "customer_name": float,
        "items": float,
        # ... more fields
    },
    "warnings": List[str],
    "extraction_metadata": {
        "source_type": str,
        "model": str,
        "timestamp": str,
        "steps": List[Dict]
    }
}
```

**Example:**

```python
text = """
Order from: Alice Smith
Email: alice@example.com
5 laptops @ $1000 each
Ship to: 123 Main St, City, State 12345
"""

result = agent.extract_order(text)

if result["can_create_order"]:
    print(f"Order created with {result['confidence']:.0%} confidence")
    print(f"Customer: {result['order']['customer_name']}")
    print(f"Total: ${result['order']['total_amount']}")
else:
    print(f"Cannot create order. Missing: {result['missing_fields']}")
```

---

#### extract_order_streaming()

Extract order with streaming progress updates.

```python
for update in agent.extract_order_streaming(input_text, source_type="text"):
    status = update.get("status")
    
    if status == "complete":
        result = update.get("result")
        # Use result
```

**Parameters:**
- `input_text` (str): Text to extract order from
- `source_type` (str): Type of input. Default: `"text"`

**Yields:** `Dict[str, Any]`

Update types:
- `{"status": "starting", "message": str}`
- `{"status": "extracting", "message": str}`
- `{"status": "progress", "data": dict, "step": int, "total_steps": int}`
- `{"status": "complete", "result": dict}`
- `{"status": "error", "error": str}`

**Example:**

```python
for update in agent.extract_order_streaming(text):
    if update["status"] == "progress":
        print(f"Step {update['step']}/{update['total_steps']}")
    elif update["status"] == "complete":
        result = update["result"]
        print("Done!")
        break
```

---

#### process_pdf()

Extract order from PDF file.

```python
result = agent.process_pdf(pdf_file)
```

**Parameters:**
- `pdf_file`: File path (str/Path) or file-like object

**Returns:** `Dict[str, Any]` (same as `extract_order()`)

**Example:**

```python
# From file path
result = agent.process_pdf("invoice.pdf")

# From Streamlit upload
uploaded_file = st.file_uploader("Upload PDF")
if uploaded_file:
    result = agent.process_pdf(uploaded_file)
```

---

## PDFProcessor

PDF document processing and text extraction.

### Initialization

```python
from src.pdf_processor import PDFProcessor

processor = PDFProcessor(
    chunk_size=2000,
    chunk_overlap=200
)
```

**Parameters:**
- `chunk_size` (int): Maximum characters per chunk. Default: `2000`
- `chunk_overlap` (int): Overlap between chunks. Default: `200`

### Methods

#### process_pdf()

```python
result = processor.process_pdf(pdf_file)
```

**Returns:**

```python
{
    "text": str,  # Extracted text
    "metadata": {
        "num_pages": int,
        "extractor": str,
        "title": str,
        "author": str
    },
    "chunks": [
        {
            "text": str,
            "chunk_id": int,
            "start_pos": int,
            "end_pos": int
        }
    ],
    "tables": List[List[List[str]]],
    "total_length": int,
    "num_chunks": int,
    "success": bool
}
```

---

## OrderDatabase

SQLite database for storing extracted orders.

### Initialization

```python
from src.database import OrderDatabase

db = OrderDatabase("database/orders.db")
```

### Methods

#### save_order()

```python
order_id = db.save_order(extraction_result)
```

**Parameters:**
- `extraction_result` (Dict): Result from `extract_order()`

**Returns:** `int` - Order ID

---

#### get_order()

```python
order = db.get_order(order_id)
```

**Parameters:**
- `order_id` (int): Order ID

**Returns:** `Dict` or `None`

---

#### search_orders()

```python
orders = db.search_orders(
    customer_name="John",
    start_date="2024-01-01",
    min_amount=100.0,
    limit=50
)
```

**Parameters:**
- `customer_name` (str, optional): Customer name (partial match)
- `start_date` (str, optional): Start date (ISO format)
- `end_date` (str, optional): End date (ISO format)
- `min_amount` (float, optional): Minimum total amount
- `max_amount` (float, optional): Maximum total amount
- `limit` (int): Maximum results. Default: `100`

**Returns:** `List[Dict]`

---

#### get_statistics()

```python
stats = db.get_statistics()
```

**Returns:**

```python
{
    "total_orders": int,
    "valid_orders": int,
    "total_value": float,
    "avg_confidence": float,
    "orders_last_7_days": int
}
```

---

## Tools

Individual extraction tools available as standalone functions.

### extract_customer_info()

```python
from src.tools import extract_customer_info

result = extract_customer_info.invoke({"text": input_text})
data = json.loads(result)
```

**Returns:** JSON string with:
```python
{
    "customer_name": str,
    "customer_email": str,
    "customer_phone": str,
    "company_name": str,
    "contact_person": str
}
```

---

### extract_items()

```python
from src.tools import extract_items

result = extract_items.invoke({"text": input_text})
items = json.loads(result)
```

**Returns:** JSON string with list of items:
```python
[
    {
        "name": str,
        "quantity": float,
        "price": float,
        "unit": str
    }
]
```

---

### extract_addresses()

```python
from src.tools import extract_addresses

result = extract_addresses.invoke({"text": input_text})
addresses = json.loads(result)
```

**Returns:** JSON string with:
```python
{
    "shipping_address": str,
    "billing_address": str
}
```

---

### extract_dates()

```python
from src.tools import extract_dates

result = extract_dates.invoke({"text": input_text})
dates = json.loads(result)
```

**Returns:** JSON string with:
```python
{
    "order_date": str,  # YYYY-MM-DD
    "delivery_date": str,
    "due_date": str
}
```

---

### extract_financial_info()

```python
from src.tools import extract_financial_info

result = extract_financial_info.invoke({"text": input_text})
financial = json.loads(result)
```

**Returns:** JSON string with:
```python
{
    "total_amount": float,
    "subtotal": float,
    "tax_amount": float,
    "currency": str,
    "payment_terms": str,
    "payment_method": str
}
```

---

### validate_order_data()

```python
from src.tools import validate_order_data

result = validate_order_data.invoke({
    "order_json": json.dumps(order_dict)
})
validation = json.loads(result)
```

**Returns:** JSON string with:
```python
{
    "valid": bool,
    "errors": List[str],
    "warnings": List[str],
    "can_create_order": bool
}
```

---

## Schema Models

### Order

```python
from src.schema import Order

order = Order(
    customer_name="John Doe",
    customer_email="john@example.com",
    items=[
        OrderItem(
            name="Widget",
            quantity=5,
            price=10.0
        )
    ],
    shipping_address="123 Main St",
    total_amount=50.0
)

# Validate
is_valid, missing_fields = validate_order_completeness(order)

# Convert to dict
order_dict = order.model_dump()

# Convert to JSON
order_json = order.model_dump_json(indent=2)
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customer_name | str | ✓ | Customer name |
| customer_email | str | | Email address |
| customer_phone | str | | Phone number |
| company_name | str | | Company name |
| items | List[OrderItem] | ✓ | Order items |
| shipping_address | str | | Shipping address |
| billing_address | str | | Billing address |
| order_date | str | | Order date (YYYY-MM-DD) |
| delivery_date | str | | Delivery date |
| total_amount | float | | Total amount |
| currency | str | | Currency code |
| payment_terms | str | | Payment terms |
| notes | str | | Additional notes |

---

### OrderItem

```python
from src.schema import OrderItem

item = OrderItem(
    name="Laptop",
    quantity=5,
    price=1000.0,
    unit="pcs"
)

# Auto-calculated subtotal
print(item.subtotal)  # 5000.0
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | ✓ | Product name |
| quantity | float | ✓ | Quantity |
| price | float | | Unit price |
| subtotal | float | | Auto-calculated |
| unit | str | | Unit type |
| sku | str | | SKU/product code |

---

### ExtractionResult

```python
from src.schema import ExtractionResult

result = ExtractionResult(
    can_create_order=True,
    confidence=0.85,
    missing_fields=[],
    order=order,
    field_confidence={"customer_name": 0.95}
)
```

---

## Configuration

### Config Class

```python
from src.config import config

# Access settings
print(config.OLLAMA_BASE_URL)
print(config.DEFAULT_MODEL)
print(config.LLM_TEMPERATURE)

# Get LLM config
llm_config = config.get_llm_config()

# Get PDF config
pdf_config = config.get_pdf_config()
```

### Environment Variables

```bash
# Ollama
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:latest"
export LLM_TEMPERATURE="0.1"

# PDF
export PDF_CHUNK_SIZE="2000"
export PDF_MAX_SIZE_MB="10.0"

# Database
export DATABASE_PATH="database/orders.db"
export ENABLE_DATABASE="true"

# Environment
export APP_ENV="production"  # development, production, testing
```

---

## Error Handling

### Common Errors

```python
from src.agent import OrderExtractionAgent

agent = OrderExtractionAgent()

try:
    result = agent.extract_order(text)
except ConnectionError:
    print("Cannot connect to Ollama. Is it running?")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Validation Errors

```python
from src.schema import Order
from pydantic import ValidationError

try:
    order = Order(
        customer_name="John",
        items=[]  # Invalid - requires at least one item
    )
except ValidationError as e:
    print(e.errors())
```

---

## Complete Example

```python
from src.agent import OrderExtractionAgent
from src.database import OrderDatabase
import json

# Initialize
agent = OrderExtractionAgent()
db = OrderDatabase()

# Input text
text = """
Purchase Order #12345
From: Tech Solutions Inc.
Contact: Sarah Chen (sarah@techsolutions.com)

Items:
- 10 Laptops @ $1200 = $12,000
- 10 Mice @ $50 = $500

Total: $12,500
Ship to: 123 Tech Ave, San Francisco, CA 94105
Payment: Net 30
"""

# Extract
print("Extracting order...")
result = agent.extract_order(text)

# Check validity
if result["can_create_order"]:
    print(f"✓ Order valid (confidence: {result['confidence']:.0%})")
    
    # Print details
    order = result["order"]
    print(f"Customer: {order['customer_name']}")
    print(f"Items: {len(order['items'])}")
    print(f"Total: ${order['total_amount']}")
    
    # Save to database
    order_id = db.save_order(result)
    print(f"✓ Saved to database (ID: {order_id})")
    
    # Export JSON
    with open("order.json", "w") as f:
        json.dump(result, f, indent=2)
    print("✓ Exported to order.json")
    
else:
    print("✗ Cannot create order")
    print(f"Missing fields: {result['missing_fields']}")
    print(f"Warnings: {result['warnings']}")

# Cleanup
db.close()
```

---

## Best Practices

### 1. Error Handling

Always wrap agent calls in try-except blocks:

```python
try:
    result = agent.extract_order(text)
except Exception as e:
    logger.error(f"Extraction failed: {e}")
    # Handle error appropriately
```

### 2. Confidence Thresholds

Filter results by confidence:

```python
CONFIDENCE_THRESHOLD = 0.7

if result["confidence"] >= CONFIDENCE_THRESHOLD:
    # Auto-process
    process_order(result)
else:
    # Manual review
    flag_for_review(result)
```

### 3. Validation

Always validate before using:

```python
from src.schema import validate_order_completeness

order = result["order"]
is_valid, missing = validate_order_completeness(order)

if not is_valid:
    print(f"Order incomplete: {missing}")
```

### 4. Resource Management

Close database connections:

```python
db = OrderDatabase()
try:
    # Use database
    db.save_order(result)
finally:
    db.close()
```

### 5. Logging

Enable logging for debugging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
agent = OrderExtractionAgent(verbose=True)
```

---

## Performance Tips

1. **Use appropriate model size:**
   - `llama3.2:1b` - Fastest, good for simple orders
   - `llama3.2:3b` - Balanced
   - `llama3.2:latest` - Most accurate

2. **Batch processing:**
   ```python
   results = [agent.extract_order(text) for text in texts]
   ```

3. **PDF optimization:**
   ```python
   processor = PDFProcessor(chunk_size=1000)  # Smaller chunks
   ```

4. **Caching:**
   Enable LangChain caching for repeated queries

---

For more examples, see `examples/usage_examples.py`
