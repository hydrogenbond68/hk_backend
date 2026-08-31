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

# ============= GET ALL PRODUCTS =============
@product_bp.route('', methods=['GET'])
def get_products():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        search = request.args.get('search')
        min_price = request.args.get('min_price') or request.args.get('minPrice')
        max_price = request.args.get('max_price') or request.args.get('maxPrice')
        sort_by = request.args.get('sort_by') or request.args.get('sortBy', 'created_at')
        sort_order = request.args.get('sort_order') or request.args.get('sortOrder', 'desc')
        featured = request.args.get('featured', type=bool)
        include_inactive = request.args.get('include_inactive', type=bool)
        
        # Parse price filters
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
        
        # Build query
        query = Product.query
        
        # Filter by active status (admin can see inactive)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        # Apply filters
        if category and category != 'undefined':
            query = query.filter_by(category=category)
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
        
        # Apply sorting
        if sort_by and sort_by != 'undefined':
            sort_column = getattr(Product, sort_by, Product.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        # Pagination
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

# ============= GET SINGLE PRODUCT =============
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

# ============= CREATE PRODUCT (Admin Only) =============
@product_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        logger.info(f"Creating product with data: {data}")
        
        required = ['name', 'description', 'price', 'category', 'stock_quantity']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Handle image_urls
        image_urls = data.get('image_urls', [])
        if isinstance(image_urls, str):
            try:
                image_urls = json.loads(image_urls)
            except:
                image_urls = []
        if not isinstance(image_urls, list):
            image_urls = []
        
        # Handle specifications
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
        
        logger.info(f"Product created successfully: {product.id} - {product.name}")
        
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

# ============= UPDATE PRODUCT (Admin Only) =============
@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        product = Product.query.get_or_404(product_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_admin and product.seller_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        logger.info(f"Updating product {product_id} with data: {data}")
        
        # Update allowed fields
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
        
        # Handle image_urls
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
        
        # Handle specifications
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
        
        logger.info(f"Product updated successfully: {product.id} - {product.name}")
        
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

# ============= DELETE PRODUCT (Admin Only) =============
@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        product = Product.query.get_or_404(product_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_admin and product.seller_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Soft delete - just deactivate
        product.is_active = False
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Product deleted (deactivated): {product.id} - {product.name}")
        
        response = make_response(jsonify({'message': 'Product deleted successfully'}), 200)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_product: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= GET CATEGORIES =============
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

# ============= BULK UPDATE PRODUCTS (Admin Only) =============
@product_bp.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_products():
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        update_data = data.get('update_data', {})
        
        if not product_ids or not update_data:
            return jsonify({'error': 'Product IDs and update data required'}), 400
        
        updated_count = 0
        for product_id in product_ids:
            product = Product.query.get(product_id)
            if product:
                for field, value in update_data.items():
                    if hasattr(product, field):
                        setattr(product, field, value)
                product.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Updated {updated_count} products',
            'updated_count': updated_count
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk_update_products: {str(e)}")
        return jsonify({'error': str(e)}), 500
