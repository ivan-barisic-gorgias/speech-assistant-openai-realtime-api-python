"""
Function handlers for OpenAI Realtime API agent function calls.
These implementations use mock data to simulate real backend systems.
"""

import json
import time
from mock_data import CUSTOMERS, ORDERS, INVENTORY


# Function routing map
FUNCTION_MAP = {
    'get_customer_by_email': lambda args: handle_get_customer_by_email(args.get('email', '')),
    'get_customer_by_phone': lambda args: handle_get_customer_by_phone(args.get('phone', '')),
    'get_order': lambda args: handle_get_order(args.get('order_id', '')),
    'check_inventory': lambda args: handle_check_inventory(args.get('product_name', ''))
}


def handle_function_call(function_name, arguments_dict):
    """
    Main entry point for handling function calls from OpenAI Realtime API.

    Args:
        function_name: Name of the function to call
        arguments_dict: Dictionary containing function arguments

    Returns:
        tuple: (result dict or None, error message or None)
    """
    print(f"[OPENAI TOOL] {function_name} called with args: {arguments_dict}")

    # Route to appropriate handler
    handler = FUNCTION_MAP.get(function_name)

    if handler is None:
        error_msg = f"Unknown function: {function_name}. Available functions: {list(FUNCTION_MAP.keys())}"
        print(f"[OPENAI TOOL] ERROR: {error_msg}")
        return None, error_msg

    try:
        result = handler(arguments_dict)
        print(f"[OPENAI TOOL] SUCCESS: {function_name} returned: {result}")
        return result, None
    except Exception as e:
        error_msg = f"Error executing {function_name}: {e}"
        print(f"[OPENAI TOOL] ERROR: {error_msg}")
        return None, error_msg


def handle_get_customer_by_email(email):
    """
    Retrieve customer information by email address.
    Used for identity verification.
    """
    # Simulate processing delay
    time.sleep(0.2)

    customer = CUSTOMERS.get(email)

    if customer:
        return {
            "success": True,
            "customer": customer,
            "message": f"Customer verified: {customer['name']}"
        }
    else:
        return {
            "success": False,
            "message": "No customer found with that email address. Please verify the email and try again."
        }


def handle_get_customer_by_phone(phone):
    """
    Retrieve customer information by phone number.
    Used for identity verification.
    """
    # Simulate processing delay
    time.sleep(0.2)

    # Search for customer by phone
    for customer in CUSTOMERS.values():
        if customer['phone'] == phone:
            return {
                "success": True,
                "customer": customer,
                "message": f"Customer verified: {customer['name']}"
            }

    return {
        "success": False,
        "message": "No customer found with that phone number. Please verify the number and try again."
    }


def handle_get_order(order_id):
    """
    Retrieve order information by order ID.
    Should only be called after customer identity is verified.
    """
    # Simulate processing delay
    time.sleep(0.2)

    order = ORDERS.get(order_id)

    if order:
        # Format items for response
        items_summary = ", ".join([f"{item['quantity']}x {item['name']}" for item in order['items']])

        response = {
            "success": True,
            "order_id": order['order_id'],
            "status": order['status'],
            "items": items_summary,
            "total": f"${order['total']:.2f}",
            "order_date": order['order_date']
        }

        # Add tracking info if available
        if order['tracking_number']:
            response['tracking_number'] = order['tracking_number']
            response['estimated_delivery'] = order['estimated_delivery']

        return response
    else:
        return {
            "success": False,
            "message": "Order not found. Please verify the order number and try again."
        }


def handle_check_inventory(product_name):
    """
    Check inventory for a specific product.
    Returns availability and price information.
    """
    # Simulate processing delay
    time.sleep(0.2)

    # Case-insensitive search
    product = None
    for item_name, item_data in INVENTORY.items():
        if item_name.lower() == product_name.lower():
            product = item_data
            product_name = item_name  # Use the properly cased name
            break

    if product:
        quantity = product['quantity']
        price = product['price']

        if quantity > 10:
            availability = "in stock"
        elif quantity > 0:
            availability = "limited stock"
        else:
            availability = "out of stock"

        return {
            "success": True,
            "product_name": product_name,
            "availability": availability,
            "quantity": quantity,
            "price": f"${price:.2f}"
        }
    else:
        return {
            "success": False,
            "message": f"Product '{product_name}' not found in our inventory."
        }