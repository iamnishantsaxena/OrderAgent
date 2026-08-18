"""
Extraction Tools for Order Extraction
Regex/heuristic fallback functions called directly by the agent
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def extract_customer_info(text: str) -> Dict[str, Any]:
    """
    Extract customer information from text including name, email, phone, and company.

    Args:
        text: The text to extract customer information from

    Returns:
        Dict with customer information
    """
    result = {
        "customer_name": None,
        "customer_email": None,
        "customer_phone": None,
        "company_name": None,
        "contact_person": None
    }

    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        result["customer_email"] = emails[0]

    # Extract phone numbers
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-555-123-4567
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # 555-123-4567
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            result["customer_phone"] = phones[0]
            break

    # Look for name patterns
    name_keywords = ['from:', 'customer:', 'name:', 'client:', 'contact:', 'attn:']
    for keyword in name_keywords:
        pattern = rf'{keyword}\s*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["customer_name"] = matches[0].strip()
            break

    # Look for company names
    company_keywords = ['company:', 'corp:', 'corporation:', 'inc:', 'ltd:', 'llc:']
    for keyword in company_keywords:
        pattern = rf'{keyword}\s*([A-Z][A-Za-z0-9\s&]+(?:Inc|Corp|Ltd|LLC)?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["company_name"] = matches[0].strip()
            break

    return result


def extract_items(text: str) -> List[Dict[str, Any]]:
    """
    Extract ordered items from text including product names, quantities, and prices.

    Args:
        text: The text to extract items from

    Returns:
        List of item dicts
    """
    items = []

    # Pattern 1: "5 laptops at $1000 each"
    pattern1 = r'(\d+(?:\.\d+)?)\s+([a-zA-Z\s]+?)\s+(?:at|@|for)\s+\$?(\d+(?:\.\d+)?)'
    matches1 = re.findall(pattern1, text, re.IGNORECASE)
    for match in matches1:
        items.append({
            "name": match[1].strip(),
            "quantity": float(match[0]),
            "price": float(match[2]),
            "unit": "unit"
        })

    # Pattern 2: "Product: Widget X, Qty: 10, Price: $50"
    pattern2 = r'(?:product|item):\s*([^,\n]+).*?(?:qty|quantity):\s*(\d+(?:\.\d+)?).*?(?:price|cost):\s*\$?(\d+(?:\.\d+)?)'
    matches2 = re.findall(pattern2, text, re.IGNORECASE)
    for match in matches2:
        items.append({
            "name": match[0].strip(),
            "quantity": float(match[1]),
            "price": float(match[2]),
            "unit": "unit"
        })

    # Pattern 3: "10x Widget A - $25.00"
    pattern3 = r'(\d+)x\s*([^-\n]+?)\s*-\s*\$?(\d+(?:\.\d+)?)'
    matches3 = re.findall(pattern3, text)
    for match in matches3:
        items.append({
            "name": match[1].strip(),
            "quantity": float(match[0]),
            "price": float(match[2]),
            "unit": "unit"
        })

    # Pattern 4: Simple "10 widgets" without price
    if not items:
        pattern4 = r'(\d+(?:\.\d+)?)\s+([a-zA-Z\s]{3,30}?)(?=\s|$|,|\.|\n)'
        matches4 = re.findall(pattern4, text)
        for match in matches4:
            # Filter out common false positives
            if not any(word in match[1].lower() for word in ['page', 'year', 'day', 'month']):
                items.append({
                    "name": match[1].strip(),
                    "quantity": float(match[0]),
                    "price": None,
                    "unit": "unit"
                })

    return items


def extract_addresses(text: str) -> Dict[str, Optional[str]]:
    """
    Extract shipping and billing addresses from text.

    Args:
        text: The text to extract addresses from

    Returns:
        Dict with shipping and billing addresses
    """
    result = {
        "shipping_address": None,
        "billing_address": None
    }

    # Look for shipping address
    shipping_keywords = [
        'ship to:', 'shipping address:', 'delivery address:', 'deliver to:',
        'ship address:', 'shipping:'
    ]
    for keyword in shipping_keywords:
        pattern = rf'{keyword}\s*([^}}\n]+?)(?:\n\n|\n[A-Z]|$)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            result["shipping_address"] = matches[0].strip()
            break

    # Look for billing address
    billing_keywords = [
        'bill to:', 'billing address:', 'invoice address:', 'billing:',
        'bill address:'
    ]
    for keyword in billing_keywords:
        pattern = rf'{keyword}\s*([^}}\n]+?)(?:\n\n|\n[A-Z]|$)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            result["billing_address"] = matches[0].strip()
            break

    # If billing says "same as shipping", copy shipping
    if result["billing_address"] and 'same' in result["billing_address"].lower():
        result["billing_address"] = result["shipping_address"]

    return result


def extract_dates(text: str) -> Dict[str, Optional[str]]:
    """
    Extract relevant dates from text including order date, delivery date, and due date.

    Args:
        text: The text to extract dates from

    Returns:
        Dict with extracted dates
    """
    result = {
        "order_date": None,
        "delivery_date": None,
        "due_date": None
    }

    # Date patterns
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # 2024-01-15
        r'\d{2}/\d{2}/\d{4}',  # 01/15/2024
        r'\d{2}-\d{2}-\d{4}',  # 01-15-2024
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # January 15, 2024
    ]

    # Order date
    order_keywords = ['order date:', 'date:', 'ordered on:', 'placed on:']
    for keyword in order_keywords:
        for pattern in date_patterns:
            full_pattern = rf'{keyword}\s*({pattern})'
            matches = re.findall(full_pattern, text, re.IGNORECASE)
            if matches:
                result["order_date"] = normalize_date(matches[0])
                break
        if result["order_date"]:
            break

    # Delivery date
    delivery_keywords = ['delivery date:', 'deliver by:', 'expected delivery:', 'ship by:']
    for keyword in delivery_keywords:
        for pattern in date_patterns:
            full_pattern = rf'{keyword}\s*({pattern})'
            matches = re.findall(full_pattern, text, re.IGNORECASE)
            if matches:
                result["delivery_date"] = normalize_date(matches[0])
                break
        if result["delivery_date"]:
            break

    # Due date
    due_keywords = ['due date:', 'payment due:', 'due by:', 'payable by:']
    for keyword in due_keywords:
        for pattern in date_patterns:
            full_pattern = rf'{keyword}\s*({pattern})'
            matches = re.findall(full_pattern, text, re.IGNORECASE)
            if matches:
                result["due_date"] = normalize_date(matches[0])
                break
        if result["due_date"]:
            break

    return result


def extract_financial_info(text: str) -> Dict[str, Any]:
    """
    Extract financial information including amounts, payment terms, and currency.

    Args:
        text: The text to extract financial information from

    Returns:
        Dict with financial information
    """
    result = {
        "total_amount": None,
        "subtotal": None,
        "tax_amount": None,
        "currency": "USD",
        "payment_terms": None,
        "payment_method": None
    }

    # Extract total amount
    total_patterns = [
        r'\btotal:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'grand total:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'amount due:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
    ]
    for pattern in total_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["total_amount"] = float(matches[0].replace(',', ''))
            break

    # Extract subtotal
    subtotal_pattern = r'subtotal:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
    matches = re.findall(subtotal_pattern, text, re.IGNORECASE)
    if matches:
        result["subtotal"] = float(matches[0].replace(',', ''))

    # Extract tax
    tax_pattern = r'tax:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
    matches = re.findall(tax_pattern, text, re.IGNORECASE)
    if matches:
        result["tax_amount"] = float(matches[0].replace(',', ''))

    # Detect currency
    currencies = {
        r'\$': 'USD',
        r'€': 'EUR',
        r'£': 'GBP',
        r'₹': 'INR',
        r'USD': 'USD',
        r'EUR': 'EUR',
        r'GBP': 'GBP'
    }
    for pattern, currency in currencies.items():
        if re.search(pattern, text):
            result["currency"] = currency
            break

    # Payment terms
    payment_terms = {
        r'net\s*30': 'Net 30',
        r'net\s*60': 'Net 60',
        r'net\s*90': 'Net 90',
        r'due on receipt': 'Due on Receipt',
        r'prepaid': 'Prepaid',
        r'cod|cash on delivery': 'Cash on Delivery'
    }
    for pattern, term in payment_terms.items():
        if re.search(pattern, text, re.IGNORECASE):
            result["payment_terms"] = term
            break

    return result


def validate_order_data(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate extracted order data and identify issues.

    Args:
        order: The extracted order dict

    Returns:
        Dict with validation results
    """
    errors = []
    warnings = []

    # Check critical fields
    if not order.get("customer_name") and not order.get("company_name"):
        errors.append("Missing customer name or company name")

    if not order.get("items") or len(order.get("items", [])) == 0:
        errors.append("No items found in order")

    # Validate items
    for idx, item in enumerate(order.get("items", [])):
        if not item.get("name"):
            errors.append(f"Item {idx + 1} missing name")
        if not item.get("quantity") or item.get("quantity", 0) <= 0:
            errors.append(f"Item {idx + 1} has invalid quantity")
        if item.get("price") is not None and item.get("price") < 0:
            warnings.append(f"Item {idx + 1} has negative price")

    # Validate amounts
    if order.get("total_amount") is not None and order.get("total_amount") < 0:
        errors.append("Total amount is negative")

    # Validate dates
    date_fields = ["order_date", "delivery_date", "due_date"]
    for field in date_fields:
        if order.get(field):
            if not is_valid_date(order[field]):
                warnings.append(f"{field} is in invalid format")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "can_create_order": len(errors) == 0
    }


