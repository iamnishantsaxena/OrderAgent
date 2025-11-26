# main.py
# -------------------------------
# Import ADK components
# -------------------------------
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool

# -------------------------------
# Sub-Agents Definitions
# -------------------------------

# NLP Extraction Agent
nlp_agent = LlmAgent(
    name="NLP_Extraction_Agent",
    model="gemini-2.5-flash",
    # description="Extracts product names and quantities from text.",
    instruction="""
        You are an NLP Extraction Agent specialized in extracting purchase order details from unstructured text.
        Given the following text, extract the vendor name, list of items with their quantities, and the total amount.
        Return the extracted information in the following JSON format:
        {
        "vendor": "Vendor Name",
        "items": [
            {"item_name": "Item 1", "quantity": Quantity1},
            {"item_name": "Item 2", "quantity": Quantity2},
            ...
        ],
        "total_amount": TotalAmount
        } 
        Ensure that the JSON is properly formatted and valid.
        """
)

# PDF Parsing Agent
pdf_agent = LlmAgent(
    name="PDF_Parsing_Agent",
    model="gemini-2.5-flash",
    # description="Extracts text from PDF-like content.",
    instruction="""
        You are a PDF parsing agent. Extract clean text from the PDF content.
        Return the raw text only.
    """
)

# Optional: You can add more agents here like EmailParserAgent, ValidationAgent, etc.

# -------------------------------
# Root Agent Definition
# -------------------------------

root_agent = LlmAgent(
    name="Automated_Purchase_Order_Generation_Agent",
    model="gemini-2.5-flash",
    # description="Root agent orchestrating order parsing and structured PO generation.",
    instruction="""
        You are the Automated Purchase Order Root Agent.

        Your responsibilities:
        1. Decide which sub-agent to use based on the user's input.
        2. If the input is raw text, call the NLP Extraction Sub Agent.
        3. If PDF-like content is detected, call the PDF Parser Sub Agent (placeholder for now).
        4. Always return structured JSON in this format:

        {
        "vendor": "...",
        "items": [
            {"product_name": "...", "quantity": ...}
        ],
        "notes": "..."
        }

        Keep reasoning short. When using tools, provide the minimal input they need.
        """,
    sub_agents=[nlp_agent, pdf_agent],
)

agent = root_agent