from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'name': 'Harykims Intertech API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'products': '/api/products',
            'orders': '/api/orders',
            'reviews': '/api/reviews',
            'inquiries': '/api/inquiries',
            'wishlist': '/api/wishlist'
        },
        'docs': 'Contact support for API documentation'
    })

@main_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Harykims Intertech Backend',
        'version': '1.0.0'
    })

@main_bp.route('/api/status')
def api_status():
    return jsonify({
        'status': 'online',
        'timestamp': '2024-01-01T00:00:00Z',
        'message': 'API is running smoothly'
    })
