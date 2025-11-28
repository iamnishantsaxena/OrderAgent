# System Workflow Visualization

## Complete Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INPUT                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │    PDF     │  │    Text    │  │   Email    │                   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                   │
└────────┼───────────────┼───────────────┼──────────────────────────┘
         │               │               │
         ├───────────────┴───────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                               │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  PDF Processor                                        │           │
│  │  • Extract text (PyPDF2 + pdfplumber)               │           │
│  │  • Extract tables                                    │           │
│  │  • Clean & normalize                                 │           │
│  │  • Intelligent chunking (2000 char chunks)          │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Cleaned Text Input   │
         └───────────┬────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATION                               │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  OrderExtractionAgent                                 │           │
│  │  • Manages workflow                                   │           │
│  │  • Coordinates LLM + Tools                           │           │
│  │  • Tracks extraction steps                           │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: INITIAL EXTRACTION                        │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  LLM Analysis (Ollama + Llama 3.2)                  │           │
│  │  ┌────────────────────────────────────────┐         │           │
│  │  │ System Prompt:                          │         │           │
│  │  │ "You are an expert order processor..." │         │           │
│  │  └────────────────────────────────────────┘         │           │
│  │                                                       │           │
│  │  Extract:                                            │           │
│  │  • Customer information                              │           │
│  │  • Items with quantities                            │           │
│  │  • Addresses                                         │           │
│  │  • Financial details                                 │           │
│  │  • Dates                                             │           │
│  │                                                       │           │
│  │  Output: Structured JSON                            │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Initial Extract │
            └────────┬─────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 2: TOOL-BASED REFINEMENT                       │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  Specialized Extraction Tools                        │           │
│  │  ┌────────────────┐  ┌────────────────┐            │           │
│  │  │ extract_       │  │ extract_       │            │           │
│  │  │ customer_info  │  │ items          │            │           │
│  │  │ • Regex        │  │ • Patterns     │            │           │
│  │  │ • Email detect │  │ • Quantity     │            │           │
│  │  │ • Phone parse  │  │ • Prices       │            │           │
│  │  └────────────────┘  └────────────────┘            │           │
│  │                                                       │           │
│  │  ┌────────────────┐  ┌────────────────┐            │           │
│  │  │ extract_       │  │ extract_       │            │           │
│  │  │ addresses      │  │ dates          │            │           │
│  │  │ • Ship-to      │  │ • Order date   │            │           │
│  │  │ • Bill-to      │  │ • Delivery     │            │           │
│  │  └────────────────┘  └────────────────┘            │           │
│  │                                                       │           │
│  │  ┌────────────────┐                                 │           │
│  │  │ extract_       │                                 │           │
│  │  │ financial_info │                                 │           │
│  │  │ • Amounts      │                                 │           │
│  │  │ • Currency     │                                 │           │
│  │  │ • Terms        │                                 │           │
│  │  └────────────────┘                                 │           │
│  │                                                       │           │
│  │  Fill gaps in initial extraction                    │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Refined Extract │
            └────────┬─────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: VALIDATION                                │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  validate_order_data Tool                            │           │
│  │                                                       │           │
│  │  Check:                                              │           │
│  │  ✓ Critical fields present                          │           │
│  │    - customer_name OR company_name                  │           │
│  │    - items (at least one)                           │           │
│  │                                                       │           │
│  │  ✓ Data quality                                      │           │
│  │    - Quantities > 0                                  │           │
│  │    - Prices reasonable                               │           │
│  │    - Dates valid format                              │           │
│  │    - No contradictions                               │           │
│  │                                                       │           │
│  │  Output: Validation report                          │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Validation Report      │
        │ • Errors               │
        │ • Warnings             │
        │ • Can create order?    │
        └────────┬───────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 4: CONFIDENCE SCORING                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  calculate_confidence Tool                           │           │
│  │                                                       │           │
│  │  For each field:                                     │           │
│  │  ┌─────────────────────────────────┐                │           │
│  │  │ HIGH (0.8-1.0)                  │                │           │
│  │  │ • Explicitly stated             │                │           │
│  │  │ • Exact match in text           │                │           │
│  │  └─────────────────────────────────┘                │           │
│  │  ┌─────────────────────────────────┐                │           │
│  │  │ MEDIUM (0.5-0.7)                │                │           │
│  │  │ • Implied or partial            │                │           │
│  │  │ • Derived from context          │                │           │
│  │  └─────────────────────────────────┘                │           │
│  │  ┌─────────────────────────────────┐                │           │
│  │  │ LOW (0.0-0.4)                   │                │           │
│  │  │ • Inferred or uncertain         │                │           │
│  │  │ • Multiple interpretations      │                │           │
│  │  └─────────────────────────────────┘                │           │
│  │                                                       │           │
│  │  Calculate overall: weighted_average(field_scores)  │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Confidence Scores      │
        │ • Per field            │
        │ • Overall              │
        └────────┬───────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 5: RESULT ASSEMBLY                             │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  Build ExtractionResult                              │           │
