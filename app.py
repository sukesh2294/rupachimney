import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from models import db, Admin, Enquiry, ContactMessage, GalleryImage, Service, Customer, Setting, Order

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rupa_chimney.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}



# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='sukesh2294@gmail.com').first():
            admin = Admin(
                username='sukesh2294@gmail.com',
                password_hash=generate_password_hash('sky123')
            )
            db.session.add(admin)
        
        # Create default services if not exists
        if not Service.query.first():
            default_services = [
                Service(
                    title="1 Number Bricks",
                    description="High-quality red bricks perfect for construction",
                    price="₹ 9/Piece",
                    features="Durable, Weather resistant, Standard size",
                    image="brick1.jpg",
                    display_order=1
                ),
                Service(
                    title="2 Number Bricks",
                    description="Premium quality bricks for superior construction",
                    price="₹ 12/Piece",
                    features="High strength, Perfect for load bearing, Long lasting",
                    image="brick2.jpg",
                    display_order=2
                ),
                Service(
                    title="Piket Red Brick",
                    description="Clay piket bricks for decorative purposes",
                    price="₹ 8.50/Piece",
                    features="Aesthetic appeal, Smooth finish, Decorative",
                    image="piket_brick.jpg",
                    display_order=3
                ),
                Service(
                    title="Industrial Chimneys",
                    description="Custom industrial chimneys for factories",
                    price="Contact for Price",
                    features="Custom sizes, High temperature resistance, Durable",
                    image="chimney.jpg",
                    display_order=4
                )
            ]
            db.session.add_all(default_services)
        
        # Create default settings if not exists
        if not Setting.query.first():
            default_settings = [
                Setting(key='company_name', value='Rupa Chimney'),
                Setting(key='company_phone', value='+91-6299924802, +91-7549149491'),
                Setting(key='company_email', value='rupachimney@gmail.com'),
                Setting(key='company_address', value='Nawada Road, Sikandra, Jamui, Bihar - 811315'),
                Setting(key='company_description', value='Leading manufacturer of high-quality bricks and industrial chimneys since 1998'),
                Setting(key='whatsapp_number', value='917549149491'),
                Setting(key='facebook_url', value='#'),
                Setting(key='twitter_url', value='#'),
                Setting(key='instagram_url', value='#'),
                Setting(key='linkedin_url', value='#'),
                Setting(key='youtube_url', value='#')
            ]
            db.session.add_all(default_settings)
        
        db.session.commit()

# Home Page Route
@app.route('/')
def home():
    """Home page"""
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
    settings = {s.key: s.value for s in Setting.query.all()}
    slider_images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return render_template('index.html', services=services, settings=settings, slider_images=slider_images)

# About Page Route
@app.route('/about')
def about():
    """About page"""
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template('about.html', settings=settings)

# Services Page Route
@app.route('/services')
def services():
    """Services page"""
    services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template('services.html', services=services, settings=settings)

