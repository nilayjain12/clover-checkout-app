# Clover Checkout Application

A simple and robust web application that integrates with the Clover REST API to perform OAuth 2.0 authentication and process payments. This project is built using Python with the FastAPI framework and is fully containerized with Docker for easy setup and deployment.

## Features

- **Clover OAuth 2.0:** Secure authentication flow to connect to a merchant's Clover account.
- **Secure Token Management:** Access tokens are securely stored and managed by the backend.
- **Payment Processing:** A complete payment flow that creates an order, adds a line item, and processes a payment using the Clover API.
- **Transaction History:** View a list of recent transactions and their status (successful or failed).
- **Modern UI:** A clean, responsive user interface with clear user feedback, including loading states and error messages.
- **Containerized:** Uses Docker and Docker Compose, allowing the application to be run with a single command.
- **Automated Testing:** Includes a suite of unit tests to ensure application reliability.
- **Makefile for Convenience:** Common commands are bundled into a `Makefile` for ease of use.

## Project Structure

```
.
├── app/                  # Core application logic, services, and utilities
│   ├── clover_service.py   # Functions for interacting with the Clover API
│   ├── token_utils.py      # Utilities for managing OAuth tokens
│   └── transaction_utils.py# Logging for transactions
├── static/               # Frontend assets
│   └── index.html        # Main HTML file with CSS and JavaScript
├── .dockerignore         # Specifies files to ignore in Docker build
├── .env                  # Local environment variables (you must create this)
├── docker-compose.yml    # Defines and runs the multi-container Docker application
├── Dockerfile            # Instructions to build the Docker image
├── main.py               # FastAPI application entrypoint and route definitions
├── Makefile              # Automates common development tasks
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── test_main.py          # Unit tests for the application
└── transactions.log      # Log file for payment history
```

## Setup and Installation

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- A [Clover Developer Sandbox Account](https://sandbox.dev.clover.com/developers/)
- `make` (optional, but recommended for using the Makefile commands)

### 1. Clover Developer Account Configuration

Before running the application, you must configure your application in the Clover Developer Dashboard.

1.  **Create an App:** Log in to your Clover Sandbox account and create a new application.
2.  **Get Credentials:** Note the `App ID` (Client ID) and `App Secret` (Client Secret).
3.  **Configure URLs:**
    -   Under **App Settings** -> **App URL**, set it to `http://localhost:8000`.
    -   Under **Web Configuration**, set the **Default OAuth Response** to `Code`.
    -   Add `http://localhost:8000/auth/callback` as a **Redirect URI**.
4.  **Set Required Permissions:** This is the most critical step.
    -   Navigate to **Settings** -> **Required Permissions**.
    -   Check the following boxes and provide a brief reason for each:
        -   **Merchant**: `Read`
        -   **Orders**: `Read` and `Write`
        -   **Payments**: `Read` and `Write`
        -   **Ecommerce**: `Enable online payments`
    -   **Save** your changes.
5.  **Configure Ecommerce Settings**:
    -   Navigate to **Settings** -> **Ecommerce Settings**.
    -   Set the **Integration Type** to `API`.

### 2. Local Application Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd clover-checkout-app
    ```

2.  **Create Environment File:**
    -   Create a file named `.env` in the root of the project.
    -   Add your Clover App credentials to this file.

    ```env
    # .env file
    CLOVER_CLIENT_ID=YOUR_CLOVER_APP_ID
    CLOVER_CLIENT_SECRET=YOUR_CLOVER_APP_SECRET
    CLOVER_API_BASE_URL=https://sandbox.dev.clover.com
    APP_REDIRECT_URI=http://localhost:8000/auth/callback
    ```

### 3. Running the Application

-   **Using Make (Recommended):**
    ```bash
    make up
    ```
    This will build the Docker images and start the application in the background.

-   **Using Docker Compose directly:**
    ```bash
    docker-compose up --build -d
    ```

The application will be available at [http://localhost:8000](http://localhost:8000).

## How to Use

1.  Open your web browser and navigate to `http://localhost:8000`.
2.  Click the **Login with Clover** button and authorize the application using your sandbox merchant account.
3.  After being redirected, you will see the main payment form. The Merchant ID will be displayed.
4.  Enter a payment amount and a description.
5.  Click **Submit Payment**. The application will show the transaction status.
6.  Click **View Recent Transactions** to see a history of payments.
7.  Click **Logout** to clear your session token.

## Running Tests

To run the included unit tests, use the following command:

```bash
make test
```

## Other Commands

-   **View Logs:**
    ```bash
    make logs
    ```
-   **Stop the Application:**
    ```bash
    make down
    ```
-   **Access the Running Container:**
    ```bash
    make shell
    ```

## Troubleshooting

-   **`401 Unauthorized` Error:** This almost always means the access token does not have the correct permissions. Ensure you have set all the **Required Permissions** correctly in the Clover dashboard and, most importantly, **you must Logout and Login again** after saving any permission changes to generate a new token.
-   **`token.json` Issues:** The application creates `token.json` to store your OAuth token. If you encounter strange authentication issues, you can stop the app (`make down`), delete `token.json` from the project root, and start it again.
