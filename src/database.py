"""
Database Module for Order Storage (Optional)
Stores extracted orders in SQLite database
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .config import config


class OrderDatabase:
    """SQLite database for storing extracted orders"""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure database directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT,
                customer_name TEXT,
                customer_email TEXT,
                company_name TEXT,
                total_amount REAL,
                currency TEXT,
                order_date TEXT,
                delivery_date TEXT,
                payment_terms TEXT,
                shipping_address TEXT,
                billing_address TEXT,
                can_create_order BOOLEAN,
                confidence REAL,
                source_type TEXT,
                created_at TEXT,
                order_json TEXT,
                extraction_result TEXT
            )
        """)
        
        # Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_name TEXT,
                quantity REAL,
                unit TEXT,
                price REAL,
                subtotal REAL,
                sku TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        """)
        
        # Extraction logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_type TEXT,
                input_length INTEGER,
                success BOOLEAN,
                error_message TEXT,
                processing_time REAL,
                created_at TEXT
            )
        """)
        
        self.conn.commit()
    
    def save_order(self, extraction_result: Dict) -> int:
        """
        Save extracted order to database
        
        Args:
            extraction_result: Complete extraction result dictionary
            
        Returns:
            Order ID
        """
        cursor = self.conn.cursor()
        
        order_data = extraction_result.get("order", {})
        
        # Insert order
        cursor.execute("""
            INSERT INTO orders (
                order_number, customer_name, customer_email, company_name,
                total_amount, currency, order_date, delivery_date,
                payment_terms, shipping_address, billing_address,
                can_create_order, confidence, source_type, created_at,
                order_json, extraction_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_data.get("order_number"),
            order_data.get("customer_name"),
            order_data.get("customer_email"),
            order_data.get("company_name"),
            order_data.get("total_amount"),
            order_data.get("currency", "USD"),
            order_data.get("order_date"),
            order_data.get("delivery_date"),
            order_data.get("payment_terms"),
            order_data.get("shipping_address"),
            order_data.get("billing_address"),
            extraction_result.get("can_create_order", False),
            extraction_result.get("confidence", 0.0),
            extraction_result.get("extraction_metadata", {}).get("source_type", "unknown"),
            datetime.now().isoformat(),
            json.dumps(order_data),
            json.dumps(extraction_result)
        ))
        
        order_id = cursor.lastrowid
        
        # Insert items
        for item in order_data.get("items", []):
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, item_name, quantity, unit, price, subtotal, sku
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item.get("name"),
                item.get("quantity"),
                item.get("unit", "unit"),
                item.get("price"),
                item.get("subtotal"),
                item.get("sku")
            ))
        
        self.conn.commit()
        return order_id
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """
        Retrieve order by ID
        
        Args:
            order_id: Order ID
            
        Returns:
            Order dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        order = dict(row)
        
        # Get items
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = [dict(item_row) for item_row in cursor.fetchall()]
        order["items"] = items
        
        return order
    
    def search_orders(
        self,
        customer_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search orders with filters
        
        Args:
            customer_name: Filter by customer name (partial match)
            start_date: Filter by created date (from)
            end_date: Filter by created date (to)
            min_amount: Minimum total amount
            max_amount: Maximum total amount
            limit: Maximum number of results
            
        Returns:
            List of order dictionaries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        if customer_name:
            query += " AND (customer_name LIKE ? OR company_name LIKE ?)"
            params.extend([f"%{customer_name}%", f"%{customer_name}%"])
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        if min_amount is not None:
            query += " AND total_amount >= ?"
            params.append(min_amount)
        
        if max_amount is not None:
            query += " AND total_amount <= ?"
            params.append(max_amount)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        orders = [dict(row) for row in cursor.fetchall()]
        
        return orders
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total orders
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        stats["total_orders"] = cursor.fetchone()["count"]
        
        # Valid orders
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE can_create_order = 1")
        stats["valid_orders"] = cursor.fetchone()["count"]
        
        # Total value
        cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE total_amount IS NOT NULL")
        result = cursor.fetchone()
        stats["total_value"] = result["total"] or 0.0
        
        # Average confidence
        cursor.execute("SELECT AVG(confidence) as avg FROM orders")
        result = cursor.fetchone()
        stats["avg_confidence"] = result["avg"] or 0.0
        
        # Recent orders
        cursor.execute("""
            SELECT COUNT(*) as count FROM orders 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        stats["orders_last_7_days"] = cursor.fetchone()["count"]
        
        return stats
    
    def log_extraction(
        self,
        input_type: str,
        input_length: int,
        success: bool,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None
    ):
        """
        Log extraction attempt
        
        Args:
            input_type: Type of input (text, email, pdf)
            input_length: Length of input in characters
            success: Whether extraction succeeded
            error_message: Error message if failed
            processing_time: Processing time in seconds
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO extraction_logs (
                input_type, input_length, success, error_message,
                processing_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            input_type,
            input_length,
            success,
            error_message,
            processing_time,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Example usage
if __name__ == "__main__":
    # Create database
    db = OrderDatabase()
    
    # Example order
    example_result = {
        "can_create_order": True,
        "confidence": 0.85,
        "order": {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "company_name": "Acme Corp",
            "items": [
                {
                    "name": "Widget A",
                    "quantity": 10,
                    "price": 25.0,
                    "subtotal": 250.0,
                    "unit": "pcs"
                }
            ],
            "total_amount": 250.0,
            "currency": "USD",
            "payment_terms": "Net 30"
        }
    }
    
    # Save order
    order_id = db.save_order(example_result)
    print(f"Saved order with ID: {order_id}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Database stats: {stats}")
    
    db.close()
