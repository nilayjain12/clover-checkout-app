import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='transactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_transaction(details: dict):
    """
    Logs key details of a transaction to transactions.log.

    Args:
        details (dict): A dictionary containing transaction information.
                        Expected keys: order_id, payment_id, amount,
                        currency, description, status.
    """
    # Create a structured log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "status": details.get('status', 'N/A'),
        "payment_id": details.get('payment_id', 'N/A'),
        "order_id": details.get('order_id', 'N/A'),
        "amount": details.get('amount', 0),
        "amount_usd": details.get('amount', 0) / 100.0,
        "currency": details.get('currency', 'USD'),
        "description": details.get('description', 'N/A'),
        "error_message": details.get('error_message', None)
    }
    
    # Log to file
    logging.info(f"Transaction: {json.dumps(log_entry)}")
    
    # Print to console for debugging
    log_message = (
        f"Status: {log_entry['status']}, "
        f"PaymentID: {log_entry['payment_id']}, "
        f"OrderID: {log_entry['order_id']}, "
        f"Amount: ${log_entry['amount_usd']:.2f} {log_entry['currency']}, "
        f"Description: {log_entry['description']}"
    )
    
    if log_entry['error_message']:
        log_message += f", Error: {log_entry['error_message']}"
    
    print(f"Logged transaction: {log_message}")

def log_error(error_type: str, error_message: str, context: dict = None):
    """
    Logs error information with context.
    
    Args:
        error_type (str): Type of error (e.g., 'API_ERROR', 'AUTH_ERROR')
        error_message (str): Detailed error message
        context (dict): Additional context information
    """
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {}
    }
    
    logging.error(f"Error: {json.dumps(error_entry)}")
    print(f"Error logged: {error_type} - {error_message}")

def get_transaction_summary():
    """
    Returns a summary of recent transactions from the log file.
    """
    try:
        with open('transactions.log', 'r') as f:
            lines = f.readlines()
        
        # Parse last 10 transactions
        recent_transactions = []
        for line in lines[-10:]:
            if 'Transaction:' in line:
                try:
                    # Extract JSON from log line
                    json_start = line.find('Transaction: ') + len('Transaction: ')
                    json_str = line[json_start:].strip()
                    transaction = json.loads(json_str)
                    recent_transactions.append(transaction)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return recent_transactions
    except FileNotFoundError:
        return []

