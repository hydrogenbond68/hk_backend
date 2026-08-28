from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Product, User
import json
import logging
from datetime import datetime

product_bp = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

@product_bp.after_request
def add_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@product_bp.route('', methods=['GET'])
def get_products():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        sub_category = request.args.get('sub_category')
        search = request.args.get('search')
        min_price = request.args.get('min_price') or request.args.get('minPrice')
        max_price = request.args.get('max_price') or request.args.get('maxPrice')
        sort_by = request.args.get('sort_by') or request.args.get('sortBy', 'created_at')
        sort_order = request.args.get('sort_order') or request.args.get('sortOrder', 'desc')
        featured = request.args.get('featured', type=bool)
        timestamp = request.args.get('_t')  # Cache-busting parameter
        
        if min_price and min_price != 'undefined':
            try:
                min_price = float(min_price)
            except ValueError:
                min_price = None
        else:
            min_price = None
            
        if max_price and max_price != 'undefined':
            try:
                max_price = float(max_price)
            except ValueError:
                max_price = None
        else:
            max_price = None
        
        query = Product.query.filter_by(is_active=True)
        
        if category and category != 'undefined':
            query = query.filter_by(category=category)
        if sub_category and sub_category != 'undefined':
            query = query.filter_by(sub_category=sub_category)
        if search and search != 'undefined':
            query = query.filter(
                Product.name.ilike(f'%{search}%') | 
                Product.description.ilike(f'%{search}%')
            )
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if featured:
            query = query.filter_by(is_featured=True)
        
        if sort_by and sort_by != 'undefined':
            sort_column = getattr(Product, sort_by, Product.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        response = make_response(jsonify({
            'products': [product.to_dict() for product in paginated.items],
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginated.pages,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        response = make_response(jsonify({'product': product.to_dict()}))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        logger.error(f"Error in get_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        logger.info(f"Creating product with data: {data}")
        
        required = ['name', 'description', 'price', 'category', 'stock_quantity']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        image_urls = data.get('image_urls', [])
        if isinstance(image_urls, str):
            try:
                image_urls = json.loads(image_urls)
            except:
                image_urls = []
        if not isinstance(image_urls, list):
            image_urls = []
        
        specifications = data.get('specifications', {})
        if isinstance(specifications, str):
            try:
                specifications = json.loads(specifications)
            except:
                specifications = {}
        if not isinstance(specifications, dict):
            specifications = {}
        
        product = Product(
            seller_id=user.id,
            name=data['name'],
            description=data['description'],
            price=float(data['price']),
            category=data['category'],
            sub_category=data.get('sub_category'),
            stock_quantity=int(data['stock_quantity']),
            min_order_quantity=int(data.get('min_order_quantity', 1)),
            image_urls=json.dumps(image_urls),
            specifications=json.dumps(specifications),
            is_featured=data.get('is_featured', False)
        )
        
        db.session.add(product)
        db.session.commit()
        
        response = make_response(jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201)
        
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in create_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        product = Product.query.get_or_404(product_id)
        
        if not user.is_admin and product.seller_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        logger.info(f"Updating product {product_id} with data: {data}")
        
        allowed_fields = ['name', 'description', 'price', 'category', 'sub_category', 
                         'stock_quantity', 'min_order_quantity', 'is_featured', 'is_active']
        
        for field in allowed_fields:
            if field in data and data[field] is not None:
                if field in ['price']:
                    setattr(product, field, float(data[field]))
                elif field in ['stock_quantity', 'min_order_quantity']:
                    setattr(product, field, int(data[field]))
                else:
                    setattr(product, field, data[field])
        
        if 'image_urls' in data and data['image_urls'] is not None:
            image_urls = data['image_urls']
            if isinstance(image_urls, str):
                try:
                    image_urls = json.loads(image_urls)
                except:
                    image_urls = []
            if not isinstance(image_urls, list):
                image_urls = []
            product.image_urls = json.dumps(image_urls)
        
        if 'specifications' in data and data['specifications'] is not None:
            specifications = data['specifications']
            if isinstance(specifications, str):
                try:
                    specifications = json.loads(specifications)
                except:
                    specifications = {}
            if not isinstance(specifications, dict):
                specifications = {}
            product.specifications = json.dumps(specifications)
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        response = make_response(jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200)
        
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in update_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        product = Product.query.get_or_404(product_id)
        
        if not user.is_admin and product.seller_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        product.is_active = False
        db.session.commit()
        
        response = make_response(jsonify({'message': 'Product deleted successfully'}), 200)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@product_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = db.session.query(Product.category).distinct().all()
        response = make_response(jsonify({
            'categories': [cat[0] for cat in categories if cat[0]]
        }))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({'error': str(e)}), 500
