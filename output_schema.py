"""
Output Schema for Order Intelligence Agent
Defines the structured JSON format for parsed orders
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

class OrderItem(BaseModel):
    """Individual item in a purchase order"""
    product_name: str = Field(
        description="Full product name including brand, size, and type (e.g., 'Coca-Cola 330ml cans 24-pack')"
    )
    quantity: float = Field(
        description="Numeric quantity ordered",
        gt=0
    )
    unit: str = Field(
        description="Unit of measurement (e.g., 'cases', 'bottles', 'kg', 'liters', 'boxes')"
    )
    sku: Optional[str] = Field(
        default=None,
        description="Stock Keeping Unit code if identifiable"
    )
    unit_price: Optional[float] = Field(
        default=None,
        description="Price per unit if available",
        ge=0
    )
    line_total: Optional[float] = Field(
        default=None,
        description="Total price for this line item",
        ge=0
    )

class ValidationReport(BaseModel):
    """Validation status of extracted order data"""
    is_valid: bool = Field(
        description="Whether the extracted data is complete and valid"
    )
    completeness_score: int = Field(
        description="Percentage score (0-100) indicating data completeness",
        ge=0,
        le=100
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of critical missing fields"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings about ambiguous or suspicious data"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving data quality"
    )

class OrderData(BaseModel):
    """Complete structured purchase order data"""
    vendor: Optional[str] = Field(
        default=None,
        description="Vendor/Supplier company name"
    )
    customer: Optional[str] = Field(
        default=None,
        description="Customer/Restaurant name"
    )
    order_date: Optional[str] = Field(
        default=None,
        description="Date order was placed (YYYY-MM-DD format)"
    )
    delivery_date: Optional[str] = Field(
        default=None,
        description="Requested delivery date (YYYY-MM-DD format)"
    )
    items: List[OrderItem] = Field(
        description="List of ordered items with quantities and details"
    )
    total_amount: Optional[float] = Field(
        default=None,
        description="Total order amount in dollars",
        ge=0
    )
    delivery_address: Optional[str] = Field(
        default=None,
        description="Full delivery address"
    )
    special_instructions: Optional[str] = Field(
        default=None,
        description="Any special delivery or handling instructions"
    )
    contact_email: Optional[str] = Field(
        default=None,
        description="Contact email address"
    )
    contact_phone: Optional[str] = Field(
        default=None,
        description="Contact phone number"
    )
    confidence: str = Field(
        description="Overall confidence level: 'high', 'medium', or 'low'",
        pattern="^(high|medium|low)$"
    )

class OrderProcessingResult(BaseModel):
    """Final output from the Order Intelligence Agent"""
    status: str = Field(
        description="Processing status: 'success', 'partial', or 'failed'",
        pattern="^(success|partial|failed)$"
    )
    extraction_method: str = Field(
        description="Which agent(s) were used (e.g., 'NLP_Extraction_Agent', 'Email_Parsing_Agent + NLP_Extraction_Agent')"
    )
    order_data: OrderData = Field(
        description="Extracted and structured order information"
    )
    validation: ValidationReport = Field(
        description="Validation results for the extracted data"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps or actions needed (e.g., 'Verify delivery address', 'Confirm SKU for Item 3')"
    )


# Example output for reference
EXAMPLE_OUTPUT = {
    "status": "success",
    "extraction_method": "Email_Parsing_Agent + NLP_Extraction_Agent",
    "order_data": {
        "vendor": "Sysco Food Services",
        "customer": "John's Restaurant",
        "order_date": "2025-06-15",
        "delivery_date": "2025-06-17",
        "items": [
            {
                "product_name": "Coca-Cola 330ml cans 24-pack",
                "quantity": 10,
                "unit": "cases",
                "sku": "CC-330-24",
                "unit_price": 18.50,
                "line_total": 185.00
            },
            {
                "product_name": "Sprite 500ml bottles 12-pack",
                "quantity": 5,
                "unit": "cases",
                "sku": "SP-500-12",
                "unit_price": 22.00,
                "line_total": 110.00
            },
            {
                "product_name": "Heinz Ketchup 1L bottle",
                "quantity": 20,
                "unit": "bottles",
                "sku": "HZ-KTC-1L",
                "unit_price": 4.50,
                "line_total": 90.00
            },
            {
                "product_name": "Colombian Ground Coffee",
                "quantity": 15,
                "unit": "kg",
                "sku": None,
                "unit_price": 12.00,
                "line_total": 180.00
            }
        ],
        "total_amount": 565.00,
        "delivery_address": "123 Main Street, Sydney NSW 2000",
        "special_instructions": "Deliver to back entrance, morning preferred",
        "contact_email": "orders@johnsrestaurant.com",
        "contact_phone": "+61 2 1234 5678",
        "confidence": "high"
    },
    "validation": {
        "is_valid": True,
        "completeness_score": 95,
        "missing_fields": [],
        "warnings": [
            "SKU missing for Colombian Ground Coffee - requires catalog lookup"
        ],
        "suggestions": [
            "Confirm delivery time window with customer"
        ]
    },
    "next_steps": [
        "Lookup SKU for Colombian Ground Coffee in product catalog",
        "Send order confirmation to customer",
        "Schedule delivery for June 17, 2025"
    ]
}