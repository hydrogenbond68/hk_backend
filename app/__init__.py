from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
import secrets
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/harykims.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret or len(jwt_secret) < 32:
        jwt_secret = secrets.token_hex(32)

    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    db.init_app(app)
    jwt = JWTManager(app)

    CORS(app, origins='*', allow_headers=['Content-Type', 'Authorization', 'Cache-Control', 'Pragma', 'Expires', 'ngrok-skip-browser-warning'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cache-Control, Pragma, Expires, ngrok-skip-browser-warning'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

    from app import models

    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import product_bp
    from app.routes.order_routes import order_bp
    from app.routes.review_routes import review_bp
    from app.routes.inquiry_routes import inquiry_bp
    from app.routes.wishlist_routes import wishlist_bp
    from app.routes.main_routes import main_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(review_bp, url_prefix='/api/reviews')
    app.register_blueprint(inquiry_bp, url_prefix='/api/inquiries')
    app.register_blueprint(wishlist_bp, url_prefix='/api/wishlist')

    @app.before_request
    def log_request():
        request._start_time = time.time()
        logger.info(f"→ {request.method} {request.path} (Origin: {request.headers.get('Origin', 'none')})")

    @app.after_request
    def log_response(response):
        duration = 0
        if hasattr(request, '_start_time'):
            duration = round((time.time() - request._start_time) * 1000, 2)
        logger.info(f"← {request.method} {request.path} → {response.status_code} ({duration}ms) [CORS: {response.headers.get('Access-Control-Allow-Origin', 'MISSING')}]")
        response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', '0')
        return response

    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"500 error on {request.path}: {error}")
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

    @app.route('/api/debug', methods=['GET'])
    def debug_info():
        from app.models import Product, User, Order
        return jsonify({
            'status': 'ok',
            'database': str(app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')[:50] + '...'),
            'product_count': Product.query.count(),
            'user_count': User.query.count(),
            'order_count': Order.query.count(),
            'cors_origin': request.headers.get('Origin', 'none'),
            'env': os.environ.get('RENDER', 'not_render')
        })

    return app
