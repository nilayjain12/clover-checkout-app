# Quick Start Guide

## Follow these steps for quick setup:

### 1. Prerequisites
- Python 3.10+ or Docker
- Clover Developer Account
- Clover App Credentials

### 2. Clover App Setup
1. Go to [Clover Developer Portal](https://dev.clover.com)
2. Create a new App
3. Copy Client ID and Client Secret
4. Set Redirect URI: `http://localhost:8000/auth/callback`

### 3. Application Setup

#### Option A: With Docker (Easiest)
```bash
# Clone repository
git clone <repository-url>
cd clover-checkout-app

# Set environment variables
export CLOVER_CLIENT_ID="your_client_id"
export CLOVER_CLIENT_SECRET="your_client_secret"

# Run with Docker Compose
docker-compose up --build
```

#### Option B: Local Development
```bash
# Clone repository
git clone <repository-url>
cd clover-checkout-app

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CLOVER_CLIENT_ID="your_client_id"
export CLOVER_CLIENT_SECRET="your_client_secret"

# Run application
python -m uvicorn main:app --reload
```

### 4. Application Access
- Go to browser: `http://localhost:8000`
- Click "Login with Clover"
- Authorize with your Clover account
- Fill payment form and test

### 5. Testing
```bash
# Run tests
pytest test_main.py -v

# Or with Makefile
make test
```

### 6. Useful Commands
```bash
# Show help
make help

# Development setup
make dev-setup

# Format code
make format

# Run all checks
make check

# Clean up
make clean
```

### 7. Troubleshooting

#### Authentication Issues
- Are Client ID and Client Secret correct?
- Is Redirect URI set in Clover app?
- Are you using sandbox environment?

#### Payment Issues
- Use test cards in sandbox mode
- Is amount positive and valid?
- Is network connectivity working?

#### View Logs
```bash
# Application logs
docker-compose logs -f

# Transaction logs
tail -f transactions.log
```

### 8. Next Steps
- See README.md for production deployment
- Visit `http://localhost:8000/docs` for API documentation
- Explore source code for customization

## Support
For issues:
1. Check logs
2. Read README.md
3. Create GitHub Issues 