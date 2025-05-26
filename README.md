# Flask Login API

A simple Flask API with user registration and login functionality, including Swagger documentation, using MongoDB Atlas.

## Setup

1. **Environment Variables**
   Create a `.env` file in the root directory with the following content:
   ```
   MONGO_URI=your_mongodb_connection_string
   SECRET_KEY=your_secret_key
   ```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python app.py
```

The server will start at `http://localhost:5001`

## API Documentation

Swagger documentation is available at: `http://localhost:5001/api/docs`

## API Endpoints

### Register User
- **URL**: `/register`
- **Method**: `POST`
- **Body**:
```json
{
    "username": "your_username",
    "email": "your_email@example.com",
    "password": "your_password"
}
```

### Login
- **URL**: `/login`
- **Method**: `POST`
- **Body**:
```json
{
    "email": "your_email@example.com",
    "password": "your_password"
}
```

## Features

- User registration with email and username validation
- Secure password hashing
- User login with credential verification
- Swagger UI documentation
- **MongoDB Atlas** cloud database for user storage
- Environment variable configuration for sensitive data 