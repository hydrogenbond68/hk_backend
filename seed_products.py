from app import create_app, db
from app.models import Product, User
import json
import random
from datetime import datetime

# Generate 500+ accessories with realistic data and multiple images
def generate_accessories():
    # Categories and their sub-categories
    categories = {
        "Electronics": [
            "Headphones", "Earphones", "Speakers", "Chargers", "Power Banks",
            "USB Cables", "Adapters", "Screen Protectors", "Phone Cases",
            "Smart Watches", "Fitness Trackers", "Bluetooth Trackers",
            "Webcams", "Microphones", "Tripods", "Selfie Sticks",
            "Car Mounts", "Wireless Chargers", "Cable Organizers",
            "Laptop Stands", "Keyboard Covers", "Mouse Pads"
        ],
        "Fashion": [
            "Watches", "Belts", "Wallets", "Sunglasses", "Hats",
            "Scarves", "Gloves", "Jewelry", "Bracelets", "Necklaces",
            "Earrings", "Rings", "Tie Clips", "Cufflinks", "Pocket Squares",
            "Ties", "Bow Ties", "Suspenders", "Shoe Accessories",
            "Bag Accessories", "Keychains", "Phone Charms"
        ],
        "Home & Living": [
            "Decorative Vases", "Picture Frames", "Candles", "Candle Holders",
            "Coasters", "Table Runners", "Placemats", "Napkin Rings",
            "Salt & Pepper Shakers", "Oil Dispensers", "Cooking Utensils",
            "Cutting Boards", "Knife Sets", "Measuring Cups",
            "Storage Jars", "Spice Racks", "Wine Racks", "Bottle Openers",
            "Corkscrews", "Ice Cube Trays", "Baking Molds"
        ],
        "Sports & Outdoors": [
            "Water Bottles", "Gym Bags", "Yoga Mats", "Resistance Bands",
            "Jump Ropes", "Dumbbells", "Kettlebells", "Foam Rollers",
            "Sports Headbands", "Wristbands", "Sweat Towels", "Shaker Bottles",
            "Camping Accessories", "Hiking Gear", "Fishing Accessories",
            "Outdoor Lighting", "Portable Chairs", "Coolers",
            "Sports Watches", "GPS Trackers", "Action Cameras"
        ],
        "Office & Stationery": [
            "Notebooks", "Pens", "Pencils", "Markers", "Highlighters",
            "Sticky Notes", "Desk Organizers", "File Folders", "Binders",
            "Paper Clips", "Staplers", "Tape Dispensers", "Scissors",
            "Desk Lamps", "Wireless Mouse", "Keyboard", "Monitor Stands",
            "Cable Management", "Document Holders", "Whiteboards",
            "Calendars", "Planners", "Business Card Holders"
        ],
        "Automotive": [
            "Car Phone Mounts", "Dash Cams", "USB Car Chargers",
            "Car Air Fresheners", "Seat Covers", "Steering Wheel Covers",
            "Floor Mats", "Trash Cans", "LED Lights", "Car Organizers",
            "Sun Shades", "Bug Shields", "Chrome Accents", "Tire Valves",
            "License Plate Frames", "Key Covers", "Parking Sensors"
        ],
        "Beauty & Grooming": [
            "Hair Brushes", "Combs", "Hair Ties", "Headbands", "Bobby Pins",
            "Makeup Brushes", "Sponges", "Mirrors", "Organizers",
            "Travel Bottles", "Nail Clippers", "Tweezers", "Scissors",
            "Electric Toothbrushes", "Flossers", "Tongue Cleaners",
            "Shaving Kits", "Facial Rollers", "Spa Accessories"
        ],
        "Travel Accessories": [
            "Luggage Tags", "Passport Covers", "Travel Pillows",
            "Eye Masks", "Ear Plugs", "Packing Cubes", "Toiletry Bags",
            "Travel Adapters", "Power Banks", "Carry-on Organizers",
            "Travel Mugs", "Foldable Bags", "TSA Locks", "Notebooks",
            "Travel Journals", "Camera Bags", "Travel Scales"
        ],
        "Gaming Accessories": [
            "Gaming Mice", "Mechanical Keyboards", "Gaming Headsets", "Mouse Pads",
            "Controller Stands", "Cable Management", "Gaming Chairs", "Monitor Arms",
            "RGB Lighting", "Streaming Accessories", "Capture Cards", "Green Screens"
        ],
        "Pet Accessories": [
            "Pet Collars", "Leashes", "Harnesses", "ID Tags",
            "Pet Bowls", "Food Storage", "Pet Beds", "Carriers",
            "Grooming Brushes", "Nail Trimmers", "Toys", "Treat Dispensers"
        ]
    }

    # Brand names
    brands = [
        "TechPro", "EliteGear", "SmartAccess", "PremiumPlus", "InnovationX",
        "Vanguard", "ApexGear", "ZenTech", "PrimeAccess", "EcoSmart",
        "UrbanStyle", "ClassicEdge", "ModernWave", "NovaTech", "PulseGear",
        "Radiant", "Apex", "Axis", "Zenith", "Spectrum"
    ]

    # Generate product names
    def generate_product_name(category, sub_category):
        adjectives = ["Premium", "Deluxe", "Ultra", "Pro", "Advanced", "Essential", "Smart", "Classic", "Modern", "Elite"]
        models = ["Series", "Pro", "Max", "Ultra", "Plus", "Air", "Lite", "Studio", "Sport", "Vibe"]
        
        adj = random.choice(adjectives)
        brand = random.choice(brands)
        model = random.choice(models)
        
        if random.random() < 0.3:
            return f"{brand} {adj} {sub_category} {model}"
        elif random.random() < 0.6:
            return f"{adj} {sub_category} {brand}"
        else:
            return f"{brand} {sub_category} {adj}"

    # Generate product descriptions
    def generate_description(category, sub_category, brand):
        features = [
            f"High-quality {sub_category.lower()} designed for {category.lower()} enthusiasts.",
            f"Premium {sub_category.lower()} with advanced features and durable construction.",
            f"Professional-grade {sub_category.lower()} suitable for both beginners and experts.",
            f"Eco-friendly {sub_category.lower()} made from sustainable materials.",
            f"{brand} presents this {sub_category.lower()} with cutting-edge technology.",
            f"Ergonomic {sub_category.lower()} designed for maximum comfort and efficiency.",
            f"Versatile {sub_category.lower()} perfect for multiple applications.",
            f"Compact and lightweight {sub_category.lower()} ideal for travel.",
            f"High-performance {sub_category.lower()} with exceptional durability.",
            f"Stylish {sub_category.lower()} that combines form and function."
        ]
        
        benefits = [
            "Made with premium materials for long-lasting use",
            "Comes with 1-year warranty",
            "Easy to use and maintain",
            "Suitable for professional and personal use",
            "Compatible with most standard systems",
            "Available in multiple colors and sizes",
            "Backed by excellent customer support"
        ]
        
        desc = random.choice(features) + " "
        desc += random.choice(benefits) + ". "
        if random.random() < 0.3:
            desc += "Perfect for gifting and everyday use."
        
        return desc

    # Generate 3 images per product with different angles
    def get_image_urls(sub_category):
        images = []
        # Different colors for variety
        colors = ['blue', 'red', 'green', 'yellow', 'purple', 'orange', 'pink', 'teal', 'indigo', 'amber', 'lime', 'cyan']
        # Different angles/perspectives
        angles = ['front', 'side', 'back', 'top', 'perspective', 'closeup', 'lifestyle']
        
        # Generate 3 different images per product
        for i in range(3):
            color = random.choice(colors)
            angle = random.choice(angles)
            width = random.choice([400, 500, 600])
            height = random.choice([400, 500, 600])
            # Different placeholder styles
            if i == 0:
                # Main product image
                images.append(f"https://placehold.co/{width}x{height}/{color}/white?text={sub_category.replace(' ', '+')}")
            elif i == 1:
                # Alternate angle
                images.append(f"https://placehold.co/{width}x{height}/{random.choice(colors)}/white?text={sub_category.replace(' ', '+')}+{angle}")
            else:
                # Detail/lifestyle shot
                images.append(f"https://placehold.co/{width}x{height}/{random.choice(colors)}/white?text={sub_category.replace(' ', '+')}+detail")
        return images

    # Generate specifications
    def generate_specifications(sub_category, category):
        specs = {}
        
        if category == "Electronics":
            specs = {
                "Brand": random.choice(brands),
                "Model": f"{random.randint(100, 999)}X",
                "Warranty": f"{random.choice([6, 12, 24, 36])} months",
                "Material": random.choice(["Aluminum", "Plastic", "Glass", "Carbon Fiber", "Stainless Steel"]),
                "Color": random.choice(["Black", "White", "Silver", "Gold", "Blue", "Red"]),
                "Weight": f"{random.randint(50, 500)}g",
                "Dimensions": f"{random.randint(5, 20)}x{random.randint(5, 20)}x{random.randint(1, 10)}cm"
            }
        elif category == "Fashion":
            specs = {
                "Brand": random.choice(brands),
                "Material": random.choice(["Leather", "Fabric", "Metal", "Plastic", "Wood"]),
                "Size": random.choice(["S", "M", "L", "XL", "One Size"]),
                "Color": random.choice(["Black", "Brown", "Tan", "Navy", "White"]),
                "Occasion": random.choice(["Casual", "Formal", "Sport", "Everyday"])
            }
        elif category == "Home & Living":
            specs = {
                "Brand": random.choice(brands),
                "Material": random.choice(["Ceramic", "Glass", "Wood", "Metal", "Plastic"]),
                "Style": random.choice(["Modern", "Classic", "Minimalist", "Rustic", "Contemporary"]),
                "Color": random.choice(["White", "Black", "Natural", "Multi", "Pastel"]),
                "Dimensions": f"{random.randint(10, 30)}x{random.randint(10, 30)}x{random.randint(5, 20)}cm"
            }
        else:
            specs = {
                "Brand": random.choice(brands),
                "Material": random.choice(["Steel", "Aluminum", "Plastic", "Rubber", "Leather"]),
                "Color": random.choice(["Black", "Red", "Blue", "Green", "Yellow"]),
                "Weight": f"{random.randint(100, 1000)}g",
                "Durability": random.choice(["High", "Medium", "Professional"])
            }
        
        return specs

    # Generate prices in KES (Kenya Shillings)
    def generate_price(category):
        # Converting from USD to KES (approx 1 USD = 150 KES)
        if category == "Electronics":
            usd_price = random.uniform(15.99, 299.99)
        elif category == "Fashion":
            usd_price = random.uniform(9.99, 149.99)
        elif category == "Home & Living":
            usd_price = random.uniform(5.99, 89.99)
        elif category == "Sports & Outdoors":
            usd_price = random.uniform(7.99, 199.99)
        elif category == "Office & Stationery":
            usd_price = random.uniform(2.99, 79.99)
        else:
            usd_price = random.uniform(5.99, 99.99)
        
        # Convert to KES (1 USD ≈ 150 KES)
        kes_price = usd_price * 150
        return round(kes_price, 2)

    products = []
    product_id = 1

    # Generate products for each category
    for category, sub_categories in categories.items():
        for sub_category in sub_categories:
            # Generate multiple products for each sub-category
            num_products = random.randint(3, 8)
            
            for _ in range(num_products):
                if len(products) >= 500:
                    break
                    
                brand = random.choice(brands)
                
                product = {
                    "seller_id": 2,
                    "name": generate_product_name(category, sub_category),
                    "description": generate_description(category, sub_category, brand),
                    "price": generate_price(category),
                    "category": category,
                    "sub_category": sub_category,
                    "stock_quantity": random.randint(10, 500),
                    "min_order_quantity": random.randint(1, 5),
                    "image_urls": json.dumps(get_image_urls(sub_category)),
                    "specifications": json.dumps(generate_specifications(sub_category, category)),
                    "is_featured": random.random() < 0.1,
                    "is_active": True
                }
                products.append(product)
                product_id += 1
                
                if len(products) >= 500:
                    break
            if len(products) >= 500:
                break
        if len(products) >= 500:
            break

    return products

