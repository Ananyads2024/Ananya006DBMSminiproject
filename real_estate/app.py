from flask import Flask, render_template, request, redirect
import mysql.connector
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="real_estate"
)
cursor = conn.cursor(dictionary=True)

# Home page route
@app.route('/')
def index():
    cursor.execute("""
        SELECT p.*, 
               ROUND(AVG(r.rating), 1) AS avg_rating,
               MAX(r.comment) AS latest_review
        FROM properties p
        LEFT JOIN reviews r ON p.id = r.property_id
        GROUP BY p.id
    """)
    properties = cursor.fetchall()
    return render_template("index.html", properties=properties)

# Add property route
@app.route('/add', methods=["GET", "POST"])
def add_property():
    if request.method == "POST":
        title = request.form['title']
        location = request.form['location']
        price = request.form['price']
        type_ = request.form['type']
        desc = request.form['description']
        cursor.execute("INSERT INTO properties (title, location, price, type, description) VALUES (%s, %s, %s, %s, %s)",
                       (title, location, price, type_, desc))
        conn.commit()
        return redirect('/')
    return render_template("add_property.html")

# Edit property route
@app.route('/edit/<int:id>', methods=["GET", "POST"])
def edit_property(id):
    if request.method == "POST":
        title = request.form['title']
        location = request.form['location']
        price = request.form['price']
        type_ = request.form['type']
        desc = request.form['description']
        cursor.execute("UPDATE properties SET title=%s, location=%s, price=%s, type=%s, description=%s WHERE id=%s",
                       (title, location, price, type_, desc, id))
        conn.commit()
        return redirect('/')
    cursor.execute("SELECT * FROM properties WHERE id=%s", (id,))
    property = cursor.fetchone()
    return render_template("edit_property.html", property=property)

# Delete property route
@app.route('/delete/<int:id>')
def delete_property(id):
    cursor.execute("DELETE FROM properties WHERE id=%s", (id,))
    conn.commit()
    return redirect('/')

# View/Add reviews route
@app.route('/review/<int:property_id>', methods=["GET", "POST"])
def review_property(property_id):
    if request.method == "POST":
        user_name = request.form['user_name']
        rating = int(request.form['rating'])
        comment = request.form['comment']
        cursor.execute("INSERT INTO reviews (property_id, user_name, rating, comment) VALUES (%s, %s, %s, %s)",
                       (property_id, user_name, rating, comment))
        conn.commit()
        return redirect(f'/review/{property_id}')

    cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
    property = cursor.fetchone()

    cursor.execute("SELECT * FROM reviews WHERE property_id = %s ORDER BY review_date DESC", (property_id,))
    reviews = cursor.fetchall()

    cursor.execute("SELECT AVG(rating) as avg_rating FROM reviews WHERE property_id = %s", (property_id,))
    avg_rating = cursor.fetchone()['avg_rating']

    return render_template("review.html", property=property, reviews=reviews, avg_rating=avg_rating)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already exists")
            return redirect('/register')

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        flash("Registration successful! Please log in.")
        return redirect('/login')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!")
            return redirect('/')
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect('/')

# Start the app
if __name__ == "__main__":
    app.run(debug=True)
