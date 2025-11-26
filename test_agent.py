from agent import agent

# Test with a sample order
sample_order = """
Purchase Order Request
From: Restaurant Supply Co.
Date: June 15, 2025

Please send:
- 10 cases of Coca-Cola 330ml cans
- 5 cases of Sprite 500ml bottles  
- 20 bottles of Heinz Ketchup 1L
- 15 kg of ground coffee beans

Total: $1,250.00
Deliver to: John's Restaurant, 123 Main St
"""

sample1 = """I need 10 cases of Coke, 5 cases of Sprite, and 20 bottles of ketchup.
Total around $300. Deliver to 123 Main St next Tuesday."""

# response = agent.query(sample_order)
response = agent.predict("Process this purchase order:\n" + sample1)

"""
agent.run(text)
agent.predict(text)     
agent.query(text)        
agent.generate(text)      
"""

print(response)

# Simple usage

# Response is a dict matching OrderProcessingResult schema
print(response['status'])          # 'success', 'partial', or 'failed'
print(response['order_data'])      # Extracted order info
print(response['validation'])      # Validation report