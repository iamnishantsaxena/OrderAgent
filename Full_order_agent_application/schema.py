"""
Order Schema Definitions
Defines the structured output format for extracted orders
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum


class PaymentTerms(str, Enum):
    """Common payment terms"""
    NET_30 = "Net 30"
    NET_60 = "Net 60"
    NET_90 = "Net 90"
    DUE_ON_RECEIPT = "Due on Receipt"
    PREPAID = "Prepaid"
    COD = "Cash on Delivery"
    CREDIT_CARD = "Credit Card"
    OTHER = "Other"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"
    OTHER = "OTHER"


class OrderItem(BaseModel):
    """Individual item in an order"""
    name: str = Field(description="Product or service name")
    quantity: float = Field(default=1.0, description="Quantity ordered")
    unit: Optional[str] = Field(default="unit", description="Unit of measurement (pcs, kg, boxes, etc.)")
    price: Optional[float] = Field(default=None, description="Unit price")
    subtotal: Optional[float] = Field(default=None, description="Item subtotal (quantity * price)")
    description: Optional[str] = Field(default=None, description="Additional item details")
    sku: Optional[str] = Field(default=None, description="SKU or product code")
    
    @model_validator(mode='after')
    def calculate_subtotal(self):
        """Auto-calculate subtotal if not provided"""
        if self.subtotal is None and self.price is not None and self.quantity is not None:
            self.subtotal = round(self.price * self.quantity, 2)
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Laptop Pro 15",
                "quantity": 5,
                "unit": "pcs",
                "price": 1000.00,
                "subtotal": 5000.00,
                "sku": "LAP-PRO-15"
            }
        }


class CustomerInfo(BaseModel):
    """Customer information"""
    name: Optional[str] = Field(default=None, description="Customer full name or company name")
    email: Optional[str] = Field(default=None, description="Customer email address")
    phone: Optional[str] = Field(default=None, description="Customer phone number")
    company: Optional[str] = Field(default=None, description="Company name if different from customer name")
    contact_person: Optional[str] = Field(default=None, description="Contact person name")


class Address(BaseModel):
    """Address structure"""
    full_address: Optional[str] = Field(default=None, description="Complete address as single string")
    street: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    postal_code: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)


class Order(BaseModel):
    """Complete order structure"""
    # Customer Information
    customer_name: Optional[str] = Field(default=None, description="Customer name or company")
    customer_email: Optional[str] = Field(default=None, description="Customer email")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone")
    company_name: Optional[str] = Field(default=None, description="Company name")
    contact_person: Optional[str] = Field(default=None, description="Contact person")
    
    # Items
    items: List[OrderItem] = Field(default_factory=list, description="List of ordered items")
    
    # Addresses
    shipping_address: Optional[str] = Field(default=None, description="Shipping address")
    billing_address: Optional[str] = Field(default=None, description="Billing address")
    
    # Dates
    order_date: Optional[str] = Field(default=None, description="Order date (YYYY-MM-DD)")
    delivery_date: Optional[str] = Field(default=None, description="Expected delivery date")
    due_date: Optional[str] = Field(default=None, description="Payment due date")
    
    # Financial
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(default=None, description="Tax amount")
    shipping_cost: Optional[float] = Field(default=None, description="Shipping cost")
    discount: Optional[float] = Field(default=None, description="Discount amount")
    total_amount: Optional[float] = Field(default=None, description="Final total amount")
    currency: str = Field(default="USD", description="Currency code")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    
    # References
    order_number: Optional[str] = Field(default=None, description="Order/PO number")
    invoice_number: Optional[str] = Field(default=None, description="Invoice number")
    reference: Optional[str] = Field(default=None, description="Customer reference")
    
    # Additional
    notes: Optional[str] = Field(default=None, description="Additional notes or comments")
    special_instructions: Optional[str] = Field(default=None, description="Special delivery/handling instructions")
    urgency: Optional[str] = Field(default=None, description="Urgency level (normal, urgent, rush)")
    
    # Extensibility
    extras: Dict[str, Any] = Field(default_factory=dict, description="Additional custom fields")

    @model_validator(mode='after')
    def calculate_total(self):
        """Auto-calculate total if not provided"""
        if self.total_amount is None:
            total = self.subtotal or 0.0
            total += self.tax_amount or 0.0
            total += self.shipping_cost or 0.0
            total -= self.discount or 0.0
            self.total_amount = round(total, 2) if total > 0 else None
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "items": [
                    {
                        "name": "Widget A",
                        "quantity": 10,
                        "price": 25.00,
                        "subtotal": 250.00
                    }
                ],
                "shipping_address": "123 Main St, City, State 12345",
                "total_amount": 250.00,
                "currency": "USD"
            }
        }


class ExtractionResult(BaseModel):
    """Complete extraction result with metadata"""
    can_create_order: bool = Field(description="Whether order creation is possible")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence score")
    missing_fields: List[str] = Field(default_factory=list, description="List of critical missing fields")
    order: Order = Field(description="Extracted order data")
    field_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence score for each extracted field"
    )
    warnings: List[str] = Field(default_factory=list, description="Warnings about data quality")
    extraction_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about extraction process"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "can_create_order": True,
                "confidence": 0.85,
                "missing_fields": ["delivery_date"],
                "order": {
                    "customer_name": "Acme Corp",
                    "items": [{"name": "Product X", "quantity": 5, "price": 100}],
                    "total_amount": 500
                },
                "field_confidence": {
                    "customer_name": 0.95,
                    "items": 0.90
                }
            }
        }


# Required fields for order creation
CRITICAL_FIELDS = [
    "customer_name",
    "items"
]

# Fields that should have high confidence
HIGH_CONFIDENCE_FIELDS = [
    "customer_name",
    "customer_email",
    "items",
    "total_amount"
]

# Confidence thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.5
CONFIDENCE_THRESHOLD_LOW = 0.3


def validate_order_completeness(order: Order) -> tuple[bool, List[str]]:
    """
    Validate if order has minimum required fields
    Returns: (is_valid, missing_critical_fields)
    """
    missing = []
    
    if not order.customer_name and not order.company_name:
        missing.append("customer_name or company_name")
    
    if not order.items or len(order.items) == 0:
        missing.append("items")
    
    return len(missing) == 0, missing


def calculate_overall_confidence(field_confidence: Dict[str, float]) -> float:
    """Calculate overall confidence score from field confidences"""
    if not field_confidence:
        return 0.0
    
    # Weight important fields more heavily
    weighted_sum = 0.0
    weight_total = 0.0
    
    for field, confidence in field_confidence.items():
        weight = 2.0 if field in HIGH_CONFIDENCE_FIELDS else 1.0
        weighted_sum += confidence * weight
        weight_total += weight
    
    return round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0
