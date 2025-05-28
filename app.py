from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_marshmallow import Marshmallow
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import secrets
from dotenv import load_dotenv
import jwt
import datetime
from functools import wraps
from dateutil import parser
from dateutil.relativedelta import relativedelta

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Initialize extensions
mongo = PyMongo(app)
ma = Marshmallow(app)

# JWT Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1]  # Remove 'Bearer' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_type'], data['user_id']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Schemas
class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "full_name", "phone", "created_at")

class TurfOwnerSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "name", "phone", "business_name", "address", "created_at")

class TurfSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "location", "size", "amenities", "price_per_hour", "owner_id", "availability", "surface_type", "capacity", "description")

class BookingSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "turf_id", "start_time", "end_time", "status", "total_cost", "created_at", "notes")

user_schema = UserSchema()
users_schema = UserSchema(many=True)
turf_owner_schema = TurfOwnerSchema()
turf_owners_schema = TurfOwnerSchema(many=True)
turf_schema = TurfSchema()
turfs_schema = TurfSchema(many=True)
booking_schema = BookingSchema()
bookings_schema = BookingSchema(many=True)

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
            "version": "3.0.0"
        },
        "basePath": "/",
        "schemes": ["http"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header"
            }
        },
        "tags": [
            {"name": "User", "description": "Operations for users"},
            {"name": "Turf Owner", "description": "Operations for turf owners"}
        ],
        "paths": {
            "/user/register": {
                "post": {
                    "tags": ["User"],
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
                                    "password": {"type": "string"},
                                    "full_name": {"type": "string"},
                                    "phone": {"type": "string"}
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
                    "tags": ["User"],
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
                    "tags": ["User"],
                    "summary": "Get all available turfs",
                    "responses": {
                        "200": {"description": "List of turfs"},
                        "404": {"description": "No turfs found"}
                    }
                }
            },
            "/user/book": {
                "post": {
                    "tags": ["User"],
                    "summary": "Book a turf",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "turf_id": {"type": "string"},
                                    "start_time": {"type": "string", "format": "date-time"},
                                    "end_time": {"type": "string", "format": "date-time"},
                                    "notes": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {"description": "Booking created successfully"},
                        "400": {"description": "Invalid input"},
                        "409": {"description": "Time slot unavailable"}
                    }
                }
            },
            "/user/bookings": {
                "get": {
                    "tags": ["User"],
                    "summary": "Get user bookings",
                    "security": [{"Bearer": []}],
                    "responses": {
                        "200": {"description": "List of bookings"},
                        "404": {"description": "No bookings found"}
                    }
                }
            },
            "/user/booking/<id>": {
                "delete": {
                    "tags": ["User"],
                    "summary": "Cancel a booking",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Booking cancelled"},
                        "403": {"description": "Unauthorized"},
                        "404": {"description": "Booking not found"}
                    }
                }
            },
            "/owner/register": {
                "post": {
                    "tags": ["Turf Owner"],
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
                                    "phone": {"type": "string"},
                                    "business_name": {"type": "string"},
                                    "address": {"type": "string"}
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
                    "tags": ["Turf Owner"],
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
                    "tags": ["Turf Owner"],
                    "summary": "Add a new turf",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "location": {"type": "string"},
                                    "size": {"type": "string"},
                                    "amenities": {"type": "array", "items": {"type": "string"}},
                                    "price_per_hour": {"type": "number"},
                                    "availability": {"type": "boolean"},
                                    "surface_type": {"type": "string"},
                                    "capacity": {"type": "integer"},
                                    "description": {"type": "string"}
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
                    "tags": ["Turf Owner"],
                    "summary": "Update turf details",
                    "security": [{"Bearer": []}],
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
                                    "size": {"type": "string"},
                                    "amenities": {"type": "array", "items": {"type": "string"}},
                                    "price_per_hour": {"type": "number"},
                                    "availability": {"type": "boolean"},
                                    "surface_type": {"type": "string"},
                                    "capacity": {"type": "integer"},
                                    "description": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {"description": "Turf updated successfully"},
                        "400": {"description": "Invalid input"},
                        "403": {"description": "Unauthorized"},
                        "404": {"description": "Turf not found"}
                    }
                },
                "delete": {
                    "tags": ["Turf Owner"],
                    "summary": "Delete a turf",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Turf deleted successfully"},
                        "403": {"description": "Unauthorized"},
                        "404": {"description": "Turf not found"}
                    }
                }
            },
            "/owner/turfs": {
                "get": {
                    "tags": ["Turf Owner"],
                    "summary": "Get all turfs owned by the owner",
                    "security": [{"Bearer": []}],
                    "responses": {
                        "200": {"description": "List of turfs"},
                        "404": {"description": "No turfs found"}
                    }
                }
            },
            "/owner/turf/<id>/bookings": {
                "get": {
                    "tags": ["Turf Owner"],
                    "summary": "Get all bookings for a turf",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {"description": "List of bookings"},
                        "403": {"description": "Unauthorized"},
                        "404": {"description": "No bookings found"}
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
    full_name = data.get('full_name')
    phone = data.get('phone')

    if not all([username, email, password, full_name, phone]):
        return jsonify({'message': 'Missing fields'}), 400

    if mongo.db.users.find_one({'email': email}):
        return jsonify({'message': 'Email already registered'}), 400
    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'Username already taken'}), 400

    hashed_password = generate_password_hash(password)
    user_id = mongo.db.users.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password,
        'full_name': full_name,
        'phone': phone,
        'created_at': datetime.datetime.utcnow()
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

    token = jwt.encode({
        'user_type': 'user',
        'user_id': str(user['_id']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    user_data = {
        'id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'phone': user['phone'],
        'created_at': user['created_at'].isoformat()
    }
    return jsonify({'message': 'Login successful', 'user': user_data, 'token': token}), 200

@app.route('/user/turfs', methods=['GET'])
def get_turfs():
    turfs = mongo.db.turfs.find({'availability': True})
    turfs_list = turfs_schema.dump(turfs)
    if not turfs_list:
        return jsonify({'message': 'No turfs available'}), 404
    return jsonify(turfs_list), 200

@app.route('/user/book', methods=['POST'])
@token_required
def book_turf(current_user):
    if current_user[0] != 'user':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = current_user[1]
    turf_id = data.get('turf_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    notes = data.get('notes', '')

    if not all([turf_id, start_time, end_time]):
        return jsonify({'message': 'Missing fields'}), 400

    try:
        start_time = parser.parse(start_time)
        end_time = parser.parse(end_time)
    except:
        return jsonify({'message': 'Invalid date format'}), 400

    if start_time >= end_time:
        return jsonify({'message': 'End time must be after start time'}), 400

    turf = mongo.db.turfs.find_one({'_id': ObjectId(turf_id), 'availability': True})
    if not turf:
        return jsonify({'message': 'Turf not found or unavailable'}), 404

    # Check for overlapping bookings
    existing_booking = mongo.db.bookings.find_one({
        'turf_id': turf_id,
        'status': 'confirmed',
        '$or': [
            {'start_time': {'$lte': end_time, '$gte': start_time}},
            {'end_time': {'$gte': start_time, '$lte': end_time}},
            {'start_time': {'$lte': start_time}, 'end_time': {'$gte': end_time}}
        ]
    })
    if existing_booking:
        return jsonify({'message': 'Time slot unavailable'}), 409

    # Calculate total cost
    duration_hours = (end_time - start_time).total_seconds() / 3600
    total_cost = turf['price_per_hour'] * duration_hours

    booking_id = mongo.db.bookings.insert_one({
        'user_id': user_id,
        'turf_id': turf_id,
        'start_time': start_time,
        'end_time': end_time,
        'status': 'confirmed',
        'total_cost': total_cost,
        'created_at': datetime.datetime.utcnow(),
        'notes': notes
    }).inserted_id

    return jsonify({'message': 'Booking created successfully', 'id': str(booking_id)}), 201

@app.route('/user/bookings', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    if current_user[0] != 'user':
        return jsonify({'message': 'Unauthorized'}), 403

    bookings = mongo.db.bookings.find({'user_id': current_user[1]})
    bookings_list = bookings_schema.dump(bookings)
    if not bookings_list:
        return jsonify({'message': 'No bookings found'}), 404
    return jsonify(bookings_list), 200

@app.route('/user/booking/<id>', methods=['DELETE'])
@token_required
def cancel_booking(current_user, id):
    if current_user[0] != 'user':
        return jsonify({'message': 'Unauthorized'}), 403

    booking = mongo.db.bookings.find_one({'_id': ObjectId(id), 'user_id': current_user[1]})
    if not booking:
        return jsonify({'message': 'Booking not found or unauthorized'}), 404

    if booking['status'] == 'cancelled':
        return jsonify({'message': 'Booking already cancelled'}), 400

    mongo.db.bookings.update_one(
        {'_id': ObjectId(id)},
        {'$set': {'status': 'cancelled'}}
    )
    return jsonify({'message': 'Booking cancelled successfully'}), 200

# Turf Owner Routes
@app.route('/owner/register', methods=['POST'])
def owner_register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')
    business_name = data.get('business_name')
    address = data.get('address')

    if not all([username, email, password, name, phone, business_name, address]):
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
        'phone': phone,
        'business_name': business_name,
        'address': address,
        'created_at': datetime.datetime.utcnow()
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

    token = jwt.encode({
        'user_type': 'owner',
        'user_id': str(owner['_id']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    owner_data = {
        'id': str(owner['_id']),
        'username': owner['username'],
        'email': owner['email'],
        'name': owner['name'],
        'phone': owner['phone'],
        'business_name': owner['business_name'],
        'address': owner['address'],
        'created_at': owner['created_at'].isoformat()
    }
    return jsonify({'message': 'Login successful', 'owner': owner_data, 'token': token}), 200

@app.route('/owner/turf', methods=['POST'])
@token_required
def add_turf(current_user):
    if current_user[0] != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    name = data.get('name')
    location = data.get('location')
    size = data.get('size')
    amenities = data.get('amenities', [])
    price_per_hour = data.get('price_per_hour')
    availability = data.get('availability', True)
    surface_type = data.get('surface_type')
    capacity = data.get('capacity')
    description = data.get('description', '')

    if not all([name, location, size, price_per_hour, surface_type, capacity]):
        return jsonify({'message': 'Missing fields'}), 400

    turf_id = mongo.db.turfs.insert_one({
        'owner_id': current_user[1],
        'name': name,
        'location': location,
        'size': size,
        'amenities': amenities,
        'price_per_hour': price_per_hour,
        'availability': availability,
        'surface_type': surface_type,
        'capacity': capacity,
        'description': description
    }).inserted_id

    return jsonify({'message': 'Turf added successfully', 'id': str(turf_id)}), 201

@app.route('/owner/turf/<id>', methods=['PUT'])
@token_required
def update_turf(current_user, id):
    if current_user[0] != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403

    turf = mongo.db.turfs.find_one({'_id': ObjectId(id), 'owner_id': current_user[1]})
    if not turf:
        return jsonify({'message': 'Turf not found or unauthorized'}), 404

    data = request.get_json()
    update_data = {}
    for field in ['name', 'location', 'size', 'amenities', 'price_per_hour', 'availability', 'surface_type', 'capacity', 'description']:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return jsonify({'message': 'No fields to update'}), 400

    mongo.db.turfs.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_data}
    )
    return jsonify({'message': 'Turf updated successfully'}), 200

@app.route('/owner/turf/<id>', methods=['DELETE'])
@token_required
def delete_turf(current_user, id):
    if current_user[0] != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403

    turf = mongo.db.turfs.find_one({'_id': ObjectId(id), 'owner_id': current_user[1]})
    if not turf:
        return jsonify({'message': 'Turf not found or unauthorized'}), 404

    # Check for active bookings
    active_bookings = mongo.db.bookings.find_one({
        'turf_id': id,
        'status': 'confirmed'
    })
    if active_bookings:
        return jsonify({'message': 'Cannot delete turf with active bookings'}), 400

    mongo.db.turfs.delete_one({'_id': ObjectId(id)})
    return jsonify({'message': 'Turf deleted successfully'}), 200

@app.route('/owner/turfs', methods=['GET'])
@token_required
def get_owner_turfs(current_user):
    if current_user[0] != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403

    turfs = mongo.db.turfs.find({'owner_id': current_user[1]})
    turfs_list = turfs_schema.dump(turfs)
    if not turfs_list:
        return jsonify({'message': 'No turfs found'}), 404
    return jsonify(turfs_list), 200

@app.route('/owner/turf/<id>/bookings', methods=['GET'])
@token_required
def get_turf_bookings(current_user, id):
    if current_user[0] != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403

    turf = mongo.db.turfs.find_one({'_id': ObjectId(id), 'owner_id': current_user[1]})
    if not turf:
        return jsonify({'message': 'Turf not found or unauthorized'}), 404

    bookings = mongo.db.bookings.find({'turf_id': id})
    bookings_list = bookings_schema.dump(bookings)
    if not bookings_list:
        return jsonify({'message': 'No bookings found'}), 404
    return jsonify(bookings_list), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)