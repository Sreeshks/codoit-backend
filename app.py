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

# Turf Owner Schema
class TurfOwnerSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "name", "phone")

# Turf Schema
class TurfSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "location", "price_per_hour", "owner_id", "availability")

user_schema = UserSchema()
users_schema = UserSchema(many=True)
turf_owner_schema = TurfOwnerSchema()
turf_owners_schema = TurfOwnerSchema(many=True)
turf_schema = TurfSchema()
turfs_schema = TurfSchema(many=True)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Turf Booking API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Create Swagger JSON
@app.route('/static/swagger.json')
def swagger_json():
    swagger = {
        "swagger": "2.0",
        "info": {
            "title": "Turf Booking API",
            "description": "API for user and turf owner management, turf booking system",
            "version": "1.0.0"
        },
        "basePath": "/",
        "schemes": ["http"],
        "paths": {
            "/user/register": {
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
                        "201": {"description": "User created successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/user/login": {
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
                        "200": {"description": "Login successful"},
                        "401": {"description": "Invalid credentials"}
                    }
                }
            },
            "/user/turfs": {
                "get": {
                    "summary": "Get all available turfs",
                    "responses": {
                        "200": {"description": "List of turfs"},
                        "404": {"description": "No turfs found"}
                    }
                }
            },
            "/owner/register": {
                "post": {
                    "summary": "Register a new turf owner",
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
                                    "password": {"type": "string"},
                                    "name": {"type": "string"},
                                    "phone": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {"description": "Turf owner created successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/owner/login": {
                "post": {
                    "summary": "Login turf owner",
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
                        "200": {"description": "Login successful"},
                        "401": {"description": "Invalid credentials"}
                    }
                }
            },
            "/owner/turf": {
                "post": {
                    "summary": "Add a new turf",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "owner_id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "location": {"type": "string"},
                                    "price_per_hour": {"type": "number"},
                                    "availability": {"type": "boolean"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {"description": "Turf created successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/owner/turf/<id>": {
                "put": {
                    "summary": "Update turf details",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "type": "string"
                        },
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "location": {"type": "string"},
                                    "price_per_hour": {"type": "number"},
                                    "availability": {"type": "boolean"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {"description": "Turf updated successfully"},
                        "400": {"description": "Invalid input"},
                        "404": {"description": "Turf not found"}
                    }
                }
            }
        }
    }
    return jsonify(swagger)

# User Routes
@app.route('/user/register', methods=['POST'])
def user_register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

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

@app.route('/user/login', methods=['POST'])
def user_login():
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

@app.route('/user/turfs', methods=['GET'])
def get_turfs():
    turfs = mongo.db.turfs.find({'availability': True})
    if not turfs:
        return jsonify({'message': 'No turfs available'}), 404
    return jsonify(turfs_schema.dump(turfs)), 200

# Turf Owner Routes
@app.route('/owner/register', methods=['POST'])
def owner_register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    if not all([username, email, password, name, phone]):
        return jsonify({'message': 'Missing fields'}), 400

    if mongo.db.turf_owners.find_one({'email': email}):
        return jsonify({'message': 'Email already registered'}), 400
    if mongo.db.turf_owners.find_one({'username': username}):
        return jsonify({'message': 'Username already taken'}), 400

    hashed_password = generate_password_hash(password)
    owner_id = mongo.db.turf_owners.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password,
        'name': name,
        'phone': phone
    }).inserted_id

    return jsonify({'message': 'Turf owner created successfully', 'id': str(owner_id)}), 201

@app.route('/owner/login', methods=['POST'])
def owner_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    owner = mongo.db.turf_owners.find_one({'email': email})
    if not owner or not check_password_hash(owner['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    owner_data = {
        'id': str(owner['_id']),
        'username': owner['username'],
        'email': owner['email'],
        'name': owner['name'],
        'phone': owner['phone']
    }
    return jsonify({'message': 'Login successful', 'owner': owner_data}), 200

@app.route('/owner/turf', methods=['POST'])
def add_turf():
    data = request.get_json()
    owner_id = data.get('owner_id')
    name = data.get('name')
    location = data.get('location')
    price_per_hour = data.get('price_per_hour')
    availability = data.get('availability', True)

    if not all([owner_id, name, location, price_per_hour]):
        return jsonify({'message': 'Missing fields'}), 400

    if not mongo.db.turf_owners.find_one({'_id': ObjectId(owner_id)}):
        return jsonify({'message': 'Invalid owner ID'}), 400

    turf_id = mongo.db.turfs.insert_one({
        'owner_id': owner_id,
        'name': name,
        'location': location,
        'price_per_hour': price_per_hour,
        'availability': availability
    }).inserted_id

    return jsonify({'message': 'Turf added successfully', 'id': str(turf_id)}), 201

@app.route('/owner/turf/<id>', methods=['PUT'])
def update_turf(id):
    data = request.get_json()
    name = data.get('name')
    location = data.get('location')
    price_per_hour = data.get('price_per_hour')
    availability = data.get('availability')

    update_data = {}
    if name:
        update_data['name'] = name
    if location:
        update_data['location'] = location
    if price_per_hour:
        update_data['price_per_hour'] = price_per_hour
    if availability is not None:
        update_data['availability'] = availability

    if not update_data:
        return jsonify({'message': 'No fields to update'}), 400

    result = mongo.db.turfs.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_data}
    )

    if result.matched_count == 0:
        return jsonify({'message': 'Turf not found'}), 404

    return jsonify({'message': 'Turf updated successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)