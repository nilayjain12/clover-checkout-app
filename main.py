import os
import requests
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Use absolute imports from the 'app' package
from app import token_utils, transaction_utils, clover_service

# --- Configuration ---
# These variables will be loaded from the environment variables
# provided by the Docker run command.
CLIENT_ID = os.getenv("CLOVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLOVER_CLIENT_SECRET")
BASE_API_URL = os.getenv("CLOVER_API_BASE_URL", "https://sandbox.dev.clover.com")
REDIRECT_URI = os.getenv("APP_REDIRECT_URI", "http://localhost:8000/auth/callback")

# --- App Lifecycle Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, ensure token.json exists.
    print("Application startup: Checking for token.json...")
    if not os.path.exists(token_utils.TOKEN_FILE):
        with open(token_utils.TOKEN_FILE, "w") as f:
            f.write("") # Create an empty file
        print(f"'{token_utils.TOKEN_FILE}' created successfully.")
    yield
    # On shutdown
    print("Application shutdown.")

# --- FastAPI App Initialization ---
app = FastAPI(lifespan=lifespan, title="Clover Checkout App", version="1.0.0")

# Mount a directory to serve static files (like index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Pydantic Models ---
class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount in USD")
    description: str = Field(..., min_length=1, max_length=100, description="Payment description")

class PaymentResponse(BaseModel):
    status: str
    payment_id: str
    order_id: str
    amount: float
    currency: str
    description: str

# --- Helper Functions ---
def get_clover_auth_url():
    """Constructs the Clover authorization URL."""
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="CLOVER_CLIENT_ID is not set. Please check your .env file or docker command.")
    return f"{BASE_API_URL}/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def exchange_code_for_token(code: str, merchant_id: str):
    """Exchanges the authorization code for an access token."""
    token_url = f"{BASE_API_URL}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }
    try:
        # ** THE FIX IS HERE: **
        # Send the payload as form data in the request body, which is a more
        # standard OAuth 2.0 practice and what the Clover API expects.
        response = requests.post(token_url, data=payload)
        response.raise_for_status() # This will raise an exception for 4xx/5xx responses
        token_data = response.json()
        token_data['merchant_id'] = merchant_id
        token_utils.save_token(token_data)
        print("Successfully exchanged code for access token.")
        return token_data
    except requests.exceptions.RequestException as e:
        # Add more detailed logging to see exactly what Clover is sending back on failure.
        print("--- ERROR: FAILED TO EXCHANGE CODE FOR TOKEN ---")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        else:
            print(f"An error occurred with no response from the server: {e}")
        print("-------------------------------------------------")
        transaction_utils.log_error("TOKEN_EXCHANGE_ERROR", str(e), {"merchant_id": merchant_id})
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code for token. Check server logs for details.")

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the main index.html page."""
    try:
        with open("static/index.html") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

@app.get("/auth/login")
def auth_login():
    """Redirects the user to the Clover authorization page."""
    print(f"Login request received")
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"REDIRECT_URI: {REDIRECT_URI}")
    print(f"BASE_API_URL: {BASE_API_URL}")
    
    if not token_utils.is_token_expired():
        print("Token is still valid, redirecting to home")
        return RedirectResponse(url="/")
    
    try:
        auth_url = get_clover_auth_url()
        print(f"Generated auth URL: {auth_url}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        print(f"Error generating auth URL: {e}")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>Configuration Error</h1>
            <p>Error generating authentication URL: {str(e)}</p>
            <p>Please check your environment variables:</p>
            <ul>
                <li>CLOVER_CLIENT_ID: {CLIENT_ID or 'NOT SET'}</li>
                <li>APP_REDIRECT_URI: {REDIRECT_URI}</li>
                <li>CLOVER_API_BASE_URL: {BASE_API_URL}</li>
            </ul>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """, status_code=500)

