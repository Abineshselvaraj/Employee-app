from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from utils.db import get_db_connection  # Database helper function

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Allowed file extensions for profile picture uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Directory to store uploaded profile pictures
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

# Owner login route
@app.route('/owner_login', methods=['GET', 'POST'])
def owner_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'owner':
                return redirect(url_for('employee_list'))
            else:
                return redirect(url_for('employee_profile'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')  # Same login form for owner login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'owner':
                return redirect(url_for('employee_list'))
            else:
                return redirect(url_for('employee_profile'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Fetch form data
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        dob = request.form['dob']
        address = request.form['address']

        # Handle profile picture upload
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            file_path = None  # Default if no image is uploaded

        # Hash the password for security
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert into users table
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, 'employee')
            )
            conn.commit()

            # Get the ID of the newly created user
            user_id = cursor.lastrowid

            # Insert into employees table
            cursor.execute(
                "INSERT INTO employees (user_id, name, dob, address, profile_pic) VALUES (%s, %s, %s, %s, %s)",
                (user_id, name, dob, address, file_path)
            )
            conn.commit()

            return redirect(url_for('login'))  # Redirect to login after successful signup
        except Exception as e:
            return f"An error occurred: {e}", 500
        finally:
            conn.close()

    return render_template('signup.html')

@app.route('/employee_list')
def employee_list():
    if 'role' not in session or session['role'] != 'owner':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()

    return render_template('employee_list.html', employees=employees)

@app.route('/employee_profile', methods=['GET', 'POST'])
def employee_profile():
    if 'role' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE user_id=%s", (user_id,))
    employee = cursor.fetchone()

    # Handle displaying the profile picture path
    profile_pic = employee['profile_pic'] if employee['profile_pic'] else None

    editable = False  # Default to view mode

    if request.method == 'POST':
        if 'edit' in request.form:  # If the "Edit Profile" button was clicked
            editable = True
            return render_template('employee_profile.html', employee=employee, profile_pic=profile_pic, editable=editable)

        # If the form is submitted to save changes
        name = request.form['name']
        dob = request.form['dob']
        address = request.form['address']

        # Handle new profile picture upload
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            cursor.execute(""" 
                UPDATE employees SET name=%s, dob=%s, address=%s, profile_pic=%s WHERE user_id=%s
            """, (name, dob, address, 'static/uploads/' + filename, user_id))
        else:
            cursor.execute(""" 
                UPDATE employees SET name=%s, dob=%s, address=%s WHERE user_id=%s
            """, (name, dob, address, user_id))

        conn.commit()
        return redirect(url_for('employee_profile'))

    return render_template('employee_profile.html', employee=employee, profile_pic=profile_pic, editable=editable)

# Add logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
