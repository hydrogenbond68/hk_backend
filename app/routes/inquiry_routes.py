from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Inquiry, Product, User
from datetime import datetime

inquiry_bp = Blueprint('inquiries', __name__)

@inquiry_bp.route('/', methods=['POST'])
@jwt_required()
def create_inquiry():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()
    
    if not all(k in data for k in ['product_id', 'subject', 'message']):
        return jsonify({'error': 'Product ID, subject, and message required'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    inquiry = Inquiry(
        product_id=data['product_id'],
        user_id=user.id,
        subject=data['subject'],
        message=data['message']
    )
    
    db.session.add(inquiry)
    db.session.commit()
    
    return jsonify({
        'message': 'Inquiry sent successfully',
        'inquiry': inquiry.to_dict()
    }), 201

@inquiry_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_inquiries():
    user_id = get_jwt_identity()
    inquiries = Inquiry.query.filter_by(user_id=user_id).order_by(Inquiry.created_at.desc()).all()
    return jsonify({'inquiries': [i.to_dict() for i in inquiries]}), 200

@inquiry_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_inquiries():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return jsonify({'inquiries': [i.to_dict() for i in inquiries]}), 200

@inquiry_bp.route('/<int:inquiry_id>/reply', methods=['POST'])
@jwt_required()
def reply_inquiry(inquiry_id):
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    data = request.get_json()
    
    if not data.get('reply'):
        return jsonify({'error': 'Reply message required'}), 400
    
    inquiry.reply = data['reply']
    inquiry.status = 'replied'
    inquiry.replied_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Reply sent successfully',
        'inquiry': inquiry.to_dict()
    }), 200
