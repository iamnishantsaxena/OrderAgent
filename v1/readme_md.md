# Email Order Parser

Parse emails and extract order information as structured JSON using free local LLMs.

## Quick Start

### Pre-Setup: Python with uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python=3.12
uv pip install -r requirements.txt
```

### 1. Install Ollama

```bash
brew install ollama
```

### 2. Pull a Model

```bash
ollama pull qwen2.5:1.5b-instruct-q4_1
```

Or try other models:
- `ollama pull llama3.2` (better quality)
- `ollama pull mistral` (best quality)

### 3. Install Python Dependencies (optional)

```bash
pip install langchain langchain-community langchain-core pydantic
```

### 4. Start Ollama Server

**Terminal 1:**
```bash
ollama serve
```

Keep this running.

### 5. Run the Parser

**Terminal 2:**
```bash
python email_order_parser.py
```

## Usage

```python
from email_order_parser import EmailOrderParser

# Initialize parser
parser = EmailOrderParser(model_name="qwen2.5:1.5b-instruct-q4_1")

# Parse email
email_text = """
Hi, I'm John Doe (john@email.com).
Please deliver to 123 Main St.

I need:
- 2 Coffee Beans at $15.99
- 1 Mug at $10

Thanks!
"""

order = parser.parse_email(email_text)
print(order)
```

## Output Example

```json
{
  "customer_name": "John Doe",
  "customer_email": "john@email.com",
  "delivery_address": "123 Main St",
  "items": [
    {
      "product_name": "Coffee Beans",
      "quantity": 2,
      "unit_price": 15.99
    },
    {
      "product_name": "Mug",
      "quantity": 1,
      "unit_price": 10.0
    }
  ],
  "total_amount": 41.98
}
```

## Troubleshooting

**Connection Error?**
- Make sure `ollama serve` is running in another terminal

**Model Not Found?**
- Run `ollama pull <model-name>` first

**Slow Performance?**
- Use smaller models: `qwen2.5:1.5b-instruct-q4_1` or `llama3.2:1b`

## Requirements

- macOS (Intel or Apple Silicon)
- Python 3.8+
- 2GB+ RAM
- Internet (first time only, to download models)
