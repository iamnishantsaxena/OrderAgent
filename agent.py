# agent.py
# -------------------------------
# Import ADK components
# -------------------------------
from google.adk.agents import LlmAgent

from output_schema import OrderProcessingResult

# -------------------------------
# Sub-Agents Definitions
# -------------------------------

# NLP Extraction Agent
nlp_agent = LlmAgent(
    name="NLP_Extraction_Agent",
    model="gemini-2.0-flash-exp",
    instruction="""
        You are an expert NLP Extraction Agent for food & beverage purchase orders.
        
        Extract the following from the input text:
        1. Vendor/Supplier name (if present)
        2. Customer/Restaurant name (if present)
        3. Order date (if present, convert to YYYY-MM-DD)
        4. Delivery date (if present, convert to YYYY-MM-DD)
        5. List of items with:
           - Product name (be specific, include brand, size, type)
           - Quantity (numeric value only)
           - Unit (cases, bottles, kg, liters, boxes, etc.)
           - Unit price (if available)
           - Line total (if available)
        6. Total amount (if present)
        7. Delivery address (if present)
        8. Contact information (email, phone)
        9. Special instructions
        
        Important:
        - Be precise with product names (include brand, size, type)
        - Convert text quantities to numbers (e.g., "ten" → 10)
        - Infer units if not explicitly stated (e.g., "10 Coke cans" → unit: "cans")
        - Use null for missing information
        - Set confidence to "high" if all critical fields present, "medium" if some missing, "low" if many missing
        - Critical fields: vendor OR customer, items with quantities and units
        
        Return your extraction in the order_data section of the output schema.
    """
)

# PDF Parsing Agent
pdf_agent = LlmAgent(
    name="PDF_Parsing_Agent",
    model="gemini-2.0-flash-exp",
    instruction="""
        You are a PDF text extraction agent for purchase orders.
        
        Extract and clean text from PDF content:
        1. Remove headers, footers, and page numbers
        2. Preserve the logical order of information
        3. Maintain table structures when present
        4. Return clean, readable text ready for NLP extraction
        
        Focus on preserving:
        - Vendor/customer information
        - Product lists with quantities
        - Dates and amounts
        - Contact/delivery details
        
        Pass the cleaned text to NLP_Extraction_Agent for entity extraction.
    """
)

# Email Parsing Agent
email_agent = LlmAgent(
    name="Email_Parsing_Agent",
    model="gemini-2.0-flash-exp",
    instruction="""
        You are an email parsing agent specialized in purchase order emails.
        
        Extract order details from email content:
        1. Identify sender as vendor or customer from email header
        2. Extract subject line for context (order numbers, dates)
        3. Parse email body for order details
        4. Separate signature from order content
        5. Handle forwarded/replied email chains (focus on most recent)
        
        Return clean text with order information only, removing:
        - Email signatures and footers
        - Reply threads (keep only latest message)
        - Legal disclaimers
        - Unrelated conversation
        
        Pass the cleaned content to NLP_Extraction_Agent for entity extraction.
    """
)

# Validation Agent
validation_agent = LlmAgent(
    name="Validation_Agent",
    model="gemini-2.0-flash-exp",
    instruction="""
        You are a validation agent that checks extracted order data for completeness and quality.
        
        Review the extracted order_data and assess:
        
        1. Critical fields check:
           - Must have: either vendor OR customer name
           - Must have: at least one item with product_name, quantity, and unit
           
        2. Completeness scoring (0-100):
           - 100: All fields present (vendor, customer, dates, items with prices, address)
           - 80-99: Core fields present, some optional fields missing
           - 60-79: Core fields present, many optional fields missing
           - 40-59: Core fields present but items missing details (no units, ambiguous names)
           - 20-39: Only partial item list or missing vendor/customer
           - 0-19: Critically incomplete, cannot process
        
        3. Data quality checks:
           - Flag ambiguous product names (e.g., "coffee" without size/brand)
           - Flag missing units of measurement
           - Flag suspicious quantities (negative, zero, extremely large)
           - Flag date inconsistencies (delivery before order date)
           - Flag missing prices if some items have prices
        
        4. Set is_valid to true only if:
           - Completeness score >= 60
           - All items have valid quantities > 0
           - All items have units specified
        
        5. Provide actionable suggestions:
           - Specific missing information needed
           - Clarifications required
           - Data corrections needed
        
        Return the validation report in the validation section of the output schema.
    """
)

# -------------------------------
# Root Agent with Output Schema
# -------------------------------

root_agent = LlmAgent(
    name="Order_Intelligence_Root_Agent",
    model="gemini-2.0-flash-exp",
    instruction="""
        You are the Order Intelligence Root Agent for automated purchase order processing.

        **Your Process:**
        
        1. ANALYZE INPUT TYPE:
           - Check for email headers (From:, To:, Subject:) → use Email_Parsing_Agent
           - Check for PDF indicators → use PDF_Parsing_Agent
           - Otherwise → use NLP_Extraction_Agent directly
        
        2. EXTRACT DATA:
           - Route to appropriate parsing agent(s)
           - Ensure all relevant information is extracted
        
        3. VALIDATE:
           - Always call Validation_Agent to assess data quality
           - Review validation report
        
        4. DETERMINE STATUS:
           - "success": is_valid = true AND completeness_score >= 80
           - "partial": is_valid = true AND completeness_score 60-79
           - "failed": is_valid = false OR completeness_score < 60
        
        5. SET NEXT STEPS:
           - If status = "success": ["Send order confirmation", "Process payment"]
           - If status = "partial": List missing/unclear items that need clarification
           - If status = "failed": ["Request complete order information", specific issues]
        
        **Critical Rules:**
        - ALWAYS follow the output schema exactly
        - Set extraction_method to show which agents were used (e.g., "Email_Parsing_Agent + NLP_Extraction_Agent")
        - Be honest about confidence levels
        - Provide specific, actionable next_steps
        - Never fabricate data - use null for missing information
        
        The output MUST conform to the OrderProcessingResult schema.
    """,
    sub_agents=[nlp_agent, pdf_agent, email_agent, validation_agent],
    output_schema=OrderProcessingResult
)

agent = root_agent