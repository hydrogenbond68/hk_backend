from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderItem, Product, User
import random
import string

order_bp = Blueprint('orders', __name__)

def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

@order_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()
    
    if not data or not data.get('items') or not data.get('shipping_address'):
        return jsonify({'error': 'Items and shipping address required'}), 400
    
    total_amount = 0
    items = []
    
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'error': f'Product {item["product_id"]} not found'}), 404
        if product.stock_quantity < item['quantity']:
            return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
        
        total_amount += product.price * item['quantity']
        items.append({
            'product': product,
            'quantity': item['quantity'],
            'price': product.price
        })
    
    order = Order(
        user_id=user.id,
        order_number=generate_order_number(),
        total_amount=total_amount,
        shipping_address=data['shipping_address'],
        shipping_method=data.get('shipping_method'),
        payment_method=data.get('payment_method'),
        notes=data.get('notes')
    )
    
    db.session.add(order)
    db.session.commit()
    
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product'].id,
            quantity=item['quantity'],
            price_at_time=item['price']
        )
        db.session.add(order_item)
        # Update stock
        item['product'].stock_quantity -= item['quantity']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Order created successfully',
        'order': order.to_dict()
    }), 201

@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if user.is_admin:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    
    return jsonify({'orders': [order.to_dict() for order in orders]}), 200

@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    order = Order.query.get_or_404(order_id)
    
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'order': order.to_dict()}), 200

@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if not data.get('status'):
        return jsonify({'error': 'Status required'}), 400
    
    order.status = data['status']
    db.session.commit()
    
    return jsonify({
        'message': 'Order status updated',
        'order': order.to_dict()
    }), 200
