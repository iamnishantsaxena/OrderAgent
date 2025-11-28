# Architecture Documentation

## System Overview

The Order Extraction Agent is a multi-layered system designed to extract structured order information from unstructured inputs using local LLMs.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                      (Streamlit UI)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Agent      │  │ PDF Processor│  │  Database    │     │
│  │ Orchestrator │  │              │  │  Manager     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │
└─────────┼──────────────────┼──────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LangChain   │  │   Tools      │  │   Schema     │     │
│  │  Agent       │  │  (Extraction)│  │  Validators  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │
└─────────┼──────────────────┼──────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM Layer                               │
│              Ollama + Llama 3.2 (Local)                     │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Input Processing

```
Input (PDF/Text/Email)
    │
    ├─> [PDF Processor] → Text Extraction + Chunking
    │                     └─> Cleaned Text
    │
    └─> [Text Input] → Direct to Agent
```

### 2. Extraction Pipeline

```
Cleaned Text
    │
    ▼
[Initial LLM Extraction]
    │ (Primary extraction via prompt)
    ▼
[Tool-Based Refinement]
    │ (Specialized extractors)
    │ ├─> Customer Info Extractor
    │ ├─> Items Extractor
    │ ├─> Address Extractor
    │ ├─> Financial Info Extractor
    │ └─> Dates Extractor
    ▼
[Validation Layer]
    │ (Business rules validation)
    ▼
[Confidence Calculation]
    │ (Field-level confidence)
    ▼
[Result Assembly]
    │
    └─> Structured JSON Output
```

## Key Components

### 1. OrderExtractionAgent (`src/agent.py`)

**Responsibilities:**
- Orchestrates the extraction workflow
- Manages LLM interactions
- Coordinates tool usage
- Assembles final results

**Methods:**
- `extract_order()`: Main synchronous extraction
- `extract_order_streaming()`: Streaming extraction with progress
- `process_pdf()`: PDF-specific processing

**State Management:**
- Tracks extraction steps
- Maintains intermediate results
- Logs operations

### 2. PDF Processor (`src/pdf_processor.py`)

**Capabilities:**
- Multi-strategy text extraction (PyPDF2 + pdfplumber)
- Intelligent chunking (respects paragraph boundaries)
- Table extraction
- Text cleaning and normalization
- Validation

**Chunking Strategy:**
```python
1. Set chunk_size (default: 2000 chars)
2. Find natural break points:
   - Paragraph boundaries (\n\n)
   - Sentence boundaries (. ! ?)
   - Maintain overlap for context
3. Create indexed chunks
```

### 3. Agent Tools (`src/tools.py`)

**Tool Functions:**
- `extract_customer_info`: Regex + pattern matching for contact details
- `extract_items`: Multiple pattern recognition for products
- `extract_addresses`: Address detection with keyword matching
- `extract_dates`: Date parsing and normalization
- `extract_financial_info`: Currency and amount extraction
- `validate_order_data`: Business rule validation
- `calculate_confidence`: Confidence scoring algorithm

**Design Pattern:** Each tool is independent and idempotent

### 4. Schema System (`src/schema.py`)

**Pydantic Models:**
```python
OrderItem
    ├─> name, quantity, price
    └─> Auto-calculated subtotal

Order
    ├─> Customer info
    ├─> Items list
    ├─> Addresses
    ├─> Financial details
    └─> Metadata

ExtractionResult
    ├─> Order object
    ├─> Validation results
    ├─> Confidence scores
    └─> Extraction metadata
```

**Validation:**
- Type checking via Pydantic
- Business rule validation
- Completeness checking

### 5. Prompt System (`src/prompts.py`)

**Prompt Types:**
- System prompt (agent context)
- Extraction prompt (main task)
- Field-specific prompts
- Validation prompts
- Confidence assessment prompts

**Strategy:**
- Few-shot examples embedded
- Clear instructions
- JSON output format specification

## LLM Integration

### Ollama Configuration

```python
Ollama(
    model="llama3.2:latest",
    base_url="http://localhost:11434",
    temperature=0.1,  # Low for consistency
)
```

### Why Local LLMs?

