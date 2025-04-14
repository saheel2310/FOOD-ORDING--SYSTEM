from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import json

app = Flask(__name__, static_folder='static')
CORS(app)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakfast_ordering.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False, index=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'category': self.category
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.Text, nullable=False)  # store JSON list of item IDs
    total_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, preparing, completed

    def serialize(self):
        return {
            'id': self.id,
            'items': json.loads(self.items),
            'total_amount': self.total_amount,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'status': self.status
        }

# --- Routes ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/menu', methods=['GET'])
def get_menu():
    category = request.args.get('category')
    if category:
        items = MenuItem.query.filter_by(category=category).all()
    else:
        items = MenuItem.query.all()
    return jsonify([item.serialize() for item in items])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    client_items = data.get('items')

    if not client_items or not isinstance(client_items, list):
        return jsonify({'error': 'Invalid or missing "items" list in request'}), 400

    verified_items_for_order = []
    calculated_total = 0.0
    item_ids = [item.get('id') for item in client_items if item.get('id') is not None]

    if not item_ids:
        return jsonify({'error': 'No valid item IDs provided in the order'}), 400

    try:
        menu_items_from_db = MenuItem.query.filter(MenuItem.id.in_(item_ids)).all()
        db_items_dict = {item.id: item for item in menu_items_from_db}

        for client_item in client_items:
            item_id = client_item.get('id')
            if item_id is None:
                continue

            db_item = db_items_dict.get(item_id)
            if not db_item:
                return jsonify({'error': f'Invalid menu item ID: {item_id}'}), 400

            verified_items_for_order.append({
                'id': db_item.id,
                'name': db_item.name,
                'price': db_item.price
            })
            calculated_total += db_item.price

        if not verified_items_for_order:
            return jsonify({'error': 'No valid items to place order'}), 400

        order = Order(
            items=json.dumps(verified_items_for_order),
            total_amount=calculated_total,
            status='pending'
        )

        db.session.add(order)
        db.session.commit()

        app.logger.info(f"Order created successfully: ID {order.id}")
        return jsonify(order.serialize()), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating order: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    return jsonify([order.serialize() for order in orders])