def calculate_confidence(extracted_data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """
    Calculate confidence scores for extracted data based on how explicitly it's stated.

    Args:
        extracted_data: The extracted data dict
        original_text: Original input text

    Returns:
        Dict with confidence scores
    """
    field_confidence = {}

    # Calculate confidence for each field
    for key, value in extracted_data.items():
        if value is None or value == "":
            field_confidence[key] = 0.0
        elif isinstance(value, list):
            if len(value) > 0:
                field_confidence[key] = 0.8  # Found items
            else:
                field_confidence[key] = 0.0
        else:
            # Check if value appears in original text
            if str(value).lower() in original_text.lower():
                field_confidence[key] = 0.9  # High confidence - exact match
            else:
                field_confidence[key] = 0.6  # Medium confidence - derived

    # Calculate overall confidence
    if field_confidence:
        overall = sum(field_confidence.values()) / len(field_confidence)
    else:
        overall = 0.0

    return {
        "overall_confidence": round(overall, 2),
        "field_confidence": field_confidence
    }


# Helper functions

def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date to YYYY-MM-DD format"""
    from dateutil import parser

    try:
        parsed = parser.parse(date_str)
        return parsed.strftime("%Y-%m-%d")
    except:
        return date_str  # Return original if parsing fails


def is_valid_date(date_str: str) -> bool:
    """Check if string is a valid date"""
    from dateutil import parser

    try:
        parser.parse(date_str)
        return True
    except:
        return False


# List of all extraction/validation functions
AGENT_TOOLS = [
    extract_customer_info,
    extract_items,
    extract_addresses,
    extract_dates,
    extract_financial_info,
    validate_order_data,
    calculate_confidence
]