1. **Privacy**: All data stays on-premises
2. **Cost**: No API fees
3. **Control**: Full control over model and parameters
4. **Speed**: No network latency (after initial load)

## Database Layer (Optional)

### SQLite Schema

```sql
orders
    ├─> id, order_number, customer_name
    ├─> financial fields
    ├─> metadata
    └─> full JSON storage

order_items
    ├─> id, order_id (FK)
    └─> item details

extraction_logs
    └─> processing metrics
```

### Features:
- Order persistence
- Search and filtering
- Statistics and analytics
- Audit trail

## Confidence Scoring System

### Field Confidence

```python
Confidence = f(explicit_presence, pattern_match, validation_success)

HIGH (0.8-1.0):   Explicitly stated, validated
MEDIUM (0.5-0.7): Implied or partially stated
LOW (0.0-0.4):    Inferred or uncertain
```

### Overall Confidence

```python
overall = weighted_average(field_confidences)

Weights:
- Critical fields (customer, items): 2x
- Important fields (contact info): 1.5x
- Optional fields: 1x
```

## Error Handling

### Strategies

1. **Graceful Degradation**
   - Partial extraction on failure
   - Return what was found
   - Clear error messaging

2. **Fallback Mechanisms**
   - Primary: LLM extraction
   - Secondary: Regex tools
   - Tertiary: Manual review flag

3. **Validation Layers**
   - Type validation (Pydantic)
   - Business rules
   - Confidence thresholds

## Performance Optimization

### PDF Processing
- Chunk size optimization
- Lazy loading for large files
- Multi-strategy extraction

### LLM Calls
- Low temperature for consistency
- Minimal max_tokens
- Structured output parsing

### Caching
- LangChain caching available
- Database result storage
- Memoization opportunities

## Security Considerations

### Current Implementation
- Local LLM (no data leakage)
- File upload validation
- Size limits on PDFs
- SQL injection protection (parameterized queries)

### Production Recommendations
- Input sanitization
- Rate limiting
- Authentication/authorization
- Audit logging
- Data encryption at rest

## Scalability

### Current Limits
- Single threaded
- Local processing only
- Memory-bound by LLM

### Scaling Options
1. **Horizontal**: Multiple agent instances
2. **Vertical**: Larger/faster models
3. **Distributed**: Queue-based processing
4. **Caching**: Result caching layer

## Monitoring & Observability

### Metrics to Track
- Extraction success rate
- Average confidence scores
- Processing time
- Error rates
- Field extraction accuracy

### Logging
- Extraction steps
- Tool calls
- Validation results
- Error traces

## Extension Points

### Adding Custom Fields
```python
# src/schema.py
class Order(BaseModel):
    custom_field: Optional[str] = None
```

### Adding Custom Tools
```python
# src/tools.py
@tool
def extract_custom_field(text: str) -> str:
    # Your logic here
    return json.dumps(result)
```

### Adding Validation Rules
```python
# src/tools.py
def validate_custom_rule(order: Order):
    # Your validation
    return is_valid, error_message
```

## Testing Strategy

### Unit Tests
- Individual tool functions
- Schema validation
- PDF processing

### Integration Tests
- End-to-end extraction
- Multi-format inputs
- Error scenarios

### Sample Data
- Diverse formats (email, PDF, text)
- Edge cases
- Validation scenarios

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Docker (Future)
```dockerfile
FROM python:3.9
# Install Ollama
# Install dependencies
# Run app
```

### Cloud Deployment
- Considerations for Ollama in cloud
- Model storage
- Memory requirements

## Future Enhancements

### Potential Improvements
1. **Multi-language support**
2. **Advanced table extraction**
3. **Image OCR integration**
4. **Email server integration**
5. **Webhook notifications**
6. **Advanced analytics dashboard**
7. **Model fine-tuning**
8. **Batch processing API**

## Conclusion

This architecture provides:
- **Modularity**: Components are independent
- **Extensibility**: Easy to add features
- **Reliability**: Multiple validation layers
- **Privacy**: Fully local processing
- **Performance**: Optimized for common cases

The system balances accuracy, speed, and usability for practical order extraction needs.
