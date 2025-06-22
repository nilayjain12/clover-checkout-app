import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from app import token_utils, transaction_utils

client = TestClient(app)

class TestTokenUtils:
    def test_save_and_load_token(self):
        """Test token saving and loading functionality."""
        # Create a temporary token file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_token_file = f.name
        
        # Mock the TOKEN_FILE path
        original_token_file = token_utils.TOKEN_FILE
        token_utils.TOKEN_FILE = temp_token_file
        
        try:
            # Test data
            test_token_data = {
                "access_token": "test_access_token",
                "expires_in": 3600,
                "merchant_id": "test_merchant_id"
            }
            
            # Save token
            token_utils.save_token(test_token_data)
            
            # Load token
            loaded_token = token_utils.load_token()
            
            # Assertions
            assert loaded_token is not None
            assert loaded_token["access_token"] == "test_access_token"
            assert loaded_token["merchant_id"] == "test_merchant_id"
            assert "expires_at" in loaded_token
            
        finally:
            # Cleanup
            token_utils.TOKEN_FILE = original_token_file
            if os.path.exists(temp_token_file):
                os.unlink(temp_token_file)
    
    def test_token_expiry(self):
        """Test token expiry checking."""
        # Create a temporary token file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_token_file = f.name
        
        # Mock the TOKEN_FILE path
        original_token_file = token_utils.TOKEN_FILE
        token_utils.TOKEN_FILE = temp_token_file
        
        try:
            # Test with expired token
            expired_token_data = {
                "access_token": "test_token",
                "expires_in": -3600,  # Expired 1 hour ago
                "merchant_id": "test_merchant"
            }
            
            token_utils.save_token(expired_token_data)
            assert token_utils.is_token_expired() == True
            
            # Test with valid token
            valid_token_data = {
                "access_token": "test_token",
                "expires_in": 3600,  # Valid for 1 hour
                "merchant_id": "test_merchant"
            }
            
            token_utils.save_token(valid_token_data)
            assert token_utils.is_token_expired() == False
            
        finally:
            # Cleanup
            token_utils.TOKEN_FILE = original_token_file
            if os.path.exists(temp_token_file):
                os.unlink(temp_token_file)

class TestTransactionUtils:
    def test_log_transaction(self):
        """Test transaction logging functionality."""
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_log_file = f.name
        
        # Mock the logging configuration
        original_filename = transaction_utils.logging.getLogger().handlers[0].baseFilename
        transaction_utils.logging.getLogger().handlers[0].baseFilename = temp_log_file
        
        try:
            # Test transaction data
            test_transaction = {
                "status": "SUCCESS",
                "payment_id": "test_payment_123",
                "order_id": "test_order_456",
                "amount": 1000,
                "currency": "USD",
                "description": "Test Payment"
            }
            
            # Log transaction
            transaction_utils.log_transaction(test_transaction)
            
            # Check if log file was created and contains the transaction
            assert os.path.exists(temp_log_file)
            
            with open(temp_log_file, 'r') as f:
                log_content = f.read()
                assert "Test Payment" in log_content
                assert "test_payment_123" in log_content
                
        finally:
            # Cleanup
            transaction_utils.logging.getLogger().handlers[0].baseFilename = original_filename
            if os.path.exists(temp_log_file):
                os.unlink(temp_log_file)

class TestMainApp:
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "authenticated" in data
    
    def test_auth_status_not_authenticated(self):
        """Test auth status when not authenticated."""
        # Ensure no token file exists
        if os.path.exists(token_utils.TOKEN_FILE):
            os.remove(token_utils.TOKEN_FILE)
        
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == False
    
    @patch('app.token_utils.is_token_expired')
    @patch('app.token_utils.get_merchant_id')
    def test_auth_status_authenticated(self, mock_get_merchant_id, mock_is_expired):
        """Test auth status when authenticated."""
        mock_is_expired.return_value = False
        mock_get_merchant_id.return_value = "test_merchant_123"
        
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == True
        assert data["merchant_id"] == "test_merchant_123"
    
    def test_pay_endpoint_not_authenticated(self):
        """Test pay endpoint when not authenticated."""
        # Ensure no token file exists
        if os.path.exists(token_utils.TOKEN_FILE):
            os.remove(token_utils.TOKEN_FILE)
        
        payment_data = {
            "amount": 10.50,
            "description": "Test Payment"
        }
        
        response = client.post("/pay", json=payment_data)
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"]
    
    def test_pay_endpoint_invalid_data(self):
        """Test pay endpoint with invalid data."""
        # Test with negative amount
        payment_data = {
            "amount": -10.50,
            "description": "Test Payment"
        }
        
        response = client.post("/pay", json=payment_data)
        assert response.status_code == 422  # Validation error
        
        # Test with empty description
        payment_data = {
            "amount": 10.50,
            "description": ""
        }
        
        response = client.post("/pay", json=payment_data)
        assert response.status_code == 422  # Validation error
    
    def test_transactions_endpoint(self):
        """Test transactions endpoint."""
        response = client.get("/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)

if __name__ == "__main__":
    pytest.main([__file__]) 