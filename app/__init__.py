from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
import secrets

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
    
    # ============= UPDATED CORS =============
    CORS(app, origins=[
        'http://localhost:3000',
        'http://localhost:5173', 
        'http://localhost:5174',
        'http://127.0.0.1:5173',
        'https://hk-backend-1.onrender.com',
        'https://hydrogenbond68.github.io',  # Your GitHub Pages frontend
        '*'
    ])
    
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
    
    @app.after_request
    def after_request(response):
        response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', '0')
        return response
    
    return app
