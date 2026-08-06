# 🤖 Agentic Order Extraction System

An intelligent workflow system that automatically extracts structured order information from unstructured inputs (emails, PDFs, text) using Ollama (Llama 3.2), LangChain, and Streamlit.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   Input Layer   │  (PDF/Text/Email)
└────────┬────────┘
         │
┌────────▼────────┐
│  PDF Processor  │  (PyPDF2 + Chunking)
└────────┬────────┘
         │
┌────────▼────────┐
│  LangChain      │  (Agent Orchestration)
│  Agent Layer    │  - Field Extraction
│                 │  - Validation
│                 │  - Confidence Scoring
└────────┬────────┘
         │
┌────────▼────────┐
│  Ollama LLM     │  (llama3.2:latest)
│  (Local)        │
└────────┬────────┘
         │
┌────────▼────────┐
│ Output Parser   │  (Structured JSON)
└────────┬────────┘
         │
┌────────▼────────┐
│  Streamlit UI   │  (Interactive Interface)
└─────────────────┘
```

## ✨ Features

- ✅ Multi-format input support (PDF, text, email)
- ✅ Intelligent field extraction with confidence scoring
- ✅ Agentic workflow with tool calling
- ✅ Structured JSON output with validation
- ✅ Real-time streaming in UI
- ✅ Debug panel showing reasoning steps
- ✅ Fallback handling for missing data
- ✅ Sample test data included
- ✅ Optional database storage (SQLite)

## 📋 Prerequisites

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

### 2. Pull Llama 3.2 Model

```bash
ollama pull llama3.2:latest
```

Verify installation:
```bash
ollama list
# Should show llama3.2:latest
ollama serve (In seperate bash)
```

### 3. Python Requirements

- Python 3.9+
- pip package manager

## 🚀 Installation

### 1. Clone/Download the Project

```bash
cd Full_order_agent_application
```

### 2. Create Virtual Environment

```bash
#Install uv (optional if already done then no need)
curl -LsSf https://astral.sh/uv/install.sh | sh

#Refer this website for more details about uv
https://docs.astral.sh/uv/

# Create virtual environment
uv venv --python=3.12

# Activate it
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

## 📦 Project Structure

```
├── README.md
├── requirements.txt
Full_order_agent_application/
├── app.py                      # Streamlit UI
├── src/
│   ├── __init__.py
│   ├── agent.py                # LangChain Agent
│   ├── pdf_processor.py        # PDF handling
│   ├── schema.py               # Output schemas
│   ├── tools.py                # Agent tools
│   └── prompts.py              # LLM prompts
├── tests/
│   ├── sample_inputs/
│   │   ├── sample_email.txt
│   │   ├── sample_whatsapp.txt
│   │   ├── sample_invoice.pdf
│   │   └── sample_order.txt
│   └── test_agent.py
├── database/
│   └── orders.db               # SQLite (auto-created)
└── logs/
    └── agent.log               # Debug logs
```

## 🎯 Usage

### Starting the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Using the Interface

1. **Choose Input Method:**
   - Upload a PDF document
   - Paste email/text content
   
2. **Click "Generate Order JSON"**

3. **View Results:**
   - Structured JSON output
   - Field confidence scores
   - Missing field alerts
   - Debug panel with reasoning

### Programmatic Usage

```python
from src.agent import OrderExtractionAgent

# Initialize agent
agent = OrderExtractionAgent()

# Extract from text
text = "Order from John Doe, 5 laptops at $1000 each..."
result = agent.extract_order(text)

print(result['order'])
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

Test with sample data:

```bash
python tests/test_agent.py
```

## 📊 Output Schema

```json
{
  "can_create_order": true,
  "confidence": 0.85,
  "missing_fields": ["delivery_date"],
  "order": {
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "+1234567890",
    "items": [
      {
        "name": "Laptop Pro 15",
        "quantity": 5,
        "price": 1000.00,
        "subtotal": 5000.00
      }
    ],
    "shipping_address": "123 Main St, City, State 12345",
    "billing_address": "Same as shipping",
    "payment_terms": "Net 30",
    "delivery_date": null,
    "order_date": "2024-01-15",
    "total_amount": 5000.00,
    "currency": "USD",
    "notes": "",
    "extras": {}
  },
  "field_confidence": {
    "customer_name": 0.95,
    "items": 0.90,
    "shipping_address": 0.80
  }
}
```

## 🔧 Configuration

Edit `src/agent.py` to customize:

- LLM temperature and parameters
- Confidence thresholds
- Required vs optional fields
- Validation rules
- Output format

## 🐛 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# (Method varies by OS)
```

### Model Not Found

```bash
ollama pull llama3.2:latest
```

### Slow Performance

- Reduce PDF chunk size in `pdf_processor.py`
- Lower max_tokens in agent configuration
- Use a smaller model: `ollama pull llama3.2:1b`

### Memory Issues

- Process PDFs in smaller chunks
- Reduce context window size
- Close other applications

## 🎨 Customization

### Adding Custom Fields

Edit `src/schema.py`:

```python
class OrderSchema(BaseModel):
    # Add your custom field
    custom_field: Optional[str] = None
```

### Custom Validation Rules

Edit `src/tools.py`:

```python
def validate_order(order_data):
    # Add your validation logic
    if not order_data.get('custom_field'):
        return False, "Custom field required"
    return True, ""
```

## 📈 Performance Tips

1. **Batch Processing:** Process multiple documents in sequence
2. **Caching:** Enable LangChain caching for repeated queries
3. **Model Selection:** Use `llama3.2:1b` for faster processing
4. **Chunk Optimization:** Tune PDF chunk size based on document type

## 🔐 Security Notes

- All processing happens locally (no data sent to external APIs)
- Ollama runs on localhost by default
- Consider adding authentication for production deployments
- Sanitize file uploads in production

## 📝 License

MIT License - Feel free to use and modify for your needs.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional document format support (DOCX, Excel)
- Multi-language support
- Advanced validation rules
- UI/UX enhancements
- Performance optimizations

## 📞 Support

For issues:
1. Check logs in `logs/agent.log`
2. Enable debug mode in Streamlit UI
3. Verify Ollama is running and model is loaded

## 🎓 Learn More

- [LangChain Documentation](https://python.langchain.com/)
- [Ollama Documentation](https://ollama.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Llama 3.2 Model Card](https://ollama.com/library/llama3.2)

---

**Built with ❤️ using Ollama, LangChain, and Streamlit**
