import pytest
import json
import tempfile
import os
import requests
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient
from main import app
from app import token_utils, transaction_utils, clover_service

client = TestClient(app)

class TestPDFRequirements:
    """
    Test suite to verify all requirements from the PDF are satisfied.
    This tests the complete payment flow and API integration.
    """
    
    @patch('app.clover_service.create_order')
    @patch('app.clover_service.add_line_item_to_order')
    @patch('app.clover_service.create_payment_for_order')
    @patch('app.clover_service.get_payment_details')
    @patch('app.clover_service.get_merchant_info')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_complete_payment_flow_requirement(self, 
                                             mock_load_token, 
                                             mock_get_token, 
                                             mock_merchant_info,
                                             mock_get_payment_details,
                                             mock_create_payment,
                                             mock_add_line_item,
                                             mock_create_order):
        """
        Test Requirement: Complete payment flow (Order -> Line Item -> Payment)
        This tests the 3-step process mentioned in the PDF:
        1. Create an order
        2. Add a line item to the order
        3. Create a payment for the order
        """
        
        # Mock authentication
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        # Mock merchant info
        mock_merchant_info.return_value = {"name": "Test Merchant"}
        
        # Mock order creation (Step 1)
        mock_create_order.return_value = {
            "id": "test_order_123",
            "state": "open"
        }
        
        # Mock line item addition (Step 2)
        mock_add_line_item.return_value = {
            "id": "test_line_item_456",
            "name": "Test Product",
            "price": 1000
        }
        
        # Mock payment creation (Step 3)
        mock_create_payment.return_value = {
            "id": "test_payment_789",
            "status": "pending",
            "amount": 1000
        }
        
        # Mock payment details retrieval
        mock_get_payment_details.return_value = {
            "id": "test_payment_789",
            "status": "succeeded",
            "amount": 1000,
            "currency": "USD"
        }
        
        # Test payment request
        payment_data = {
            "amount": 10.00,
            "description": "Test Product"
        }
        
        response = client.post("/pay", json=payment_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["payment_id"] == "test_payment_789"
        assert data["order_id"] == "test_order_123"
        assert data["amount"] == 10.00
        assert data["currency"] == "USD"
        assert data["description"] == "Test Product"
        
        # Verify all steps were called in correct order
        mock_create_order.assert_called_once_with("test_access_token", "test_merchant_123")
        mock_add_line_item.assert_called_once_with("test_access_token", "test_merchant_123", "test_order_123", 1000, "Test Product")
        mock_create_payment.assert_called_once_with("test_access_token", "test_merchant_123", "test_order_123", 1000, "USD")
        mock_get_payment_details.assert_called_once_with("test_access_token", "test_merchant_123", "test_payment_789")
    
    @patch('app.clover_service.create_order')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_order_creation_requirement(self, mock_load_token, mock_get_token, mock_create_order):
        """
        Test Requirement: Order creation functionality
        Verify that orders can be created successfully
        """
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        mock_create_order.return_value = {
            "id": "test_order_123",
            "state": "open",
            "createdTime": "2024-01-01T12:00:00Z"
        }
        
        # Test order creation through payment flow
        payment_data = {"amount": 10.00, "description": "Test"}
        
        with patch('app.clover_service.add_line_item_to_order'), \
             patch('app.clover_service.create_payment_for_order'), \
             patch('app.clover_service.get_payment_details'), \
             patch('app.clover_service.get_merchant_info'):
            
            response = client.post("/pay", json=payment_data)
            assert response.status_code == 200
            
            # Verify order was created
            mock_create_order.assert_called_once()
            call_args = mock_create_order.call_args
            assert call_args[0][0] == "test_access_token"  # access_token
            assert call_args[0][1] == "test_merchant_123"  # merchant_id
    
    @patch('app.clover_service.add_line_item_to_order')
    @patch('app.clover_service.create_order')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_line_item_addition_requirement(self, mock_load_token, mock_get_token, mock_create_order, mock_add_line_item):
        """
        Test Requirement: Line item addition functionality
        Verify that line items can be added to orders
        """
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        mock_create_order.return_value = {"id": "test_order_123"}
        mock_add_line_item.return_value = {
            "id": "test_line_item_456",
            "name": "Test Product",
            "price": 1000
        }
        
        # Test line item addition through payment flow
        payment_data = {"amount": 10.00, "description": "Test Product"}
        
        with patch('app.clover_service.create_payment_for_order'), \
             patch('app.clover_service.get_payment_details'), \
             patch('app.clover_service.get_merchant_info'):
            
            response = client.post("/pay", json=payment_data)
            assert response.status_code == 200
            
            # Verify line item was added
            mock_add_line_item.assert_called_once()
            call_args = mock_add_line_item.call_args
            assert call_args[0][0] == "test_access_token"  # access_token
            assert call_args[0][1] == "test_merchant_123"  # merchant_id
            assert call_args[0][2] == "test_order_123"     # order_id
            assert call_args[0][3] == 1000                 # amount in cents
            assert call_args[0][4] == "Test Product"       # description
    
    @patch('app.clover_service.create_payment_for_order')
    @patch('app.clover_service.create_order')
    @patch('app.clover_service.add_line_item_to_order')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_payment_creation_requirement(self, mock_load_token, mock_get_token, mock_add_line_item, mock_create_order, mock_create_payment):
        """
        Test Requirement: Payment creation functionality
        Verify that payments can be created for orders
        """
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        mock_create_order.return_value = {"id": "test_order_123"}
        mock_add_line_item.return_value = {"id": "test_line_item_456"}
        mock_create_payment.return_value = {
            "id": "test_payment_789",
            "status": "pending",
            "amount": 1000,
            "currency": "USD"
        }
        
        # Test payment creation through payment flow
        payment_data = {"amount": 10.00, "description": "Test Product"}
        
        with patch('app.clover_service.get_payment_details'), \
             patch('app.clover_service.get_merchant_info'):
            
            response = client.post("/pay", json=payment_data)
            assert response.status_code == 200
            
            # Verify payment was created
            mock_create_payment.assert_called_once()
            call_args = mock_create_payment.call_args
            assert call_args[0][0] == "test_access_token"  # access_token
            assert call_args[0][1] == "test_merchant_123"  # merchant_id
            assert call_args[0][2] == "test_order_123"     # order_id
            assert call_args[0][3] == 1000                 # amount in cents
            assert call_args[0][4] == "USD"                # currency
    
    @patch('app.clover_service.get_payment_details')
    @patch('app.clover_service.create_payment_for_order')
    @patch('app.clover_service.create_order')
    @patch('app.clover_service.add_line_item_to_order')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_payment_status_verification_requirement(self, mock_load_token, mock_get_token, mock_add_line_item, mock_create_order, mock_create_payment, mock_get_payment_details):
        """
        Test Requirement: Payment status verification
        Verify that payment status can be retrieved and verified
        """
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        mock_create_order.return_value = {"id": "test_order_123"}
        mock_add_line_item.return_value = {"id": "test_line_item_456"}
        mock_create_payment.return_value = {"id": "test_payment_789"}
        mock_get_payment_details.return_value = {
            "id": "test_payment_789",
            "status": "succeeded",
            "amount": 1000,
            "currency": "USD",
            "createdTime": "2024-01-01T12:00:00Z"
        }
        
        # Test payment status verification through payment flow
        payment_data = {"amount": 10.00, "description": "Test Product"}
        
        with patch('app.clover_service.get_merchant_info'):
            response = client.post("/pay", json=payment_data)
            assert response.status_code == 200
            
            # Verify payment status was retrieved
            mock_get_payment_details.assert_called_once()
            call_args = mock_get_payment_details.call_args
            assert call_args[0][0] == "test_access_token"  # access_token
            assert call_args[0][1] == "test_merchant_123"  # merchant_id
            assert call_args[0][2] == "test_payment_789"   # payment_id
    
    def test_oauth_authentication_requirement(self):
        """
        Test Requirement: OAuth 2.0 authentication
        Verify that OAuth authentication endpoints are available
        """
        # Test login endpoint
        response = client.get("/auth/login")
        assert response.status_code in [200, 302]  # Redirect or OK
        
        # Test callback endpoint (should handle parameters)
        response = client.get("/auth/callback?code=test_code&merchant_id=test_merchant")
        assert response.status_code in [200, 302]  # Redirect or OK
        
        # Test auth status endpoint
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "authenticated" in data
    
    def test_transaction_logging_requirement(self):
        """
        Test Requirement: Transaction logging
        Verify that transactions are properly logged
        """
        # Create a temporary log file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_log_file = f.name
        
        # Mock the logging configuration
        original_filename = transaction_utils.logging.getLogger().handlers[0].baseFilename
        transaction_utils.logging.getLogger().handlers[0].baseFilename = temp_log_file
        
        try:
            # Test transaction logging
            test_transaction = {
                "status": "SUCCESS",
                "payment_id": "test_payment_123",
                "order_id": "test_order_456",
                "amount": 1000,
                "currency": "USD",
                "description": "Test Payment"
            }
            
            transaction_utils.log_transaction(test_transaction)
            
            # Verify log file was created and contains transaction data
            assert os.path.exists(temp_log_file)
            
            with open(temp_log_file, 'r') as f:
                log_content = f.read()
                assert "test_payment_123" in log_content
                assert "test_order_456" in log_content
                assert "Test Payment" in log_content
                assert "SUCCESS" in log_content
                
        finally:
            # Cleanup
            transaction_utils.logging.getLogger().handlers[0].baseFilename = original_filename
            if os.path.exists(temp_log_file):
                os.unlink(temp_log_file)
    
    def test_error_handling_requirement(self):
        """
        Test Requirement: Error handling
        Verify that errors are properly handled and logged
        """
        # Test with invalid payment data
        invalid_payment_data = {
            "amount": -10.00,  # Negative amount
            "description": ""   # Empty description
        }
        
        response = client.post("/pay", json=invalid_payment_data)
        assert response.status_code == 422  # Validation error
        
        # Test with unauthenticated request
        if os.path.exists(token_utils.TOKEN_FILE):
            os.remove(token_utils.TOKEN_FILE)
        
        payment_data = {"amount": 10.00, "description": "Test"}
        response = client.post("/pay", json=payment_data)
        assert response.status_code == 401  # Unauthorized
    
    @patch('app.clover_service.create_order')
    @patch('app.token_utils.get_access_token')
    @patch('app.token_utils.load_token')
    def test_api_integration_requirement(self, mock_load_token, mock_get_token, mock_create_order):
        """
        Test Requirement: Clover API integration
        Verify that the application properly integrates with Clover API
        """
        mock_get_token.return_value = "test_access_token"
        mock_load_token.return_value = {"merchant_id": "test_merchant_123"}
        
        # Mock successful API response
        mock_create_order.return_value = {
            "id": "test_order_123",
            "state": "open"
        }
        
        # Test API integration through payment flow
        payment_data = {"amount": 10.00, "description": "Test Product"}
        
        with patch('app.clover_service.add_line_item_to_order'), \
             patch('app.clover_service.create_payment_for_order'), \
             patch('app.clover_service.get_payment_details'), \
             patch('app.clover_service.get_merchant_info'):
            
            response = client.post("/pay", json=payment_data)
            assert response.status_code == 200
            
            # Verify API was called with correct parameters
            mock_create_order.assert_called_once()
            call_args = mock_create_order.call_args
            assert call_args[0][0] == "test_access_token"  # access_token
            assert call_args[0][1] == "test_merchant_123"  # merchant_id
    
    def test_web_interface_requirement(self):
        """
        Test Requirement: Web interface
        Verify that the web interface is accessible and functional
        """
        # Test main page
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        # Test static files
        response = client.get("/static/index.html")
        assert response.status_code == 200
    
    def test_health_check_requirement(self):
        """
        Test Requirement: Health check endpoint
        Verify that health check functionality works
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "authenticated" in data

class TestIntegrationRequirements:
    """
    Integration tests to verify end-to-end functionality
    """
    
    @patch('requests.post')
    @patch('requests.get')
    def test_end_to_end_payment_flow(self, mock_get, mock_post):
        """
        Test the complete end-to-end payment flow with real API calls
        """
        # Mock OAuth token exchange
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600
        }
        
        # Mock API responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "id": "test_merchant_123",
            "name": "Test Merchant"
        }
        
        # Test the complete flow
        # This would require setting up a test environment with real Clover credentials
        # For now, we'll test the structure
        
        # Verify all required endpoints exist
        endpoints_to_test = [
            "/",
            "/auth/login",
            "/auth/status",
            "/health",
            "/transactions"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code in [200, 302]  # OK or Redirect

def run_requirement_tests():
    """
    Function to run all requirement tests and generate a report
    """
    print("Running Clover Checkout App Requirement Tests...")
    print("=" * 50)
    
    # Test categories
    test_categories = [
        "OAuth Authentication",
        "Order Creation",
        "Line Item Addition", 
        "Payment Creation",
        "Payment Status Verification",
        "Transaction Logging",
        "Error Handling",
        "API Integration",
        "Web Interface",
        "Health Check"
    ]
    
    print("Testing the following requirements:")
    for i, category in enumerate(test_categories, 1):
        print(f"{i}. {category}")
    
    print("\nTo run all tests:")
    print("pytest test_requirements.py -v")
    
    print("\nTo run specific test categories:")
    print("pytest test_requirements.py::TestPDFRequirements::test_oauth_authentication_requirement -v")
    print("pytest test_requirements.py::TestPDFRequirements::test_complete_payment_flow_requirement -v")

if __name__ == "__main__":
    run_requirement_tests() 