@app.route('/api/kitchen/orders', methods=['GET'])
def get_kitchen_orders():
    # Get all pending and preparing orders
    orders = Order.query.filter(Order.status.in_(['pending', 'preparing'])).order_by(Order.timestamp.asc()).all()
    
    # Group items from all orders
    all_items = []
    for order in orders:
        items = json.loads(order.items)
        for item in items:
            item['order_id'] = order.id
            item['order_timestamp'] = order.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            all_items.append(item)
    
    # Group items by name and count occurrences
    grouped_items = {}
    for item in all_items:
        if item['name'] not in grouped_items:
            grouped_items[item['name']] = {
                'name': item['name'],
                'count': 0,
                'order_ids': set(),
                'orders': []
            }
        grouped_items[item['name']]['count'] += 1
        grouped_items[item['name']]['order_ids'].add(item['order_id'])
        grouped_items[item['name']]['orders'].append({
            'order_id': item['order_id'],
            'timestamp': item['order_timestamp']
        })
    
    # Convert sets to lists for JSON serialization
    for item in grouped_items.values():
        item['order_ids'] = list(item['order_ids'])
    
    return jsonify({
        'grouped_items': grouped_items,
        'total_orders': len(orders)
    })

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    new_status = data.get('status')
    
    if not new_status or new_status not in ['pending', 'preparing', 'completed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    order = Order.query.get_or_404(order_id)
    order.status = new_status
    
    try:
        db.session.commit()
        return jsonify(order.serialize())
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating order status: {e}")
        return jsonify({'error': 'Server error'}), 500

# --- Create Tables ---
def initialize_app():
    with app.app_context():
        # Drop all tables to recreate them with the new schema
        db.drop_all()
        # Create all tables with the new schema
        db.create_all()
        initialize_menu_items()

# --- START OF initialize_menu_items function in app.py ---

def initialize_menu_items():
    """Adds predefined menu items to the database if they don't exist."""
    menu_items_data = [
        # === North Indian (Exactly 10 items as specified) ===
        {'name': 'Aloo Paratha', 'price': 80, 'description': 'Stuffed with spiced potatoes.', 'category': 'north-indian'},
        {'name': 'Paneer Paratha', 'price': 100, 'description': 'Stuffed with cottage cheese.', 'category': 'north-indian'},
        {'name': 'Chole Bhature', 'price': 120, 'description': 'Chickpeas curry with fried bread.', 'category': 'north-indian'},
        {'name': 'Gobi Paratha', 'price': 85, 'description': 'Stuffed with cauliflower.', 'category': 'north-indian'},
        {'name': 'Poori Bhaji', 'price': 90, 'description': 'Fried bread with potato curry.', 'category': 'north-indian'},
        {'name': 'Onion Paratha', 'price': 80, 'description': 'Stuffed with onions.', 'category': 'north-indian'},
        {'name': 'Amritsari Kulcha', 'price': 110, 'description': 'Stuffed bread with chole.', 'category': 'north-indian'},
        {'name': 'Moong Dal Cheela', 'price': 75, 'description': 'Lentil pancakes.', 'category': 'north-indian'},
        {'name': 'Matar Kachori', 'price': 70, 'description': 'Green pea stuffed pastry.', 'category': 'north-indian'},
        {'name': 'Aloo Tikki Chaat', 'price': 95, 'description': 'Potato patties with chutneys.', 'category': 'north-indian'},

        # === South Indian (10 items from previous list) ===
        {'name': 'Idli (3 pcs)', 'price': 60, 'description': 'Steamed rice cakes.', 'category': 'south-indian'},
        {'name': 'Masala Dosa', 'price': 120, 'description': 'Rice crepe with spiced potato.', 'category': 'south-indian'},
        {'name': 'Medu Vada (2 pcs)', 'price': 70, 'description': 'Lentil doughnuts.', 'category': 'south-indian'},
        {'name': 'Plain Dosa', 'price': 90, 'description': 'Crispy crepe.', 'category': 'south-indian'},
        {'name': 'Rava Dosa', 'price': 110, 'description': 'Semolina crepe.', 'category': 'south-indian'},
        {'name': 'Uttapam (Onion)', 'price': 100, 'description': 'Thick pancake with onions.', 'category': 'south-indian'},
        {'name': 'Pongal', 'price': 85, 'description': 'Savory rice-lentil mix.', 'category': 'south-indian'},
        {'name': 'Upma', 'price': 65, 'description': 'Roasted semolina porridge.', 'category': 'south-indian'},
        {'name': 'Pesarattu', 'price': 130, 'description': 'Green gram dosa.', 'category': 'south-indian'}, # Name corrected from previous iteration if needed
        {'name': 'Appam with Stew', 'price': 115, 'description': 'Rice hoppers with stew.', 'category': 'south-indian'},

        # === Mumbai Special (10 items from previous list) ===
        {'name': 'Vada Pav', 'price': 40, 'description': 'Potato fritter in bun.', 'category': 'mumbai-special'},
        {'name': 'Misal Pav', 'price': 80, 'description': 'Sprouted lentil curry with pav.', 'category': 'mumbai-special'},
        {'name': 'Pav Bhaji', 'price': 90, 'description': 'Vegetable curry with pav.', 'category': 'mumbai-special'},
        {'name': 'Kanda Poha', 'price': 60, 'description': 'Flattened rice with onions.', 'category': 'mumbai-special'},
        {'name': 'Sabudana Khichdi', 'price': 75, 'description': 'Tapioca with peanuts.', 'category': 'mumbai-special'},
        {'name': 'Bombay Sandwich', 'price': 85, 'description': 'Grilled veggie sandwich.', 'category': 'mumbai-special'},
        {'name': 'Masala Omelette Pav', 'price': 70, 'description': 'Spicy omelette with pav.', 'category': 'mumbai-special'},
        {'name': 'Bun Maska Chai', 'price': 50, 'description': 'Buttered bun with tea.', 'category': 'mumbai-special'},
        {'name': 'Dabeli', 'price': 45, 'description': 'Spicy potato in bun.', 'category': 'mumbai-special'},
        {'name': 'Ragda Pattice', 'price': 80, 'description': 'Patties with white pea curry.', 'category': 'mumbai-special'},

        # === Beverages (10 items from previous list) ===
        {'name': 'Masala Chai', 'price': 30, 'description': 'Spiced Indian tea.', 'category': 'beverages'},
        {'name': 'Filter Coffee', 'price': 40, 'description': 'South Indian coffee.', 'category': 'beverages'},
        {'name': 'Sweet Lassi', 'price': 50, 'description': 'Sweet yogurt drink.', 'category': 'beverages'},
        {'name': 'Salted Lassi', 'price': 45, 'description': 'Spiced buttermilk.', 'category': 'beverages'}, # Name clarified if needed
        {'name': 'Mango Lassi', 'price': 65, 'description': 'Mango yogurt drink.', 'category': 'beverages'},
        {'name': 'Fresh Lime Soda', 'price': 40, 'description': 'Lime soda.', 'category': 'beverages'},
        {'name': 'Jaljeera', 'price': 35, 'description': 'Spicy cumin cooler.', 'category': 'beverages'},
        {'name': 'Badam Milk', 'price': 60, 'description': 'Almond milk.', 'category': 'beverages'},
        {'name': 'Kokum Sharbat', 'price': 45, 'description': 'Kokum fruit cooler.', 'category': 'beverages'},
        {'name': 'Bottled Water', 'price': 20, 'description': 'Drinking water.', 'category': 'beverages'}
    ]

    with app.app_context():
        print("Initializing menu items...")
        items_added_count = 0
        items_updated_count = 0 # Keep track of updates too
        # Get all existing item names for efficient checking
        existing_names = {item.name for item in MenuItem.query.with_entities(MenuItem.name).all()}

        for item_data in menu_items_data:
            item_name = item_data['name']
            if item_name not in existing_names:
                try:
                    menu_item = MenuItem(**item_data)
                    db.session.add(menu_item)
                    items_added_count += 1
                    existing_names.add(item_name) # Add to set after adding to DB queue
                except Exception as e:
                    app.logger.error(f"Error adding new item '{item_name}': {e}")
                    db.session.rollback() # Rollback specific item addition
            else:
                 # Optional: Update existing item if data differs (e.g., price change)
                 try:
                     existing_item = MenuItem.query.filter_by(name=item_name).first()
                     if existing_item:
                         updated = False
                         if existing_item.price != item_data['price']:
                             existing_item.price = item_data['price']
                             updated = True
                         if existing_item.description != item_data['description']:
                             existing_item.description = item_data['description']
                             updated = True
                         if existing_item.category != item_data['category']:
                             existing_item.category = item_data['category']
                             updated = True
                         # Add other fields if needed

                         if updated:
                             items_updated_count +=1
                 except Exception as e:
                     app.logger.error(f"Error checking/updating existing item '{item_name}': {e}")
                     db.session.rollback() # Rollback potential update attempt

        # Commit all adds/updates at the end
        try:
            db.session.commit()
            if items_added_count > 0:
                 print(f"{items_added_count} new menu items added to the database.")
            if items_updated_count > 0:
                 print(f"{items_updated_count} existing menu items updated in the database.")
            if items_added_count == 0 and items_updated_count == 0:
                print("No new menu items to add or update.")
        except Exception as e:
             db.session.rollback()
             app.logger.error(f"Error committing menu item changes: {e}")

        # Optional: Remove items from DB that are no longer in menu_items_data
        current_names_in_code = {item['name'] for item in menu_items_data}
        items_to_delete = MenuItem.query.filter(MenuItem.name.notin_(current_names_in_code)).all()
        if items_to_delete:
            print(f"Found {len(items_to_delete)} items in DB not present in the code list. Deleting them...")
            for item in items_to_delete:
                db.session.delete(item)
            try:
                db.session.commit()
                print(f"Successfully deleted {len(items_to_delete)} obsolete items.")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error deleting obsolete menu items: {e}")

        print("Menu item initialization finished.")

# --- END OF initialize_menu_items function in app.py ---

if __name__ == '__main__':
    initialize_app()
    app.run(debug=True)