│  │                                                       │           │
│  │  Create Order object:                                │           │
│  │  • Convert to Pydantic model                         │           │
│  │  • Auto-calculate fields (subtotals, totals)        │           │
│  │  • Validate schema                                   │           │
│  │                                                       │           │
│  │  Package complete result:                            │           │
│  │  • can_create_order                                  │           │
│  │  • confidence                                        │           │
│  │  • missing_fields                                    │           │
│  │  • order (complete Order object)                    │           │
│  │  • field_confidence                                  │           │
│  │  • warnings                                          │           │
│  │  • extraction_metadata                               │           │
│  └───────────────────┬──────────────────────────────────┘           │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FINAL OUTPUT                                    │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  {                                                    │           │
│  │    "can_create_order": true,                        │           │
│  │    "confidence": 0.85,                              │           │
│  │    "missing_fields": [],                            │           │
│  │    "order": {                                       │           │
│  │      "customer_name": "John Doe",                  │           │
│  │      "customer_email": "john@example.com",         │           │
│  │      "items": [                                    │           │
│  │        {                                           │           │
│  │          "name": "Laptop",                        │           │
│  │          "quantity": 5,                           │           │
│  │          "price": 1000.00,                        │           │
│  │          "subtotal": 5000.00                      │           │
│  │        }                                           │           │
│  │      ],                                            │           │
│  │      "shipping_address": "123 Main St...",        │           │
│  │      "total_amount": 5000.00,                     │           │
│  │      "currency": "USD"                            │           │
│  │    },                                              │           │
│  │    "field_confidence": {                          │           │
│  │      "customer_name": 0.95,                       │           │
│  │      "items": 0.90                                │           │
│  │    }                                               │           │
│  │  }                                                  │           │
│  └──────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                     │
                     ├─────────────────────┐
                     │                     │
                     ▼                     ▼
         ┌───────────────────┐ ┌───────────────────┐
         │  Streamlit UI     │ │  Database         │
         │  Display          │ │  Storage          │
         │  • Visual cards   │ │  • SQLite         │
         │  • Confidence     │ │  • History        │
         │  • JSON export    │ │  • Analytics      │
         └───────────────────┘ └───────────────────┘
```

## LLM Interaction Flow

```
User Input
    │
    ▼
┌─────────────────────────┐
│  Prompt Construction    │
│  ┌────────────────────┐ │
│  │ System Prompt      │ │
│  │ + Extraction Rules │ │
│  │ + Output Format    │ │
│  │ + User Input       │ │
│  └────────────────────┘ │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Ollama API Call        │
│  Model: llama3.2:latest │
│  Temperature: 0.1       │
│  Max Tokens: 2000       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  LLM Processing         │
│  • Understand context   │
│  • Extract information  │
│  • Structure output     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  JSON Response          │
│  Parse & Validate       │
└───────────┬─────────────┘
            │
            ▼
        Result Data
```

## Tool Execution Pattern

```
Agent decides tool is needed
    │
    ▼
┌─────────────────────────┐
│  Tool Selection         │
│  Based on:              │
│  • Missing fields       │
│  • Low confidence       │
│  • Validation needs     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Tool Execution         │
│  • Extract with regex   │
│  • Pattern matching     │
│  • Date parsing         │
│  • Validation logic     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Merge Results          │
│  • Update fields        │
│  • Increase confidence  │
│  • Resolve conflicts    │
└───────────┬─────────────┘
            │
            ▼
    Updated Extraction
```

## Error Handling Flow

```
Operation Attempted
    │
    ├──[Success]──> Continue
    │
    └──[Error]──> ┌────────────────┐
                  │ Error Handler  │
                  └───────┬────────┘
                          │
                          ├──[PDF Error]──> Fallback Extractor
                          │
                          ├──[LLM Error]──> Retry with Tools
                          │
                          ├──[Parse Error]──> Return Partial
                          │
                          └──[Fatal]──> Error Response
                                        {
                                          "can_create_order": false,
                                          "error": "description",
                                          "partial_data": {...}
                                        }
```

## Confidence Decision Tree

```
Field Extracted
    │
    ▼
Is value explicitly in text?
    │
    ├─[Yes]─> Exact match?
    │          │
    │          ├─[Yes]─> HIGH (0.9-1.0)
    │          │
    │          └─[No]──> Similar match?
    │                    │
    │                    ├─[Yes]─> HIGH (0.8-0.9)
    │                    │
    │                    └─[No]──> MEDIUM (0.6-0.7)
    │
    └─[No]──> Implied or inferred?
               │
               ├─[Clear implication]─> MEDIUM (0.5-0.6)
               │
               └─[Uncertain]─> LOW (0.0-0.4)
```

## Streaming Updates Flow

```
Start Extraction
    │
    ▼
yield {"status": "starting"}
    │
    ▼
LLM Extraction
    │
    ├─> yield {"status": "extracting"}
    │
    └─> yield {"status": "progress", "step": 1}
    │
    ▼
Tool Refinement
    │
    ├─> yield {"status": "refining"}
    │
    └─> yield {"status": "progress", "step": 2}
    │
    ▼
Validation
    │
    ├─> yield {"status": "validating"}
    │
    └─> yield {"status": "progress", "step": 3}
    │
    ▼
Confidence Scoring
    │
    ├─> yield {"status": "scoring"}
    │
    └─> yield {"status": "progress", "step": 4}
    │
    ▼
Assembly
    │
    ├─> yield {"status": "finalizing"}
    │
    └─> yield {"status": "progress", "step": 5}
    │
    ▼
yield {"status": "complete", "result": {...}}
```

This visualization shows the complete data flow through the system!
