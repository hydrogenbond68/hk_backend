from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
import re
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required = ['email', 'password', 'first_name', 'last_name']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            company_name=data.get('company_name'),
            phone=data.get('phone'),
            address=data.get('address'),
            profile_image=data.get('profile_image'),
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # IMPORTANT: Convert to string
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # IMPORTANT: Convert to string
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=str(user_id))
        return jsonify({'access_token': new_access_token}), 200
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        logger.info(f"Get user - User ID from token: {user_id}, Type: {type(user_id)}")
        
        # Convert to int if it's a string
        if isinstance(user_id, str):
            user_id = int(user_id)
        elif isinstance(user_id, int):
            pass  # Already an int
        else:
            user_id = int(user_id)
            
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile including image"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"Profile update - User ID from token: {user_id}, Type: {type(user_id)}")
        
        # Convert to int if it's a string
        if isinstance(user_id, str):
            user_id = int(user_id)
        elif isinstance(user_id, int):
            pass  # Already an int
        else:
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        logger.info(f"Updating profile for user {user_id}: {data}")
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'company_name', 'phone', 'address', 'profile_image']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data and data[field] is not None:
                if field == 'profile_image':
                    # Handle base64 image
                    image_data = data[field]
                    if image_data and isinstance(image_data, str) and len(image_data) > 100:
                        if image_data.startswith('data:image'):
                            user.profile_image = image_data
                            updated_fields.append(field)
                        else:
                            user.profile_image = image_data
                            updated_fields.append(field)
                    elif image_data == '':
                        user.profile_image = None
                        updated_fields.append(field)
                else:
                    setattr(user, field, data[field])
                    updated_fields.append(field)
        
        db.session.commit()
        logger.info(f"Profile updated successfully for user {user_id}. Fields updated: {updated_fields}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': str(e)}), 500