# Contact Page Route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    settings = {s.key: s.value for s in Setting.query.all()}
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Create contact message
        contact_msg = ContactMessage(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        
        db.session.add(contact_msg)
        db.session.commit()
        
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', settings=settings)

# Enquiry Form Handler
@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    """Handle enquiry form submission"""
    try:
        if request.is_json:
            # JSON request from service modal
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            message = data.get('message')
            enquiry_type = 'service'
        else:
            # Form data from main enquiry form
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            message = request.form.get('message')
            enquiry_type = request.form.get('enquiry_type', 'general')
            product_name = request.form.get('product_name', 'Rupa Chimney Bricks')
            
            # Build message from form data
            message = f"Enquiry Type: {enquiry_type}\nProduct: {product_name}\nMessage: {message}"

        # Create new enquiry
        enquiry = Enquiry(
            name=name,
            email=email,
            phone=phone,
            message=message,
            enquiry_type=enquiry_type
        )
        
        db.session.add(enquiry)
        db.session.commit()
        
        flash('Thank you for your enquiry! We will contact you soon.', 'success')
        
        if request.is_json:
            return jsonify({'message': 'Enquiry submitted successfully'})
        else:
            return redirect(url_for('home'))
            
    except Exception as e:
        print(f"Error submitting enquiry: {e}")
        if request.is_json:
            return jsonify({'error': 'Failed to submit enquiry'}), 500
        else:
            flash('Error submitting enquiry. Please try again.', 'danger')
            return redirect(url_for('home'))

# API Routes
@app.route('/api/services')
def api_services():
    """API endpoint to get active services"""
    try:
        services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
        return jsonify([{
            'id': s.id,
            'title': s.title,
            'description': s.description,
            'price': s.price,
            'features': s.features,
            'image': s.image,
            'is_active': s.is_active,
            'display_order': s.display_order
        } for s in services])
    except Exception as e:
        print(f"Error fetching services: {e}")
        return jsonify([])

@app.route('/api/settings')
def api_settings():
    """API endpoint to get settings"""
    try:
        settings = Setting.query.all()
        return jsonify({s.key: s.value for s in settings})
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return jsonify({})

# Admin Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_user'] = username
            session.permanent = True
            app.permanent_session_lifetime = 1800  # 30 minutes
            
            flash("✅ Successfully logged in!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("❌ Invalid username or password", "danger")
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash("🔒 Please log in to access the admin dashboard", "warning")
        return redirect(url_for('admin_login'))
    
    # Get dashboard statistics
    total_enquiries = Enquiry.query.count()
    total_gallery_images = GalleryImage.query.count()
    pending_orders = Enquiry.query.filter_by(status='pending').count()
    total_customers = ContactMessage.query.count()
    
    return render_template('admin_dashboard.html',
                         Administrator='Sukesh',
                         total_enquiries=total_enquiries,
                         total_gallery_images=total_gallery_images,
                         pending_orders=pending_orders,
                         total_customers=total_customers)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash("👋 Successfully logged out", "info")
    return redirect(url_for('home'))

# Enquiry Management Routes
@app.route('/admin/enquiries')
def admin_enquiries():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    enquiries = Enquiry.query.order_by(Enquiry.created_at.desc()).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'email': e.email,
        'phone': e.phone,
        'message': e.message,
        'status': e.status,
        'created_at': e.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for e in enquiries])

