from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc
import time
from os import environ, path
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/games'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database configuration
DB_SERVER = r'HASSAN-ARZ1946\SQLEXPRESS'  # Your SQL Server name
DB_DATABASE = 'game_1'  # Your database name

# SQL Server connection string for Windows Authentication
conn_str = f'DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};Trusted_Connection=yes;'

def get_db_connection():
    return pyodbc.connect(conn_str)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT UserId, Name, Role, Password FROM Users WITH (INDEX(UserDetails)) WHERE Email = ?', email)
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and user.Password == password:
            session['user_id'] = user.UserId
            session['username'] = user.Name
            session['role'] = user.Role
            session['login_attempts'] = 0  # Reset on successful login
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            session['login_attempts'] += 1
            now_ts = time.time() # Use Unix timestamp
            
            if session['login_attempts'] >= 3:
                # Check if cooldown period is active
                last_attempt_ts = session.get('last_attempt_timestamp')
                if last_attempt_ts:
                    cooldown_seconds = 20
                    time_diff = now_ts - last_attempt_ts
                    if time_diff < cooldown_seconds:
                        remaining_time = int(cooldown_seconds - time_diff)
                        # Flash message removed, template will handle display
                        return render_template('login.html')
                # If cooldown is over or not yet set, record the current attempt time
                session['last_attempt_timestamp'] = now_ts
                # Flash message removed, template will handle display
            else:
                flash('Invalid email or password', 'danger')
                session.pop('last_attempt_timestamp', None) # Clear timestamp if attempts < 3

    # Check cooldown on GET request too
    last_attempt_ts = session.get('last_attempt_timestamp')
    cooldown_active = False
    remaining_time = 0
    if session.get('login_attempts', 0) >= 3 and last_attempt_ts:
        cooldown_seconds = 20
        time_diff = time.time() - last_attempt_ts
        if time_diff < cooldown_seconds:
            cooldown_active = True
            remaining_time = int(cooldown_seconds - time_diff)
            # Flash message removed, template will handle display
        else: # Cooldown finished, reset attempts
             session['login_attempts'] = 0
             session.pop('last_attempt_timestamp', None)

    return render_template('login.html', cooldown_active=cooldown_active, remaining_time=remaining_time)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Print form data for debugging
            print("Form data received:", request.form)
            
            name = request.form['name']
            email = request.form['email']
            phone = request.form.get('phone', '')  # Default to empty string if not provided
            password = request.form['password']
            role = 'customer'
            
            # Email validation - check for @ character and valid domain
            if '@' not in email:
                flash('Email must contain @ character.', 'danger')
                return render_template('register.html')
                
            # Extract domain from email
            domain = email.split('@')[1].lower()
            allowed_domains = ['gmail.com', 'hotmail.com', 'yahoo.com']
            
            if domain not in allowed_domains:
                flash('Email domain must be gmail.com, hotmail.com, or yahoo.com.', 'danger')
                return render_template('register.html')
            
            # Phone number validation and formatting
            if phone:
                # Remove any non-digit characters
                phone = ''.join(filter(str.isdigit, phone))
                
                # Check if phone has at least 11 digits
                if len(phone) < 10:
                    flash('Phone number must be at least 11 digits.', 'danger')
                    return render_template('register.html')
                    
                # If phone is empty after filtering, set to NULL
                if not phone:
                    phone = None
            else:
                phone = None  # Ensure NULL for empty strings
            
            # Input validation for required fields
            if not name or not email or not password:
                flash('Name, email, and password are required fields.', 'danger')
                return render_template('register.html')
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Debug print statements
            print(f"Attempting to register: Name={name}, Email={email}, Phone={phone}, Role={role}")
            
            try:
                # Insert new user
                cursor.execute('''
                    INSERT INTO Users (Name, Email, Phone, Role, Password)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, email, phone, role, password))
                
                conn.commit()
                print("User registration successful!")
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
                
            except pyodbc.IntegrityError as ie:
                print(f"IntegrityError: {str(ie)}")
                # Check what constraint was violated
                if "Email" in str(ie):
                    flash('Email already exists. Please use a different email.', 'danger')
                elif "Phone" in str(ie):
                    flash('Phone number already exists. Please use a different phone number.', 'danger')
                else:
                    flash(f'Registration failed: {str(ie)}', 'danger')
                conn.rollback()
                
            except Exception as e:
                print(f"Other exception: {str(e)}")
                flash(f'Registration failed: {str(e)}', 'danger')
                conn.rollback()
                
            finally:
                cursor.close()
                conn.close()
                
        except Exception as outer_e:
            print(f"Outer exception: {str(outer_e)}")
            flash(f'An error occurred: {str(outer_e)}', 'danger')
            
    return render_template('register.html')
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT g.GameId, g.GameTitle, g.Genre, g.Price, g.Platform, g.Description, i.StockQuantity, g.ImageURL
        FROM Games g
        JOIN Inventory i ON g.GameId = i.GameId
        ORDER BY g.GameTitle
    ''')
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', games=games)

