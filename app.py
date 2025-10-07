import json
from flask import Flask,flash, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from datetime import datetime
import time

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# MySQL Configuration
mysql_config = {
    'host': 'localhost',
    'database': 'railway_management_system',
    'user': 'root',
    'password': 'root'
}

# Establish MySQL connection
db = mysql.connector.connect(**mysql_config)
cursor = db.cursor()

# Route to login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if role == "admin":
            # Admin login
            query = "SELECT * FROM admin WHERE admin_id = %s AND password = %s"
            cursor.execute(query, (username, password))
            admin = cursor.fetchone()

            if admin:
                session['logged_in'] = True
                session['admin_id'] = username  # Assuming the admin ID is stored in the username field
                return redirect(url_for('index'))  # Redirect to the index page
            else:
                error = "Invalid admin ID or password. Please try again."
                return render_template("login.html", error=error)
        elif role == "user":
            # User login
            query = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('user_dashboard'))
            else:
                error = "Invalid username or password. Please try again."
                return render_template("login.html", error=error)
        else:
            error = "Invalid role selection. Please try again."
            return render_template("login.html", error=error)
    else:
        return render_template("login.html")

# Route to registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Registration logic
        # Insert new user into the database
        username = request.form.get("username")
        password = request.form.get("password")
        address = request.form.get("address")
        age = request.form.get("age")
        email = request.form.get("email")

        # Check if the username already exists
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "Username already exists. Please choose a different username."
            return render_template("register.html", error=error)
        else:
            # Insert new user into the database
            insert_query = "INSERT INTO user (username, password, address, age, email_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (username, password, address, age, email))
            db.commit()
            return redirect(url_for('login'))
    else:
        return render_template("register.html")

# Route to index.html
@app.route("/")
def index():
    # Check if the user is logged in
    if 'logged_in' in session and session['logged_in']:
        if 'admin_id' in session:
            return render_template("index.html")  # Redirect to the admin panel if logged in as admin
        else:
            return render_template("index.html")  # Render the index page if logged in as user
    else:
        # If not logged in, redirect to the login page
        return redirect(url_for('login'))


# Route to handle reservation form submission
@app.route("/reserve", methods=["POST"])
def reserve():
    # Retrieve form data
    username = request.form.get("username")
    
    # Check if the username exists in the User table
    user_query = "SELECT * FROM User WHERE username = %s"
    cursor.execute(user_query, (username,))
    user_exists = cursor.fetchone()

    if not user_exists:
        return "User does not exist. Please enter a valid username."

    # Connect to the database and execute the query to reserve a ticket
    query = "INSERT INTO Ticket (username) VALUES (%s)"
    cursor.execute(query, (username,))
    db.commit()
    
    # Process reservation data
    return "Ticket reserved successfully!"

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if 'logged_in' in session and session['logged_in']:
        if request.method == "POST":
            # Retrieve form data
            train_name = request.form.get("train_name")
            train_no = request.form.get("train_no")
            source = request.form.get("source")
            destination = request.form.get("destination")
            distance = request.form.get("distance")
            arrival_time = request.form.get("arrival_time")
            departure_time = request.form.get("departure_time")
            
            # Check if the train already exists in the database
            cursor.execute("SELECT * FROM train WHERE train_no = %s", (train_no,))
            existing_train = cursor.fetchone()

            if existing_train:
                # Train already exists, flash an error message
                flash("Train already available!", "success")
                return render_template("admin.html")
            else:
                # Connect to the database and execute the query to add train details
                query = "INSERT INTO train (train_name, train_no, source, destination, distance, arrival_time, departure_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (train_name, train_no, source, destination, distance, arrival_time, departure_time))
                db.commit()

                # Pass a message to be displayed
                flash("Train details added successfully!", "success")

            return render_template("index.html")
        else:
            return render_template("admin.html")
    else:
        return redirect(url_for('login'))  # Redirect to the login page if not logged in


# Route to user dashboard
@app.route("/user_dashboard")
def user_dashboard():
    if 'logged_in' in session and session['logged_in']:
        return render_template("user_dashboard.html")
    else:
        return redirect(url_for('login'))


# Route to cancel ticket
@app.route("/cancel_ticket", methods=["GET", "POST"])
def cancel_ticket():
    if request.method == "POST":
        tid = request.form.get("ticket_no")
        # Check if the train ID exists in the database
        cursor.execute("SELECT * FROM ticket WHERE ticket_id = %s", (tid,))
        existing_ticket = cursor.fetchone()

        if existing_ticket:
            # Delete the train from the database
            cursor.execute("DELETE FROM ticket WHERE ticket_id = %s", (tid,))
            db.commit()
            flash("Ticket cancelled successfully", "success")
            
            return render_template("user_dashboard.html")
        else:
            error = "Ticket with ID {} does not exist.".format(tid)
            return render_template("cancel_ticket.html", error=error)

    # Render the cancel_train.html template if the request method is GET
    return render_template("cancel_ticket.html")


# Route to logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route to update train details
@app.route("/update_train", methods=["GET", "POST"])
def update_train():
    if request.method == "POST":
        # Retrieve form data
        train_no = request.form.get("train_no")
        train_name = request.form.get("train_name")
        source = request.form.get("source")
        destination = request.form.get("destination")
        distance = request.form.get("distance")
        arrival_time = request.form.get("arrival_time")
        departure_time = request.form.get("departure_time")
        total_seats = request.form.get("total_seats")
        payment_amount = request.form.get("payment_amount")

        # Update train details in the database
        update_query = "UPDATE train SET train_name = %s, source = %s, destination = %s, distance = %s, arrival_time = %s, departure_time = %s, num_seats = %s, payment = %s WHERE train_no = %s"
        cursor.execute(update_query, (train_name, source, destination, distance, arrival_time, departure_time, total_seats, payment_amount, train_no))
        db.commit()

        # Flash a success message
        flash("Train details updated successfully!", "success")

        # Redirect to the index page after updating train details
        return render_template("index.html")

    # If the method is GET, render the update train form
    return render_template("update_train.html")


