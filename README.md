# FOOD-ORDING--SYSTEM
A full-stack restaurant ordering system with customer interface and kitchen display, featuring category-based menus, persistent cart, and real-time order management, built with Python Flask.
# Restaurant Ordering System

A modern web-based ordering system for restaurants with a kitchen display system (KDS). This system allows customers to place orders from different categories and enables kitchen staff to efficiently manage and prepare orders.

## Features

- **Multi-category Menu**
  - North Indian Cuisine
  - South Indian Cuisine
  - Mumbai Specials
  - Beverages

- **Customer Features**
  - Browse menu items by category
  - Add items to cart
  - Persistent cart across pages
  - Place orders with total calculation

- **Kitchen Display System (KDS)**
  - Real-time order display
  - Group similar items for efficient preparation
  - Order status management (pending → preparing → completed)
  - Auto-refresh for new orders

## Tech Stack

- **Backend**
  - Python
  - Flask
  - SQLAlchemy
  - SQLite

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript
  - LocalStorage for cart persistence

## Setup Instructions

1. **Prerequisites**
   - Python 3.x
   - pip (Python package manager)

2. **Installation**
   ```bash
   # Clone the repository
   git clone <repository-url>

   # Navigate to project directory
   cd ordering-system

   # Install required packages
   pip install -r requirements.txt
   ```

3. **Database Initialization**
   - The system will automatically create and initialize the database on first run
   - Sample menu items will be added to the database

4. **Running the Application**
   ```bash
   python app.py
   ```
   - The application will start on `http://localhost:5000`

## Usage

1. **Customer Interface**
   - Access the main page at `http://localhost:5000`
   - Navigate through different menu categories
   - Add items to cart
   - Place orders

2. **Kitchen Display**
   - Access the kitchen display at `http://localhost:5000/kitchen.html`
   - View all active orders
   - Update order status as items are prepared
   - System automatically groups similar items for efficient preparation

## Project Structure

```
ordering-system/
├── app.py                 # Main Flask application
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   └── script.js     # Main JavaScript file
│   └── images/           # Image assets
├── templates/
│   ├── index.html        # Main page
│   ├── kitchen.html      # Kitchen display page
│   ├── north-indian.html # North Indian menu
│   ├── south-indian.html # South Indian menu
│   ├── mumbai-special.html # Mumbai specials menu
│   └── beverages.html    # Beverages menu
└── requirements.txt      # Python dependencies
```

## API Endpoints

- `GET /api/menu` - Get all menu items
- `GET /api/menu?category=<category>` - Get menu items by category
- `POST /api/orders` - Create a new order
- `GET /api/kitchen/orders` - Get active orders for kitchen display
- `PUT /api/orders/<order_id>/status` - Update order status

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
