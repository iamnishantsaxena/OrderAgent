from agent import agent
import json
from typing import Dict, Any

class OrderProcessor:
    def __init__(self):
        self.agent = agent
        
    def process_order(self, input_text: str, source_type: str = "text") -> Dict[str, Any]:
        """
        Process an order through the agent pipeline
        
        Args:
            input_text: The order content (email, PDF text, or plain text)
            source_type: "text", "email", or "pdf"
        
        Returns:
            Dict with structured order data
        """
        try:
            # Add context about source type
            prompt = f"[Source Type: {source_type}]\n\n{input_text}"
            
            # Query the agent
            response = self.agent.query(prompt)
            
            # Parse response (ADK should return structured data)
            result = self._parse_response(response)
            
            return {
                "success": True,
                "data": result,
                "raw_response": str(response)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse the agent's response into structured format"""
        # ADK may return the response differently - adjust as needed
        if isinstance(response, str):
            # Try to extract JSON from string response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_text": response}
        return response

# Example usage
if __name__ == "__main__":
    processor = OrderProcessor()
    
    sample_order = """
    From: suppliers@sysco.com
    To: orders@johnsrestaurant.com
    Subject: Weekly Order - June 15, 2025
    
    Hi John,
    
    Confirming your weekly order:
    
    - 10 cases Coca-Cola 330ml (24-pack)
    - 5 cases Sprite 500ml (12-pack)
    - 20 bottles Heinz Ketchup 1L
    - 15 kg Colombian Ground Coffee
    
    Total: $1,250.00
    Delivery: June 17, 2025
    
    Thanks!
    Sysco Team
    """
    
    result = processor.process_order(sample_order, source_type="email")
    print(json.dumps(result, indent=2))