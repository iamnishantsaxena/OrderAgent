"""
Streamlit UI for Order Extraction Agent
Main application interface
"""

import streamlit as st
import json
import time
from datetime import datetime
from io import BytesIO
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import OrderExtractionAgent
from src.pdf_processor import PDFValidator

# Page configuration
st.set_page_config(
    page_title="Order Extraction Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
    }
    .metric-card {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None
if "processing" not in st.session_state:
    st.session_state.processing = False


def initialize_agent():
    """Initialize the order extraction agent"""
    if st.session_state.agent is None:
        with st.spinner("Initializing agent... (This may take a moment)"):
            try:
                st.session_state.agent = OrderExtractionAgent(
                    model_name=st.session_state.get("model_name", "llama3.2:latest"),
                    temperature=st.session_state.get("temperature", 0.1),
                    verbose=True
                )
                st.success("✅ Agent initialized successfully!")
                return True
            except Exception as e:
                st.error(f"❌ Failed to initialize agent: {e}")
                st.info("💡 Make sure Ollama is running and llama3.2:latest is pulled")
                return False
    return True


def display_result(result: dict):
    """Display extraction results in a nice format"""
    if not result:
        return
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        can_create = result.get("can_create_order", False)
        status_color = "🟢" if can_create else "🔴"
        st.metric("Order Status", f"{status_color} {'Valid' if can_create else 'Invalid'}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        confidence = result.get("confidence", 0.0)
        st.metric("Confidence", f"{confidence:.0%}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        items_count = len(result.get("order", {}).get("items", []))
        st.metric("Items Found", items_count)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        missing_count = len(result.get("missing_fields", []))
        st.metric("Missing Fields", missing_count)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Order Details",
        "📊 Confidence Scores",
        "⚠️ Validation",
        "🔍 Raw JSON"
    ])
    
    with tab1:
        display_order_details(result.get("order", {}))
    
    with tab2:
        display_confidence_scores(result.get("field_confidence", {}))
    
    with tab3:
        display_validation(result)
    
    with tab4:
        st.json(result)


def display_order_details(order: dict):
    """Display order details in a structured format"""
    if not order:
        st.warning("No order data available")
        return
    
    # Customer Information
    st.subheader("👤 Customer Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Customer Name", value=order.get("customer_name") or "N/A", disabled=True)
        st.text_input("Company", value=order.get("company_name") or "N/A", disabled=True)
        st.text_input("Email", value=order.get("customer_email") or "N/A", disabled=True)
    
    with col2:
        st.text_input("Phone", value=order.get("customer_phone") or "N/A", disabled=True)
        st.text_input("Contact Person", value=order.get("contact_person") or "N/A", disabled=True)
    
    # Items
    st.subheader("🛒 Order Items")
    items = order.get("items", [])
    
    if items:
        for idx, item in enumerate(items, 1):
            with st.expander(f"Item {idx}: {item.get('name', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Quantity", f"{item.get('quantity', 0)} {item.get('unit', 'units')}")
                with col2:
                    price = item.get('price')
                    st.metric("Unit Price", f"${price:.2f}" if price else "N/A")
                with col3:
                    subtotal = item.get('subtotal')
                    st.metric("Subtotal", f"${subtotal:.2f}" if subtotal else "N/A")
    else:
        st.warning("No items found")
    
    # Addresses
    st.subheader("📍 Addresses")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_area("Shipping Address", value=order.get("shipping_address") or "N/A", height=100, disabled=True)
    
    with col2:
        st.text_area("Billing Address", value=order.get("billing_address") or "N/A", height=100, disabled=True)
    
    # Financial Information
    st.subheader("💰 Financial Details")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        subtotal = order.get("subtotal")
        st.metric("Subtotal", f"${subtotal:.2f}" if subtotal else "N/A")
    
    with col2:
        tax = order.get("tax_amount")
        st.metric("Tax", f"${tax:.2f}" if tax else "N/A")
    
    with col3:
        shipping = order.get("shipping_cost")
        st.metric("Shipping", f"${shipping:.2f}" if shipping else "N/A")
    
    with col4:
        total = order.get("total_amount")
        currency = order.get("currency", "USD")
        st.metric("Total", f"{currency} ${total:.2f}" if total else "N/A")
    
    # Additional Information
    with st.expander("📝 Additional Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Order Date", value=order.get("order_date") or "N/A", disabled=True)
            st.text_input("Delivery Date", value=order.get("delivery_date") or "N/A", disabled=True)
            st.text_input("Payment Terms", value=order.get("payment_terms") or "N/A", disabled=True)
        
        with col2:
            st.text_input("Order Number", value=order.get("order_number") or "N/A", disabled=True)
            st.text_input("Invoice Number", value=order.get("invoice_number") or "N/A", disabled=True)
            st.text_input("Reference", value=order.get("reference") or "N/A", disabled=True)
        
        notes = order.get("notes")
        if notes:
            st.text_area("Notes", value=notes, height=100, disabled=True)


def display_confidence_scores(scores: dict):
    """Display confidence scores with visual indicators"""
    if not scores:
        st.info("No confidence scores available")
        return
    
    st.markdown("### Field Confidence Levels")
    
    for field, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        # Color coding based on confidence
        if score >= 0.8:
            color = "#28a745"  # Green
            label = "High"
        elif score >= 0.5:
            color = "#ffc107"  # Yellow
            label = "Medium"
        else:
            color = "#dc3545"  # Red
            label = "Low"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(score, text=f"**{field}**: {score:.0%} ({label})")
        with col2:
            st.markdown(f'<span style="color: {color}; font-weight: bold;">{label}</span>', unsafe_allow_html=True)


def display_validation(result: dict):
    """Display validation results and warnings"""
    can_create = result.get("can_create_order", False)
    missing_fields = result.get("missing_fields", [])
    warnings = result.get("warnings", [])
    
    if can_create:
        st.markdown('<div class="success-box">✅ <strong>Order is valid and can be created</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ <strong>Order cannot be created</strong></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Missing fields
    if missing_fields:
        st.subheader("❗ Missing Critical Fields")
        for field in missing_fields:
            st.markdown(f"- **{field}**")
    else:
        st.success("All critical fields present!")
    
    # Warnings
    if warnings:
        st.subheader("⚠️ Warnings")
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No warnings")


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">📦 Order Extraction Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-powered order extraction from text, emails, and PDFs</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_name = st.selectbox(
            "Ollama Model",
            ["llama3.2:latest", "llama3.2:1b", "llama3.2:3b"],
            index=0,
            help="Select the Ollama model to use"
        )
        st.session_state.model_name = model_name
        
        # Temperature
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.1,
            help="Lower values = more deterministic"
        )
        st.session_state.temperature = temperature
        
        st.markdown("---")
        
        # Initialize button
        if st.button("🔄 Initialize Agent", use_container_width=True):
            st.session_state.agent = None
            initialize_agent()
        
        st.markdown("---")
        
        # Info
        st.info("""
        **How to use:**
        1. Initialize the agent
        2. Upload a PDF or paste text
        3. Click "Generate Order JSON"
        4. Review the results
        """)
        
        st.markdown("---")
        
        # Status
        if st.session_state.agent:
            st.success("✅ Agent Ready")
        else:
            st.warning("⚠️ Agent Not Initialized")
    
    # Main content area
    if not initialize_agent():
        st.stop()
    
    # Input method selection
    input_method = st.radio(
        "Select Input Method",
        ["📄 Upload PDF", "📝 Paste Text/Email"],
        horizontal=True
    )
    
    input_text = None
    pdf_file = None
    
    if input_method == "📄 Upload PDF":
        pdf_file = st.file_uploader(
            "Upload PDF Document",
            type=["pdf"],
            help="Upload a PDF containing order information"
        )
        
        if pdf_file:
            # Validate PDF
            is_valid, error = PDFValidator.is_valid_pdf(pdf_file)
            if not is_valid:
                st.error(f"Invalid PDF: {error}")
                st.stop()
            
            is_valid, error = PDFValidator.check_file_size(pdf_file, max_size_mb=10.0)
            if not is_valid:
                st.error(f"File too large: {error}")
                st.stop()
            
            st.success(f"✅ PDF uploaded: {pdf_file.name}")
    
    else:
        input_text = st.text_area(
            "Paste your text or email content",
            height=300,
            placeholder="""Example:
From: john@example.com
Order for 10 laptops at $1000 each
Ship to: 123 Main St, City, State 12345
Payment: Net 30
""",
            help="Paste email content, text message, or any unstructured order information"
        )
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        extract_button = st.button(
            "🚀 Generate Order JSON",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.processing
        )
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.extraction_result = None
            st.rerun()
    
    # Process extraction
    if extract_button:
        if not pdf_file and not input_text:
            st.error("Please provide input (PDF or text)")
            st.stop()
        
        st.session_state.processing = True
        
        # Progress container
        progress_container = st.container()
        result_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Processing...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                if pdf_file:
                    # Process PDF
                    status_text.text("📄 Processing PDF...")
                    progress_bar.progress(20)
                    
                    result = st.session_state.agent.process_pdf(pdf_file)
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                
                else:
                    # Process text with streaming
                    status_text.text("🤖 Extracting information...")
                    
                    step_progress = 0
                    for update in st.session_state.agent.extract_order_streaming(input_text):
                        status = update.get("status")
                        
                        if status == "progress":
                            step = update.get("step", 0)
                            total = update.get("total_steps", 5)
                            progress = int((step / total) * 100)
                            progress_bar.progress(progress)
                        
                        elif status in ["extracting", "refining", "validating", "scoring", "finalizing"]:
                            status_text.text(f"🔄 {update.get('message')}")
                        
                        elif status == "complete":
                            result = update.get("result")
                            progress_bar.progress(100)
                            status_text.text("✅ Complete!")
                            break
                        
                        elif status == "error":
                            st.error(f"Error: {update.get('error')}")
                            st.stop()
                
                time.sleep(0.5)  # Brief pause to show completion
                progress_container.empty()
                
                # Store and display result
                st.session_state.extraction_result = result
                
            except Exception as e:
                st.error(f"❌ Extraction failed: {e}")
                import traceback
                with st.expander("Show error details"):
                    st.code(traceback.format_exc())
            
            finally:
                st.session_state.processing = False
    
    # Display results
    if st.session_state.extraction_result:
        st.markdown("---")
        st.markdown("## 📊 Extraction Results")
        display_result(st.session_state.extraction_result)
        
        # Download button
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            json_str = json.dumps(st.session_state.extraction_result, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name=f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
