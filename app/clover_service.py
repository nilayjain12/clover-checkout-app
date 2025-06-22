import os
import requests
from app import transaction_utils

# Environment variables are provided by the Docker run command
BASE_API_URL = os.getenv("CLOVER_API_BASE_URL", "https://sandbox.dev.clover.com")

def get_headers(access_token: str):
    """Constructs the authorization headers for Clover API requests."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

def validate_response(response: requests.Response, operation: str):
    """Validates API response and logs errors."""
    if not response.ok:
        error_context = {
            "operation": operation,
            "status_code": response.status_code,
            "url": response.url
        }
        
        try:
            error_data = response.json()
            error_message = error_data.get('message', 'Unknown API error')
            error_context['api_error'] = error_data
        except:
            error_message = f"HTTP {response.status_code}: {response.text}"
        
        transaction_utils.log_error("API_ERROR", error_message, error_context)
        response.raise_for_status()
    
    return response

def create_order(access_token: str, merchant_id: str):
    """
    Creates a new empty order in Clover.
    This corresponds to step 2a of the task requirements.
    """
    url = f"{BASE_API_URL}/v3/merchants/{merchant_id}/orders"
    headers = get_headers(access_token)
    
    try:
        # An empty JSON body is required to create a new, empty order
        response = requests.post(url, headers=headers, json={})
        validate_response(response, "create_order")
        order_data = response.json()
        
        print(f"Order created successfully: {order_data.get('id')}")
        return order_data
    except requests.exceptions.RequestException as e:
        transaction_utils.log_error("CREATE_ORDER_ERROR", str(e), {"merchant_id": merchant_id})
        raise

def add_line_item_to_order(access_token: str, merchant_id: str, order_id: str, amount: int, description: str):
    """
    Adds a line item to an existing order. Amount should be in cents.
    This corresponds to step 2b of the task requirements.
    """
    url = f"{BASE_API_URL}/v3/merchants/{merchant_id}/orders/{order_id}/line_items"
    headers = get_headers(access_token)
    payload = {
        "name": description,
        "price": amount
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        validate_response(response, "add_line_item")
        line_item_data = response.json()
        
        print(f"Line item added successfully: {line_item_data.get('id')}")
        return line_item_data
    except requests.exceptions.RequestException as e:
        transaction_utils.log_error("ADD_LINE_ITEM_ERROR", str(e), {
            "merchant_id": merchant_id,
            "order_id": order_id,
            "amount": amount,
            "description": description
        })
        raise

def create_payment_for_order(access_token: str, merchant_id: str, order_id: str, amount: int, currency: str):
    """
    Initiates a payment for an order using a test card token. Amount should be in cents.
    This corresponds to step 2c of the task requirements.
    """
    url = f"{BASE_API_URL}/v3/merchants/{merchant_id}/payments"
    headers = get_headers(access_token)
    # "ecom" is a generic source for card-not-present test transactions.
    payload = {
        "order": {
            "id": order_id
        },
        "amount": amount,
        "currency": currency.upper(),
        "source": "ecom"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        validate_response(response, "create_payment")
        payment_data = response.json()
        
        print(f"Payment created successfully: {payment_data.get('id')}")
        return payment_data
    except requests.exceptions.RequestException as e:
        transaction_utils.log_error("CREATE_PAYMENT_ERROR", str(e), {
            "merchant_id": merchant_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency
        })
        raise

def get_payment_details(access_token: str, merchant_id: str, payment_id: str):
    """
    Retrieves the status and details of a specific payment.
    This corresponds to step 3 of the task requirements.
    """
    url = f"{BASE_API_URL}/v3/merchants/{merchant_id}/payments/{payment_id}"
    headers = get_headers(access_token)
    
    try:
        response = requests.get(url, headers=headers)
        validate_response(response, "get_payment_details")
        payment_details = response.json()
        
        print(f"Payment details retrieved: {payment_details.get('status')}")
        return payment_details
    except requests.exceptions.RequestException as e:
        transaction_utils.log_error("GET_PAYMENT_DETAILS_ERROR", str(e), {
            "merchant_id": merchant_id,
            "payment_id": payment_id
        })
        raise

def get_merchant_info(access_token: str, merchant_id: str):
    """
    Retrieves merchant information for validation.
    """
    url = f"{BASE_API_URL}/v3/merchants/{merchant_id}"
    headers = get_headers(access_token)
    
    try:
        response = requests.get(url, headers=headers)
        validate_response(response, "get_merchant_info")
        return response.json()
    except requests.exceptions.RequestException as e:
        transaction_utils.log_error("GET_MERCHANT_INFO_ERROR", str(e), {"merchant_id": merchant_id})
        raise