@app.get("/auth/callback")
def auth_callback(request: Request, code: str = None, merchant_id: str = None, error: str = None):
    """Callback endpoint for Clover OAuth."""
    print(f"Received callback with parameters:")
    print(f"  code: {code}")
    print(f"  merchant_id: {merchant_id}")
    print(f"  error: {error}")
    print(f"  full URL: {request.url}")
    
    # Handle OAuth errors
    if error:
        print(f"OAuth error received: {error}")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>OAuth Error</h1>
            <p>Error: {error}</p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """, status_code=400)
    
    # Check if required parameters are present
    if not code:
        print("Missing 'code' parameter in callback")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>Authentication Error</h1>
            <p>Missing authorization code. This usually means the OAuth redirect URI is not configured correctly.</p>
            <p>Please check your Clover app settings and ensure the Redirect URI is set to: <code>http://localhost:8000/auth/callback</code></p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """, status_code=400)
    
    if not merchant_id:
        print("Missing 'merchant_id' parameter in callback")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>Authentication Error</h1>
            <p>Missing merchant ID. Please try logging in again.</p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """, status_code=400)
    
    try:
        print(f"Exchanging code for token...")
        exchange_code_for_token(code, merchant_id)
        print(f"Successfully exchanged code for token")
        return RedirectResponse(url="/")
    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        return HTMLResponse(content=f"""
        <html>
        <body>
            <h1>Authentication Error</h1>
            <p>Failed to complete authentication: {str(e)}</p>
            <a href="/">Return to Home</a>
        </body>
        </html>
        """, status_code=500)

@app.get("/auth/logout")
def auth_logout():
    """Logs out the user by clearing the stored token."""
    token_utils.clear_token()
    return RedirectResponse(url="/")
    
@app.get("/auth/status")
def auth_status():
    """Checks if the user is authenticated."""
    if token_utils.is_token_expired():
        return {"authenticated": False}
    
    merchant_id = token_utils.get_merchant_id()
    return {
        "authenticated": True,
        "merchant_id": merchant_id
    }

@app.post("/pay", response_model=PaymentResponse)
async def create_payment_flow(payment_request: PaymentRequest):
    """
    Handles the payment flow by creating an order, adding a line item, and paying.
    """
    access_token = token_utils.get_access_token()
    token_data = token_utils.load_token()
    if not access_token or not token_data:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login.")

    merchant_id = token_data.get("merchant_id")
    amount_in_cents = int(payment_request.amount * 100)
    currency = "USD"
    
    log_details = { 
        "amount": amount_in_cents, 
        "currency": currency, 
        "description": payment_request.description 
    }

    try:
        # DEBUG: Temporarily commented out to bypass potential merchant-read permission issues.
        merchant_info = clover_service.get_merchant_info(access_token, merchant_id)
        print(f"Processing payment for merchant: {merchant_info.get('name', 'Unknown')}")

        # Step 1: Create an Order
        order = clover_service.create_order(access_token, merchant_id)
        order_id = order['id']
        log_details['order_id'] = order_id

        # Step 2: Add a Line Item to the Order
        clover_service.add_line_item_to_order(access_token, merchant_id, order_id, amount_in_cents, payment_request.description)

        # Step 3: Create a Payment for the Order
        payment = clover_service.create_payment_for_order(access_token, merchant_id, order_id, amount_in_cents, currency)
        payment_id = payment.get('id')
        log_details['payment_id'] = payment_id
        
        # Step 4: Get final payment status for logging and response
        final_payment_details = clover_service.get_payment_details(access_token, merchant_id, payment_id)
        log_details['status'] = final_payment_details.get('status', 'UNKNOWN')

        transaction_utils.log_transaction(log_details)
        
        return PaymentResponse(
            status=final_payment_details.get('status', 'UNKNOWN'),
            payment_id=payment_id,
            order_id=order_id,
            amount=payment_request.amount,
            currency=currency,
            description=payment_request.description
        )

    except requests.exceptions.HTTPError as e:
        error_details = e.response.json()
        error_message = error_details.get('message', 'No error message provided.')
        log_details['status'] = 'FAILED'
        log_details['error_message'] = error_message
        transaction_utils.log_transaction(log_details)
        raise HTTPException(status_code=e.response.status_code, detail=f"Clover API Error: {error_message}")
    except Exception as e:
        log_details['status'] = 'FAILED'
        log_details['error_message'] = str(e)
        transaction_utils.log_transaction(log_details)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/transactions")
def get_transactions():
    """Returns recent transaction history."""
    try:
        transactions = transaction_utils.get_transaction_summary()
        return {"transactions": transactions}
    except Exception as e:
        transaction_utils.log_error("GET_TRANSACTIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve transaction history")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "authenticated": not token_utils.is_token_expired()
    }
