from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_marshmallow import Marshmallow
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Initialize extensions
mongo = PyMongo(app)
ma = Marshmallow(app)

# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Flask Login API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Create Swagger JSON
@app.route('/static/swagger.json')
def swagger_json():
    swagger = {
        "swagger": "2.0",
        "info": {
            "title": "Flask Login API",
            "description": "API for user registration and login",
            "version": "1.0.0"
        },
        "basePath": "/",
        "schemes": ["http"],
        "paths": {
            "/register": {
                "post": {
                    "summary": "Register a new user",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string"},
                                    "email": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "User created successfully"
                        },
                        "400": {
                            "description": "Invalid input"
                        }
                    }
                }
            },
            "/login": {
                "post": {
                    "summary": "Login user",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Login successful"
                        },
                        "401": {
                            "description": "Invalid credentials"
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger)

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    # Check if user already exists
    if mongo.db.users.find_one({'email': email}):
        return jsonify({'message': 'Email already registered'}), 400
    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'Username already taken'}), 400

    hashed_password = generate_password_hash(password)
    user_id = mongo.db.users.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password
    }).inserted_id

    return jsonify({'message': 'User created successfully', 'id': str(user_id)}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    user = mongo.db.users.find_one({'email': email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    user_data = {
        'id': str(user['_id']),
        'username': user['username'],
        'email': user['email']
    }
    return jsonify({'message': 'Login successful', 'user': user_data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 