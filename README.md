# Ikiguide 🌟

Ikiguide is a software application designed to help users explore potential paths in life based on their input, inspired by the Japanese concept of Ikigai. Ikigai is a Japanese term that means "a reason for being" and is often used to describe the things that make one's life worthwhile.

## What is Ikigai? 🤔

Ikigai is a concept that encourages individuals to find their purpose in life by exploring the intersection of four key questions:
1. **What do you love?** ❤️
2. **What are you good at?** 🛠️
3. **What does the world need?** 🌍
4. **What can you be paid for?** 💰

By answering these questions, Ikiguide helps users identify potential paths that align with their passions, skills, societal needs, and financial opportunities.

## Project Structure

- **ikiguide-backend**: Contains the server-side code, responsible for handling API requests and managing data.
- **ikiguide-frontend**: Includes the client-side code, built with React, to provide an interactive user interface.

## Installation and Setup ⚙️

### Prerequisites

- Node.js and npm for frontend development.
- Python and pip for backend development.
- Docker for containerization (optional).

### Frontend

1. Navigate to the `ikiguide-frontend` directory.
2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm start
   ```

### Backend

1. Navigate to the `ikiguide-backend` directory.
2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI application:

   ```bash
   uvicorn app.main:app --reload
   ```

## Usage 🚀

- Access the frontend at `http://localhost:3000` to interact with the application.
- The backend API is available at `http://localhost:8000`.

## Dependencies 📦

### Frontend

- React
- Axios
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy
- OpenAI API

## Environment Variables 🔑

The `.env` file contains encrypted secrets for the OpenAI API and Azure email sending feature. You can use the `re_encrypt_secrets.py` script to generate the encrypted secrets. Below is a generic example `.env` configuration:

```plaintext
# OpenAI Configuration
ENCRYPTED_OPENAI_API_KEY=<your_encrypted_openai_api_key_here>

# Application Configuration
APP_NAME=Ikiguide
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_HOSTS=localhost,127.0.0.1

# Session Configuration
SESSION_MAX_AGE=3600  # 1 hour in seconds
SESSION_MAX_TIMEOUT=24
SESSION_MAX_CONCURRENT=1000

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_DIR=logs

# API Configuration
API_HOST=localhost
API_PORT=8000

# Encrypted Azure App Registration Email Configuration
ENCRYPTED_AZURE_TENANT_ID=<your_encrypted_azure_tenant_id_here>
ENCRYPTED_AZURE_CLIENT_ID=<your_encrypted_azure_client_id_here>
ENCRYPTED_AZURE_CLIENT_SECRET=<your_encrypted_azure_client_secret_here>
EMAIL_FROM=<From Email>
EMAIL_BCC=<Optional BCC Email>
```

## Contribution 🤝

Contributions are welcome! Please fork the repository and submit a pull request for any features or bug fixes.

## License 📄

Ikiguide © 2024 by Nova Mentis is licensed under CC BY-NC-SA 4.0 