@app.route('/admin/enquiries/<int:enquiry_id>', methods=['PUT'])
def update_enquiry(enquiry_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    data = request.get_json()
    
    if 'status' in data:
        enquiry.status = data['status']
    
    db.session.commit()
    return jsonify({'message': 'Enquiry updated successfully'})

@app.route('/admin/enquiries/<int:enquiry_id>', methods=['DELETE'])
def delete_enquiry(enquiry_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    db.session.delete(enquiry)
    db.session.commit()
    return jsonify({'message': 'Enquiry deleted successfully'})

# Gallery Management Routes <.........................................................................>
@app.route('/admin/gallery')
def admin_gallery():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return jsonify([{
        'id': img.id,
        'filename': img.filename,
        'caption': img.caption,
        'category': img.category,
        'uploaded_at': img.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
    } for img in images])

@app.route('/admin/gallery', methods=['POST'])
def upload_gallery_image():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'image' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        gallery_image = GalleryImage(
            filename=filename,
            caption=request.form.get('caption', ''),
            category=request.form.get('category', 'general')
        )
        db.session.add(gallery_image)
        db.session.commit()
        
        return jsonify({'message': 'Image uploaded successfully'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/admin/gallery/<int:image_id>', methods=['DELETE'])
def delete_gallery_image(image_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    image = GalleryImage.query.get_or_404(image_id)
    
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
    except OSError:
        pass  
    
    db.session.delete(image)
    db.session.commit()
    return jsonify({'message': 'Image deleted successfully'})

# Service Management Routes <.............................................................................>
@app.route('/admin/services')
def admin_services():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    services = Service.query.order_by(Service.display_order, Service.title).all()
    return jsonify([{
        'id': s.id,
        'title': s.title,
        'description': s.description,
        'price': s.price,
        'is_active': s.is_active,
        'display_order': s.display_order,
        'image': s.image,
        'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for s in services])



@app.route('/admin/services', methods=['POST'])
def create_service():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if image file is present
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename
        else:
            image_filename = None
    else:
        image_filename = None
    
    data = request.form
    is_active = data.get('is_active', 'false').lower() == 'true'
    
    try:
        display_order = int(data.get('display_order', 0))
    except (ValueError, TypeError):
        display_order = 0

    service = Service(
        title=data.get('title'),
        description=data.get('description', ''),
        price=data.get('price', ''),
        is_active=is_active,
        display_order=display_order,
        image=image_filename  
    )
    db.session.add(service)
    db.session.commit()
    
    return jsonify({'message': 'Service created successfully'})

@app.route('/admin/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    service = Service.query.get_or_404(service_id)
    
    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '' and allowed_file(file.filename):
            if service.image:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service.image))
                except OSError:
                    pass
            
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            service.image = filename
    
    data = request.form
    
    if 'is_active' in data:
        service.is_active = data.get('is_active').lower() == 'true'
    
    if 'display_order' in data:
        try:
            service.display_order = int(data.get('display_order'))
        except (ValueError, TypeError):
            pass
    service.title = data.get('title', service.title)
    service.description = data.get('description', service.description)
    service.price = data.get('price', service.price)
    service.is_active = data.get('is_active', service.is_active)
    service.display_order = data.get('display_order', service.display_order)
    
    db.session.commit()
    return jsonify({'message': 'Service updated successfully'})

# @app.route('/admin/services', methods=['POST'])
# def create_service():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Unauthorized'}), 401
    
#     data = request.get_json()
#     service = Service(
#         title=data['title'],
#         description=data.get('description', ''),
#         price=data.get('price', ''),
#         is_active=data.get('is_active', True),
#         display_order=data.get('display_order', 0),
#         image=data.get('image', None )
#     )
#     db.session.add(service)
#     db.session.commit()
    
#     return jsonify({'message': 'Service created successfully'})

# @app.route('/admin/services/<int:service_id>', methods=['PUT'])
# def update_service(service_id):
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Unauthorized'}), 401
    
#     service = Service.query.get_or_404(service_id)
#     data = request.get_json()
    
#     service.title = data.get('title', service.title)
#     service.description = data.get('description', service.description)
#     service.price = data.get('price', service.price)
#     service.is_active = data.get('is_active', service.is_active)
#     service.display_order = data.get('display_order', service.display_order)
#     service.image = data.get('image', service.image)
    
#     db.session.commit()
#     return jsonify({'message': 'Service updated successfully'})

@app.route('/admin/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Service deleted successfully'})

# Customer Management Routes
@app.route('/admin/customers')
def admin_customers():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email,
        'phone': c.phone,
        'address': c.address,
        'is_blacklisted': c.is_blacklisted,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for c in customers])

@app.route('/admin/customers/<int:customer_id>/blacklist', methods=['PUT'])
def toggle_blacklist_customer(customer_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    customer = Customer.query.get_or_404(customer_id)
    customer.is_blacklisted = not customer.is_blacklisted
    db.session.commit()
    
    action = "blacklisted" if customer.is_blacklisted else "removed from blacklist"
    return jsonify({'message': f'Customer {action} successfully'})

# Order Management Routes
@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    orders = Order.query.options(db.joinedload(Order.customer), db.joinedload(Order.service))\
                      .order_by(Order.created_at.desc()).all()
    
    return jsonify([{
        'id': o.id,
        'customer_name': o.customer.name,
        'service_title': o.service.title,
        'order_date': o.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'status': o.status,
        'total_amount': o.total_amount,
        'notes': o.notes
    } for o in orders])

@app.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if 'status' in data:
        order.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Order status updated successfully'})
    
    return jsonify({'error': 'Status is required'}), 400

# Settings Routes
@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    settings = Setting.query.all()
    return jsonify({s.key: s.value for s in settings})

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    for key, value in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()
    return jsonify({'message': 'Settings updated successfully'})


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    init_db()
    app.run(debug=True)

