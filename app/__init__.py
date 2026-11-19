from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from datetime import timedelta
import os
import secrets
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy()

def resolve_allowed_origins():
    """Resolve the CORS allow-list.

    A reflected Origin combined with Allow-Credentials lets any site issue
    authenticated cross-site requests, so a wildcard is rejected in production.
    """
    configured = [
        origin.strip()
        for origin in (os.environ.get('CORS_ORIGINS') or os.environ.get('FRONTEND_URL') or '').split(',')
        if origin.strip()
    ]

    is_production = os.environ.get('NODE_ENV') == 'production' or bool(os.environ.get('RENDER'))

    if '*' in configured:
        if is_production:
            raise RuntimeError('CORS_ORIGINS must not contain "*" in production; list origins explicitly.')
        return ['*']

    if not configured:
        if is_production:
            raise RuntimeError('CORS_ORIGINS (or FRONTEND_URL) must be set in production.')
        return ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost']

    return configured


def create_app():
    app = Flask(__name__)
    # === BULLETPROOF CORS (auto-generated) ===
    import re as _cors_re
    from flask import request as _cors_request
    from flask_cors import CORS as _CORS

    _CORS_LOCAL_REGEX = r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?"
    _CORS_PROD_LIST = [
        # Add production origins here, e.g. "https://hk.example.com",
    ]

    # Single canonical CORS registration — no other CORS() call should exist.
    _CORS(
        app,
        resources={r"/*": {"origins": [_CORS_LOCAL_REGEX] + _CORS_PROD_LIST}},
        supports_credentials=True,
        allow_headers="*",
        expose_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=600,
        send_wildcard=False,
    )

    _CORS_LOCAL_RE = _cors_re.compile(
        r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?$"
    )
    _CORS_PROD_SET = set(_CORS_PROD_LIST)

    def _cors_allow(origin):
        if not origin:
            return False
        if _CORS_LOCAL_RE.match(origin):
            return True
        return origin in _CORS_PROD_SET

    @app.after_request
    def _force_cors_headers(resp):
        origin = _cors_request.headers.get("Origin")
        if origin and _cors_allow(origin):
            if "Access-Control-Allow-Origin" not in resp.headers:
                resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, ngrok-skip-browser-warning, "
                "X-Requested-With, Cache-Control, Pragma, Expires, Idempotency-Key"
            )
            resp.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
        return resp

    # Socket.IO stubs — BOTH variants so GET /socket.io/ never hits the OPTIONS catch-all.
    @app.route("/socket.io/", methods=["GET", "POST", "OPTIONS"])
    @app.route("/socket.io/<path:_siopath>", methods=["GET", "POST", "OPTIONS"])
    def _socketio_stub(_siopath=""):
        return ({"status": "socket.io not enabled on this backend"}, 501)

    # Catch-all OPTIONS so preflight on unknown paths still returns 204.
    @app.route("/<path:_any>", methods=["OPTIONS"])
    def _cors_preflight_safety(_any=""):
        return ("", 204)
    # === END BULLETPROOF CORS ===

    
    
    
    

    is_production = os.environ.get('NODE_ENV') == 'production' or bool(os.environ.get('RENDER'))

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_production:
            raise RuntimeError('SECRET_KEY must be set in production.')
        secret_key = secrets.token_hex(32)
        logger.warning('SECRET_KEY unset; using an ephemeral development secret. '
                       'Sessions are invalidated on restart.')
    app.config['SECRET_KEY'] = secret_key

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/harykims.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret or len(jwt_secret) < 32:
        if is_production:
            raise RuntimeError('JWT_SECRET_KEY must be set to at least 32 characters in production.')
        jwt_secret = secrets.token_hex(32)
        logger.warning('JWT_SECRET_KEY unset; using an ephemeral development secret. '
                       'All sessions are invalidated on restart.')

    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    db.init_app(app)
    jwt = JWTManager(app)

    allowed_origins = resolve_allowed_origins()
    allows_wildcard = '*' in allowed_origins


    @app.after_request
    def add_cors_headers(response):
        # With a wildcard we must not also claim credentials support; browsers
        # reject that combination, and reflecting the Origin would defeat it.
        if not allows_wildcard:
            origin = request.headers.get('Origin')
            if origin and origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cache-Control, Pragma, Expires, ngrok-skip-browser-warning'
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

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # Keep client errors as JSON. Werkzeug's default HTML body breaks the
        # frontend, which parses every response as JSON, and a malformed request
        # reported as HTML is indistinguishable from a real outage.
        if error.code >= 500:
            logger.error(f"{error.code} on {request.path}: {error}")
        return jsonify({'error': error.name, 'message': error.description}), error.code

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