@app.route('/game/<int:game_id>')
@login_required
def game_details(game_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT g.GameId, g.GameTitle, g.Description, g.Genre, g.Price, g.Platform, i.StockQuantity
        FROM Games g
        JOIN Inventory i ON g.GameId = i.GameId
        WHERE g.GameId = ?
    ''', game_id)
    game = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('game_details.html', game=game)

@app.route('/add_to_cart/<int:game_id>', methods=['POST'])
@login_required
def add_to_cart(game_id):
    quantity = int(request.form.get('quantity', 1))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT g.Price, i.StockQuantity
            FROM Games g
            JOIN Inventory i ON g.GameId = i.GameId
            WHERE g.GameId = ?
        ''', game_id)
        game = cursor.fetchone()
        if not game or game.StockQuantity < quantity:
            flash('Not enough stock available', 'danger')
            return redirect(url_for('index'))
        cursor.execute('''
            SELECT CartId, Quantity
            FROM Cart
            WHERE UserId = ? AND GameId = ? AND OrderId IS NULL
        ''', (session['user_id'], game_id))
        existing = cursor.fetchone()
        if existing:
            new_quantity = existing.Quantity + quantity
            if new_quantity > game.StockQuantity:
                flash('Not enough stock available', 'danger')
                return redirect(url_for('index'))
            cursor.execute('''
                UPDATE Cart SET Quantity = ? WHERE CartId = ?
            ''', (new_quantity, existing.CartId))
        else:
            cursor.execute('''
                INSERT INTO Cart (UserId, GameId, Quantity)
                VALUES (?, ?, ?)
            ''', (session['user_id'], game_id, quantity))
        conn.commit()
        flash('Game added to cart!', 'success')
    except:
        conn.rollback()
        flash('Error adding game to cart', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.CartId, g.GameId, g.GameTitle, g.Price, c.Quantity, g.Price * c.Quantity AS TotalAmount
        FROM Cart c
        JOIN Games g ON c.GameId = g.GameId
        WHERE c.UserId = ? AND c.OrderId IS NULL
        ORDER BY c.CartId DESC
    ''', session['user_id'])
    cart_items = cursor.fetchall()
    cart_total = sum(item.TotalAmount for item in cart_items) if cart_items else 0
    cursor.close()
    conn.close()
    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)

@app.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    quantity = int(request.form.get('quantity', 1))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get the game's stock quantity
        cursor.execute('''
            SELECT g.GameId, i.StockQuantity
            FROM Cart c
            JOIN Games g ON c.GameId = g.GameId
            JOIN Inventory i ON g.GameId = i.GameId
            WHERE c.CartId = ? AND c.UserId = ?
        ''', (cart_id, session['user_id']))
        result = cursor.fetchone()
        
        if not result:
            flash('Cart item not found', 'danger')
            return redirect(url_for('cart'))
            
        if quantity > result.StockQuantity:
            flash('Not enough stock available', 'danger')
            return redirect(url_for('cart'))
            
        if quantity <= 0:
            cursor.execute('DELETE FROM Cart WHERE CartId = ? AND UserId = ?', 
                         (cart_id, session['user_id']))
            flash('Item removed from cart', 'success')
        else:
            cursor.execute('''
                UPDATE Cart 
                SET Quantity = ? 
                WHERE CartId = ? AND UserId = ?
            ''', (quantity, cart_id, session['user_id']))
            flash('Cart updated successfully', 'success')
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Error updating cart: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Cart WHERE CartId = ? AND UserId = ?', (cart_id, session['user_id']))
        conn.commit()
        flash('Item removed from cart successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error removing item from cart: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('cart'))

@app.route('/order_summary')
@login_required
def order_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.CartId, g.GameId, g.GameTitle, g.Price, c.Quantity, g.Price * c.Quantity AS TotalAmount
        FROM Cart c
        JOIN Games g ON c.GameId = g.GameId
        WHERE c.UserId = ? AND c.OrderId IS NULL
        ORDER BY c.CartId DESC
    ''', session['user_id'])
    cart_items = cursor.fetchall()
    cart_total = sum(item.TotalAmount for item in cart_items) if cart_items else 0
    cursor.close()
    conn.close()
    return render_template('order_summary.html', cart_items=cart_items, cart_total=cart_total)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT COUNT(*) AS count FROM Cart WHERE UserId = ? AND OrderId IS NULL
        ''', session['user_id'])
        if cursor.fetchone().count == 0:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('cart'))
            
        cursor.execute('''
            SELECT c.CartId, c.GameId, c.Quantity, g.Price
            FROM Cart c
            JOIN Games g ON c.GameId = g.GameId
            WHERE c.UserId = ? AND OrderId IS NULL
        ''', session['user_id'])
        cart_items = cursor.fetchall()
        
        if not cart_items:
            flash('Cart is invalid', 'danger')
            return redirect(url_for('cart'))
            
        # Calculate total amount
        total_amount = sum(item.Price * item.Quantity for item in cart_items)
        
        # Create order with Completed status
        cursor.execute('''
            INSERT INTO Orders (UserId, Status, TotalAmount, OrderDate, OrderTime)
            OUTPUT INSERTED.OrderId
            VALUES (?, ?, ?, CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME))
        ''', (session['user_id'], 'Completed', total_amount))
        order_id = cursor.fetchone()[0]

        if not order_id:
            raise Exception('Order ID creation failed')
            
        # Update cart items with order ID
        cursor.execute('''
            UPDATE Cart SET OrderId = ? WHERE UserId = ? AND OrderId IS NULL
        ''', (order_id, session['user_id']))
        
        # Create payment record with Paid status
        payment_method = request.form.get('payment_method')
        if not payment_method:
            raise Exception('Payment method is required')
            
        cursor.execute('''
            INSERT INTO Payments (OrderId, PaymentMethod, PaymentStatus)
            VALUES (?, ?, ?)
        ''', (order_id, payment_method, 'Paid'))
        
        # Update inventory
        for item in cart_items:
            cursor.execute('''
                UPDATE Inventory 
                SET StockQuantity = StockQuantity - ? 
                WHERE GameId = ?
            ''', (item.Quantity, item.GameId))
        
        conn.commit()
        flash('Payment successful! Your order has been placed.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Checkout error: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.OrderId, o.OrderDate, o.OrderTime, o.TotalAmount, o.Status, p.PaymentStatus
        FROM Orders o
        JOIN Payments p ON o.OrderId = p.OrderId
        WHERE o.UserId = ?
        ORDER BY o.OrderDate DESC, o.OrderTime DESC
    ''', session['user_id'])
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all games with their stock quantities
    cursor.execute('''
        SELECT g.GameId, g.GameTitle, i.StockQuantity
        FROM Games g
        JOIN Inventory i ON g.GameId = i.GameId
        ORDER BY g.GameTitle
    ''')
    games = cursor.fetchall()
    
    # Get all users
    cursor.execute("SELECT UserId, Name, Email FROM Users WHERE Role != 'admin'")
    users = cursor.fetchall()
    
    # Get all orders with user information
    cursor.execute('''
        SELECT o.OrderId, o.OrderDate, o.OrderTime, 
               COALESCE(o.TotalAmount, 0) as TotalAmount,
               o.Status, p.PaymentStatus, p.PaymentMethod,
               u.Name as CustomerName, u.Email as CustomerEmail
        FROM Orders o
        JOIN Payments p ON o.OrderId = p.OrderId
        JOIN Users u ON o.UserId = u.UserId
        ORDER BY o.OrderDate DESC, o.OrderTime DESC
    ''')
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('admin.html', games=games, users=users, orders=orders)