def seed_database():
    app = create_app()
    with app.app_context():
        # Check if products already exist
        existing_count = Product.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} products.")
            response = input("Do you want to clear existing products and add new ones? (y/n): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
            # Clear existing products
            Product.query.delete()
            db.session.commit()
            print("Cleared existing products.")

        # Generate products
        print("Generating 500+ products with multiple images...")
        products = generate_accessories()
        
        # Add products to database
        count = 0
        for product_data in products:
            product = Product(**product_data)
            db.session.add(product)
            count += 1
            if count % 50 == 0:
                db.session.commit()
                print(f"Added {count} products...")

        db.session.commit()
        print(f"\n✅ Successfully added {count} products to the database!")
        
        # Show category breakdown
        categories = db.session.query(Product.category, db.func.count()).group_by(Product.category).all()
        print("\n📊 Category Breakdown:")
        for category, count in categories:
            print(f"  - {category}: {count} products")
        
        # Sample products with images
        sample = Product.query.limit(3).all()
        print("\n📦 Sample Products with Images:")
        for p in sample:
            images = json.loads(p.image_urls) if p.image_urls else []
            print(f"  - {p.name} (KES {p.price:.2f})")
            print(f"    Images: {len(images)} images available")

if __name__ == "__main__":
    seed_database()
