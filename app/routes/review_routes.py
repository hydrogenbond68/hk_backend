from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Review, Product, User

review_bp = Blueprint('reviews', __name__)

@review_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    
    return jsonify({
        'reviews': [review.to_dict() for review in reviews],
        'average_rating': product.get_average_rating(),
        'total_reviews': len(reviews)
    }), 200

@review_bp.route('/', methods=['POST'])
@jwt_required()
def create_review():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()
    
    if not data.get('product_id') or not data.get('rating'):
        return jsonify({'error': 'Product ID and rating required'}), 400
    
    if not 1 <= data['rating'] <= 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    existing = Review.query.filter_by(product_id=data['product_id'], user_id=user.id).first()
    if existing:
        return jsonify({'error': 'You already reviewed this product'}), 400
    
    review = Review(
        product_id=data['product_id'],
        user_id=user.id,
        rating=data['rating'],
        comment=data.get('comment')
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'message': 'Review created successfully',
        'review': review.to_dict()
    }), 201

@review_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    review = Review.query.get_or_404(review_id)
    
    if not user.is_admin and review.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message': 'Review deleted successfully'}), 200
