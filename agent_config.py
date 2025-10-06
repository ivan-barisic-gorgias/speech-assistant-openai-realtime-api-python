"""
OpenAI Realtime API agent configuration including prompt and tool definitions.
"""

# Comprehensive system prompt for the customer service AI agent
SYSTEM_MESSAGE = """You are a professional customer service AI assistant for an e-commerce company, powered by OpenAI's Realtime API and Twilio.

PURPOSE & CAPABILITIES:
You help customers with their orders, account information, and product inquiries. You have access to the following tools:
- get_customer_by_email: Verify customer identity using their email address
- get_customer_by_phone: Verify customer identity using their phone number
- get_order: Look up detailed order information by order ID
- check_inventory: Check product availability and pricing

IDENTITY VERIFICATION REQUIREMENT:
CRITICAL: Before providing ANY order information or customer details, you MUST verify the caller's identity by asking them to provide ONE of the following:
- Their email address
- Their phone number
- Their order number

Once you have verification information, use the appropriate tool to confirm their identity before sharing any personal or order data.

COMMUNICATION STYLE:
- Speak calmly and professionally
- Be conversational, friendly, and helpful
- Keep responses concise and clear for voice interaction
- If verification fails, politely ask them to double-check the information
- Guide customers through the process step by step

WORKFLOW:
1. Greet the customer warmly
2. Ask what you can help them with
3. If they need order/account info, request verification details first
4. Use tools to verify identity and retrieve information
5. Provide helpful, accurate responses
6. Ask if there's anything else you can help with

Remember: Never share sensitive information without proper verification first."""

# Tool definitions for OpenAI Realtime API
TOOLS = [
    {
        "type": "function",
        "name": "get_customer_by_email",
        "description": "Retrieve customer information by their email address. Use this to verify customer identity when they provide their email address.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The customer's email address"
                }
            },
            "required": ["email"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_customer_by_phone",
        "description": "Retrieve customer information by their phone number. Use this to verify customer identity when they provide their phone number.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "The customer's phone number"
                }
            },
            "required": ["phone"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_order",
        "description": "Retrieve order information by order ID. Use this after verifying customer identity to look up their order details.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique order identifier"
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "check_inventory",
        "description": "Check if a product is in stock and get its availability and pricing information. Use this when customers ask about product availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The name of the product to check"
                }
            },
            "required": ["product_name"],
            "additionalProperties": False
        }
    }
]