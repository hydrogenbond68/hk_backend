from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
import re
import logging
from datetime import datetime, timedelta
import secrets
import string

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

# ============= REGISTRATION =============
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.info(f"Registration attempt: {data.get('email')}")
        
        required = ['email', 'password', 'first_name', 'last_name']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name'],
            company_name=data.get('company_name'),
            phone=data.get('phone'),
            address=data.get('address'),
            profile_image=data.get('profile_image'),
            is_admin=data.get('is_admin', False),
            is_verified=False
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered successfully: {user.email}")
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful! Please verify your email.',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= LOGIN =============
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.info(f"Login attempt: {data.get('email')}")
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user:
            logger.warning(f"Login failed: User not found - {data.get('email')}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.check_password(data['password']):
            logger.warning(f"Login failed: Invalid password - {user.email}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        logger.info(f"Login successful: {user.email}")
        
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

# ============= PASSWORD RESET REQUEST =============
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            # Don't reveal if user exists or not for security
            return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Generate reset token
        token = user.generate_reset_token()
        db.session.commit()
        
        # In production, send email with reset link
        # For now, return the token (in development)
        reset_link = f"http://localhost:5173/reset-password?token={token}"
        
        logger.info(f"Password reset requested for: {user.email}")
        
        return jsonify({
            'message': 'Password reset link sent to your email',
            'reset_token': token,  # Remove in production
            'reset_link': reset_link  # Remove in production
        }), 200
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= PASSWORD RESET CONFIRM =============
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Find user by token
        user = User.query.filter_by(reset_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Verify token expiry
        if not user.verify_reset_token(token):
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Update password
        user.set_password(new_password)
        user.clear_reset_token()
        db.session.commit()
        
        logger.info(f"Password reset successful for: {user.email}")
        
        return jsonify({
            'message': 'Password reset successfully! You can now login with your new password.'
        }), 200
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= GET CURRENT USER =============
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= UPDATE PROFILE =============
@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        allowed_fields = ['first_name', 'last_name', 'company_name', 'phone', 'address', 'profile_image']
        
        for field in allowed_fields:
            if field in data and data[field] is not None:
                if field == 'profile_image':
                    if data[field] == '':
                        user.profile_image = None
                    else:
                        user.profile_image = data[field]
                else:
                    setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= REFRESH TOKEN =============
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

# ============= GET ALL USERS (Admin Only) =============
@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        current_user = User.query.get(user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= UPDATE USER ROLE (Admin Only) =============
@auth_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_user_role(user_id):
    try:
        admin_id = get_jwt_identity()
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
        
        admin = User.query.get(admin_id)
        
        if not admin or not admin.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'message': 'User role updated successfully',
                'user': user.to_dict()
            }), 200
        
        return jsonify({'error': 'is_admin field required'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user role error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= DELETE USER (Admin Only) =============
@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        admin_id = get_jwt_identity()
        if isinstance(admin_id, str):
            admin_id = int(admin_id)
        
        admin = User.query.get(admin_id)
        
        if not admin or not admin.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.id == admin.id:
            return jsonify({'error': 'Cannot delete yourself'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({'error': str(e)}), 500
