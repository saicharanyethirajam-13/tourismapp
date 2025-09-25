from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Get DB URL from environment (Render will provide it)
database_url = os.environ.get("DATABASE_URL", "postgresql://tourism_db_om3h_user:DyXP7CqoUNBWqJCq0j1vuFKq1kce4kqQ@dpg-d3ar6r0dl3ps738stdl0-a/tourism_db_om3h")

# Render sometimes gives 'postgres://' instead of 'postgresql://'
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Database Setup ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'instance')
DATABASE = os.path.join(DATABASE_DIR, 'tourism.db')
os.makedirs(DATABASE_DIR, exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db:
        db.close()

# --- General Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        subject = request.form['subject'].strip()
        message = request.form['message'].strip()

        if not name or not email or not subject or not message:
            flash("All fields are required.", "error")
            return redirect(url_for('contact'))

        db = get_db()
        db.execute("""
            INSERT INTO feedback (name, user_email, subject, message, submitted_on)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, subject, message, datetime.now()))
        db.commit()

        flash("Thank you for your feedback!", "success")
        return redirect(url_for('contact'))
    return render_template('contact_us.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))



# --- User Auth ---
@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if not name or not email or not password:
            flash("All fields are required", "error")
            return redirect(url_for('user_register'))

        db = get_db()
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash("Email already registered", "error")
            return redirect(url_for('user_register'))

        db.execute("""
            INSERT INTO users (name, email, password, role, registration_date)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, generate_password_hash(password), 'user', datetime.now().date()))
        db.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('user_register.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if not user:
            flash("❌ Email does not exist.", "error")
            return redirect(url_for('user_login'))

        if not check_password_hash(user['password'], password):
            flash("❌ Incorrect password.", "error")
            return redirect(url_for('user_login'))

        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']

        flash("✅ Logged in successfully!", "success")

        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('main_dashboard'))
    return render_template('user_login.html')

@app.route('/feedback_reports')
def feedback_reports():
    return redirect(url_for('view_feedback'))

@app.route('/admin_payments')
def admin_payments():
    return redirect(url_for('admin_packages'))

@app.route('/edit_admin_profile')
def edit_admin_profile():
    return redirect(url_for('admin_profile'))

@app.route('/login')
def login_alias():
    return redirect(url_for('user_login'))

# --- User Routes ---
@app.route('/main_dashboard')
def main_dashboard():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template('main_dashboard.html')

@app.route('/explore')
def explore_packages():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    db = get_db()
    packages = db.execute("SELECT * FROM packages").fetchall()
    return render_template('explore_packages.html', packages=packages)

@app.route('/book/<int:package_id>')
def book_package(package_id):
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("INSERT INTO bookings (user_id, package_id, booked_on) VALUES (?, ?, ?)",
               (session['user_id'], package_id, datetime.now()))
    db.commit()
    flash("Package booked!", "success")
    return redirect(url_for('my_bookings'))

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))

    db = get_db()
    bookings = db.execute("""
        SELECT b.booked_on, p.title, p.description, p.price, p.image_url
        FROM bookings b
        JOIN packages p ON b.package_id = p.id
        WHERE b.user_id = ?
        ORDER BY b.booked_on DESC
    """, (session['user_id'],)).fetchall()

    return render_template('my_bookings.html', bookings=bookings)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute("""
        UPDATE users SET name=?, email=?, phone=?, location=? WHERE id=?""",
        (request.form['name'], request.form['email'], request.form['phone'],
         request.form['location'], session['user_id']))
    db.commit()
    flash("Profile updated!", "success")
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if request.method == 'POST':
        current = request.form['current_password']
        new = request.form['new_password']
        confirm = request.form['confirm_password']

        if not check_password_hash(user['password'], current):
            flash("Current password incorrect", "error")
            return redirect(url_for('change_password'))
        if new != confirm:
            flash("New passwords do not match", "error")
            return redirect(url_for('change_password'))

        db.execute("UPDATE users SET password = ? WHERE id = ?",
                   (generate_password_hash(new), session['user_id']))
        db.commit()
        flash("Password changed!", "success")
        return redirect(url_for('profile'))
    return render_template('change_password.html')