@app.route("/cancel_train", methods=["GET", "POST"])
def cancel_train():
    if request.method == "POST":
        train_no = request.form.get("train_no")
        
        # Check if the train ID exists in the database
        cursor.execute("SELECT * FROM train WHERE train_no = %s", (train_no,))
        existing_train = cursor.fetchone()

        if existing_train:
            # Delete the train from the database
            cursor.execute("DELETE FROM train WHERE train_no = %s", (train_no,))
            db.commit()
            message = "Train canceled successfully!"
            flash(message, "success")  # Flash success message
            return render_template("index.html")
        else:
            error = "Train with ID {} does not exist.".format(train_no)
            return render_template("cancel_train.html", error=error)

    # Render the cancel_train.html template if the request method is GET
    return render_template("cancel_train.html")

# Route to check train details
@app.route("/check_train", methods=["GET","POST"])
def check_train():
    if request.method == "POST":
        # Retrieve train number from the form
        train_no = request.form.get("train_no")
        
        # Query the database to check if the train with the given train_no exists
        cursor.execute("SELECT * FROM train WHERE train_no = %s", (train_no,))
        train_details = cursor.fetchone()

        if train_details:
            # Train details found, render train_details.html with the details
            return render_template("train_details.html", train_details=train_details)
        else:
            # Train not found, render an error message
            error = "Train with ID {} does not exist.".format(train_no)
            return render_template("check_train.html", error=error)

    # If the method is not POST, render the check_train.html template
    return render_template("check_train.html")


# Route to display train details
@app.route("/train_details/<int:train_no>")
def display_train_details(train_no):
    # Query the database to retrieve train details based on train number
    cursor.execute("SELECT * FROM train WHERE train_no = %s", (train_no,))
    train_details = cursor.fetchone()

    if train_details:
        # Train details found, render train_details.html with the details
        return render_template("train_details.html", train_details=train_details)
    else:
        # Train not found, render user_dashboard.html with an error message
        error = "Train with ID {} does not exist.".format(train_no)
        return render_template("user_dashboard.html", error=error)

# Route to book ticket
@app.route("/book_ticket")
def book_ticket_page():
    return render_template("book_ticket.html")

# Function to fetch train numbers from the database
@app.route("/get_train_numbers")
def get_train_numbers():
    cursor.execute("SELECT train_no FROM train")
    train_numbers = [row[0] for row in cursor.fetchall()]  # Accessing the first element of each tuple
    return json.dumps(train_numbers)


@app.route("/show_tickets_history")
def show_tickets_history():
    if 'logged_in' in session and session['logged_in']:
        username = session['username']  # Assuming you store the username in the session
        
        # Fetch tickets history for the logged-in user from the database
        cursor.execute("SELECT * FROM ticket WHERE username = %s", (username,))
        tickets = cursor.fetchall()
        
        if tickets:
            return render_template("show_tickets_history.html", tickets=tickets)
        else:
            message = "No tickets found."
            return render_template("show_tickets_history.html", message=message)
    else:
        return render_template("login.html")  # Redirect to the login page if not logged in

# Function to book a train ticket
@app.route("/book_ticket", methods=["POST"])
def book_ticket():
    username = request.form.get("username")
    train_no = request.form.get("train_no")
    ticket_class = request.form.get("class")
    date = request.form.get("date")
    num_seats = int(request.form.get("num_seats"))
    names = request.form.getlist("names[]")
    ages = request.form.getlist("ages[]")

    # Validate input data
    if len(names) != num_seats or len(ages) != num_seats:
        flash("Number of names or ages does not match the number of seats.", "error")
        return redirect(url_for("book_ticket_page"))

    current_date = datetime.now().strftime('%Y-%m-%d')
    if date < current_date:
        flash("Invalid date. Please select a date in the future.", "error")
        return redirect(url_for("book_ticket_page"))

    # Retrieve source and destination from the train table based on train number
    cursor.execute("SELECT source, destination FROM train WHERE train_no = %s", (train_no,))
    train_details = cursor.fetchone()
    if train_details:
        source, destination = train_details
    else:
        flash("Invalid train number. Please select a valid train.", "error")
        return redirect(url_for('show_book_ticket_form'))

    # Insert ticket details into the database
    ticket_ids = []
    for i in range(num_seats):
        # Get the next available seat number
        cursor.execute("SELECT MAX(seat_no) FROM ticket WHERE train_no = %s", (train_no,))
        max_seat = cursor.fetchone()[0]
        next_seat = max_seat + 1 if max_seat else 1
        
        cursor.execute("INSERT INTO ticket (username, train_no, source, destination, class, date, seat_no, name, age) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (username, train_no, source, destination, ticket_class, date, next_seat, names[i], ages[i]))
        db.commit()

        ticket_id = cursor.lastrowid
        ticket_ids.append(ticket_id)

    # Update the num_seats for the train
    cursor.execute("UPDATE train SET num_seats = num_seats - %s WHERE train_no = %s", (num_seats, train_no))
    db.commit()

    flash("Ticket(s) booked successfully! Ticket IDs: {}".format(', '.join(map(str, ticket_ids))), "success")
    return render_template("user_dashboard.html")

@app.route("/show_trains")
def show_trains():
    # Query to fetch all train details from the database
    query = "SELECT * FROM train"
    cursor.execute(query)
    trains = cursor.fetchall()

    return render_template("show_trains.html", trains=trains)





if __name__ == "__main__":
    app.run(debug=True)
