from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from models import db, Product, Location

product_bp = Blueprint('product', __name__)
location_bp = Blueprint('location', __name__)

@product_bp.route('/', methods=['GET'])
def index():
    products = Product.query.all()
    enumerated_products = []
    for idx, product in enumerate(products):
        product_info = {
            'id': product.id,
            'index': idx + 1,
            'name': product.name,
            'price': product.price,
            'quantity': product.quantity,
            'location': product.location.name
        }
        enumerated_products.append(product_info)
    return render_template('index.html', products=enumerated_products)

@product_bp.route('/product/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        location_name = request.form['location']

        # Check if the location with the given name already exists
        location = Location.query.filter_by(name=location_name).first()

        # If location doesn't exist, create a new one
        if not location:
            location = Location(name=location_name)
            db.session.add(location)
            db.session.commit()

        # Create a new product with the provided details and the location ID
        product = Product(name=name, price=price, quantity=quantity, location_id=location.id)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('product.index'))

    return render_template('add_product.html')


@product_bp.route('/product/shift/<int:id>', methods=['GET', 'POST'])
def shift_product(id):
    product = Product.query.get_or_404(id)
    all_locations = Location.query.all()
    associated_locations = set(product.location.name for product in Product.query.filter(Product.location_id == Location.id).all())

    locations = [location for location in all_locations if location.name in associated_locations]

    if request.method == 'POST':
        new_location_id = request.form.get('new_location')
        if new_location_id == 'new':
            new_location_name = request.form.get('custom_location')
            location = Location(name=new_location_name)
            db.session.add(location)
            db.session.commit()
            new_location_id = location.id

        # Update the product's location
        product.location_id = new_location_id
        db.session.commit()
        return redirect(url_for('product.index'))

    return render_template('shift_product.html', product=product, locations=locations)

@product_bp.route('/product/delete/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify(success=True)  # Respond with a JSON object indicating success
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)) 
    
@product_bp.route('/product/report', methods=['GET'])
def product_report():
    product_balances = {}  # Dictionary to store product balances in each location

    # Query products and their locations from the database
    products = Product.query.join(Location).all()

    # Populate the product_balances dictionary
    for product in products:
        location_name = product.location.name
        product_info = {
            'name': product.name,
            'quantity': product.quantity,
            'price': product.price
        }

        if location_name not in product_balances:
            product_balances[location_name] = []

        product_balances[location_name].append(product_info)

    return render_template('report.html', product_balances=product_balances)