# --- Admin Section ---
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
def view_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    users = db.execute("SELECT id, name, email, phone, location, registration_date FROM users").fetchall()
    return render_template('user_list.html', users=users)

@app.route('/admin/feedback')
def view_feedback():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    feedbacks = db.execute("SELECT * FROM feedback ORDER BY submitted_on DESC").fetchall()
    return render_template('feedback_reports.html', feedbacks=feedbacks)

@app.route('/admin/bookings')
def all_bookings():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    bookings = db.execute("""
        SELECT b.id, b.booked_on, u.name AS user_name, u.email, 
               p.title AS package_title, p.price
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN packages p ON b.package_id = p.id
        ORDER BY b.booked_on DESC
    """).fetchall()
    return render_template('all_bookings.html', bookings=bookings)

@app.route('/admin/packages')
def admin_packages():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    packages = db.execute("SELECT * FROM packages").fetchall()
    return render_template('manage_packages.html', packages=packages)


@app.route('/admin/package/add', methods=['GET', 'POST'])
def add_package():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        destination = request.form['destination']
        price = request.form['price']
        duration = request.form['duration']
        description = request.form['description']
        status = request.form['status']
        db = get_db()
        db.execute("""
            INSERT INTO packages (title, destination, price, duration, description, status)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (title, destination, price, duration, description, status))
        db.commit()
        flash("Package added successfully!", "success")
        return redirect(url_for('admin_packages'))
    return render_template('add_package.html')


@app.route('/admin/package/edit/<int:package_id>', methods=['GET', 'POST'])
def edit_package(package_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    package = db.execute("SELECT * FROM packages WHERE id = ?", (package_id,)).fetchone()
    if not package:
        flash("Package not found.", "error")
        return redirect(url_for('admin_packages'))

    if request.method == 'POST':
        title = request.form['title']
        destination = request.form['destination']
        price = request.form['price']
        duration = request.form['duration']
        description = request.form['description']
        status = request.form['status']
        db.execute("""
            UPDATE packages SET title=?, destination=?, price=?, duration=?, description=?, status=?
            WHERE id=?""",
            (title, destination, price, duration, description, status, package_id))
        db.commit()
        flash("Package updated successfully!", "success")
        return redirect(url_for('admin_packages'))

    return render_template('edit_package.html', package=package)
@app.route('/admin/package/delete/<int:package_id>', methods=['POST'])
def delete_package(package_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("DELETE FROM packages WHERE id = ?", (package_id,))
    db.commit()
    flash("Package deleted.", "info")
    return redirect(url_for('admin_packages'))



@app.route('/admin/profile')
def admin_profile():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    db = get_db()
    admin = db.execute("SELECT * FROM admin WHERE id = ?", (session['admin_id'],)).fetchone()

    total_packages = db.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
    total_bookings = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    total_feedbacks = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

    stats = {
        'total_packages': total_packages,
        'total_bookings': total_bookings,
        'total_feedbacks': total_feedbacks
    }

    return render_template('admin_profile.html', admin=admin, stats=stats)

# --- Admin Auth ---
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if not name or not email or not password or not confirm:
            flash("All fields required", "error")
            return redirect(url_for('admin_register'))
        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for('admin_register'))

        db = get_db()
        if db.execute("SELECT id FROM admin WHERE email = ?", (email,)).fetchone():
            flash("Email already registered", "error")
            return redirect(url_for('admin_register'))

        db.execute("INSERT INTO admin (name, email, password) VALUES (?, ?, ?)",
                   (name, email, generate_password_hash(password)))
        db.commit()
        flash("Admin registered!", "success")
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        db = get_db()
        admin = db.execute("SELECT * FROM admin WHERE email = ?", (email,)).fetchone()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['email'] = admin['email']
            session['role'] = 'admin'
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        flash("Invalid credentials", "error")
    return render_template('admin_login.html')


# --- Error Handling ---
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# --- App Entry ---
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
