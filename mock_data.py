"""
Mock data for customer support simulation.
"""

# Mock customer database
CUSTOMERS = {
    "customer@example.com": {
        "customer_id": "CUST001",
        "name": "Alice Johnson",
        "email": "customer@example.com",
        "phone": "+1-555-0123",
        "address": "123 Main St, San Francisco, CA 94102",
        "status": "active"
    },
    "john.doe@example.com": {
        "customer_id": "CUST002",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0456",
        "address": "456 Oak Ave, New York, NY 10001",
        "status": "active"
    },
    "sarah.smith@example.com": {
        "customer_id": "CUST003",
        "name": "Sarah Smith",
        "email": "sarah.smith@example.com",
        "phone": "+1-555-0789",
        "address": "789 Pine Rd, Austin, TX 78701",
        "status": "active"
    }
}

# Mock orders database
ORDERS = {
    "ORD001": {
        "order_id": "ORD001",
        "customer_id": "CUST001",
        "customer_email": "customer@example.com",
        "items": [
            {"name": "Laptop Stand", "quantity": 1, "price": 49.99},
            {"name": "USB-C Cable", "quantity": 2, "price": 12.99}
        ],
        "total": 75.97,
        "status": "shipped",
        "tracking_number": "TRK123456789",
        "order_date": "2025-09-15",
        "estimated_delivery": "2025-10-05"
    },
    "ORD002": {
        "order_id": "ORD002",
        "customer_id": "CUST002",
        "customer_email": "john.doe@example.com",
        "items": [
            {"name": "Wireless Mouse", "quantity": 1, "price": 29.99}
        ],
        "total": 29.99,
        "status": "delivered",
        "tracking_number": "TRK987654321",
        "order_date": "2025-09-10",
        "estimated_delivery": "2025-09-20"
    },
    "ORD003": {
        "order_id": "ORD003",
        "customer_id": "CUST003",
        "customer_email": "sarah.smith@example.com",
        "items": [
            {"name": "Mechanical Keyboard", "quantity": 1, "price": 129.99},
            {"name": "Keyboard Wrist Rest", "quantity": 1, "price": 24.99}
        ],
        "total": 154.98,
        "status": "processing",
        "tracking_number": None,
        "order_date": "2025-09-28",
        "estimated_delivery": "2025-10-08"
    }
}

# Mock inventory
INVENTORY = {
    "Laptop Stand": {"quantity": 50, "price": 49.99},
    "USB-C Cable": {"quantity": 200, "price": 12.99},
    "Wireless Mouse": {"quantity": 75, "price": 29.99},
    "Mechanical Keyboard": {"quantity": 30, "price": 129.99},
    "Keyboard Wrist Rest": {"quantity": 100, "price": 24.99},
    "Monitor Arm": {"quantity": 25, "price": 89.99},
    "Webcam": {"quantity": 40, "price": 79.99},
    "Headphones": {"quantity": 60, "price": 149.99}
}