@app.route('/update_inventory', methods=['POST'])
@login_required
@admin_required
def update_inventory():
    game_id = request.form.get('game_id')
    quantity = request.form.get('quantity')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('EXEC remove_inventory_quantity @GameId = ?, @Quantity = ?', 
                      (game_id, quantity))
        conn.commit()
        flash('Inventory updated successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating inventory: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_game', methods=['POST'])
@login_required
@admin_required
def remove_game():
    game_id = request.form.get('game_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('EXEC remove_game @GameId = ?', (game_id,))
        conn.commit()
        flash('Game removed successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error removing game: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_game', methods=['POST'])
@login_required
@admin_required
def add_game():
    if request.method == 'POST':
        # Handle file upload
        if 'gameImage' not in request.files:
            flash('No image file uploaded', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['gameImage']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        conn = None  # Initialize conn to None
        cursor = None # Initialize cursor to None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename to make it unique
            filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                
                # Get the relative URL for the database
                image_url = f"/static/uploads/games/{filename}"
                
                conn = get_db_connection() # Assign conn here
                cursor = conn.cursor() # Assign cursor here
                
                cursor.execute("""
                    EXEC add_game_item 
                    @AdminId = ?, 
                    @GameTitle = ?, 
                    @Description = ?, 
                    @Genre = ?, 
                    @Price = ?, 
                    @Platform = ?,
                    @ImageURL = ?
                """, (
                    session['user_id'],
                    request.form['gameTitle'],
                    request.form['description'],
                    request.form['genre'],
                    request.form['price'],
                    request.form['platform'],
                    image_url
                ))
                conn.commit()
                flash('Game added successfully', 'success')
            except Exception as e:
                flash(f'Error adding game: {str(e)}', 'danger')
                if conn:
                    conn.rollback()
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
        else:
            flash('Invalid file type. Allowed types: png, jpg, jpeg, gif', 'danger')
            
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_user', methods=['POST'])
@login_required
@admin_required
def remove_user():
    user_id = request.form.get('user_id')
    admin_id = session.get('user_id')
    admin_password = 'admin123'  # Update this if you store admin password securely

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'EXEC remove_user @AdminId = ?, @AdminPassword = ?, @UserIdToRemove = ?',
            (admin_id, admin_password, user_id)
        )
        conn.commit()
        flash('User removed successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error removing user: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_inventory', methods=['POST'])
@login_required
@admin_required
def add_inventory():
    game_id = request.form.get('game_id')
    quantity = request.form.get('quantity')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('EXEC add_inventory_quantity @GameId = ?, @Quantity = ?', 
                      (game_id, quantity))
        conn.commit()
        flash('Inventory added successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error adding inventory: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get order details
    cursor.execute('''
        SELECT o.OrderId, o.OrderDate, o.OrderTime, o.TotalAmount, o.Status, p.PaymentStatus, p.PaymentMethod
        FROM Orders o
        JOIN Payments p ON o.OrderId = p.OrderId
        WHERE o.OrderId = ? AND o.UserId = ?
    ''', (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    
    # Process the OrderTime to ensure it's formatted properly
    formatted_time = None
    if order.OrderTime:
        try:
            # Handle different time formats
            time_str = str(order.OrderTime)
            
            # If it's already a datetime.time object
            if hasattr(order.OrderTime, 'strftime'):
                formatted_time = order.OrderTime
            # If it's a string representation
            elif ':' in time_str:
                if '.' in time_str:  # Has microseconds
                    formatted_time = datetime.strptime(time_str.split('.')[0], '%H:%M:%S').time()
                elif len(time_str.split(':')) == 3:  # HH:MM:SS format
                    formatted_time = datetime.strptime(time_str, '%H:%M:%S').time()
                else:  # HH:MM format
                    formatted_time = datetime.strptime(time_str, '%H:%M').time()
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error formatting time: {e}")
            formatted_time = None
            
    # Replace the original OrderTime with our formatted version
    order.OrderTime = formatted_time
    
    # Get order items
    cursor.execute('''
        SELECT g.GameTitle, g.Price, c.Quantity, g.Price * c.Quantity AS TotalAmount
        FROM Cart c
        JOIN Games g ON c.GameId = g.GameId
        WHERE c.OrderId = ?
    ''', (order_id,))
    order_items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('order_details.html', order=order, order_items=order_items)

@app.route('/update_order_status', methods=['POST'])
@login_required
@admin_required
def update_order_status():
    order_id = request.form.get('order_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update order status
        cursor.execute('''
            UPDATE Orders 
            SET Status = ? 
            WHERE OrderId = ?
        ''', (new_status, order_id))
        
        # If status is Delivered, update payment status to Paid
        if new_status == 'Delivered':
            cursor.execute('''
                UPDATE Payments 
                SET PaymentStatus = 'Paid' 
                WHERE OrderId = ?
            ''', (order_id,))
        
        conn.commit()
        flash(f'Order #{order_id} status has been updated to {new_status}', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating order status: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/confirm_order', methods=['POST'])
@login_required
@admin_required
def confirm_order():
    order_id = request.form.get('order_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update order status to Processing and payment status to Paid
        cursor.execute('''
            UPDATE Orders 
            SET Status = 'Processing' 
            WHERE OrderId = ?
        ''', (order_id,))
        
        cursor.execute('''
            UPDATE Payments 
            SET PaymentStatus = 'Paid' 
            WHERE OrderId = ?
        ''', (order_id,))
        
        conn.commit()
        flash(f'Order #{order_id} has been confirmed and marked as paid', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error confirming order: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/cancel_order', methods=['POST'])
@login_required
@admin_required
def cancel_order():
    order_id = request.form.get('order_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update order status to Cancelled
        cursor.execute('''
            UPDATE Orders 
            SET Status = 'Cancelled' 
            WHERE OrderId = ?
        ''', (order_id,))
        
        conn.commit()
        flash(f'Order #{order_id} has been cancelled', 'warning')
    except Exception as e:
        conn.rollback()
        flash(f'Error cancelling order: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_order', methods=['POST'])
@login_required
@admin_required
def delete_order():
    order_id = request.form.get('order_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete related payment first due to FK constraint
        cursor.execute('DELETE FROM Payments WHERE OrderId = ?', (order_id,))
        # Delete related cart items
        cursor.execute('DELETE FROM Cart WHERE OrderId = ?', (order_id,))
        # Delete the order itself
        cursor.execute('DELETE FROM Orders WHERE OrderId = ?', (order_id,))
        conn.commit()
        flash('Order deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting order: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
