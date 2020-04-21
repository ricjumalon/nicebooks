import os
import hashlib
import json
import datetime

from flask import Flask, session, render_template, request, url_for, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from pip._vendor import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=['POST','GET'])
def login():

    #redirect to home if user is already logged-in
    if session.get('logged_in') == True:
        return redirect(url_for('home'))

    #message to be display after login
    result_msg = None

    #check if form is submitted
    if request.method == 'POST':
        
        #get user login info
        username = request.form.get("username")
        password = request.form.get("password")

        #check if form is complete
        if username == '' or password == '':
            result_msg = "Please complete the fields!"
            return render_template('index.html', result_msg = result_msg)

        #hash the password using haslib module
        t_hashed = hashlib.sha3_512(password.encode())
        #convert the sequence of bytes returned by hashlib() into hex data
        t_password = t_hashed.hexdigest()

        #check if user exist
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": t_password}).fetchone()
        if user is None:
            #login failed
            result_msg = "Login failed: Wrong username/password!"
            return render_template('index.html', result_msg = result_msg)

        else:
            #login success
            #set sessions data
            session['logged_in'] = True
            session['username'] = user.username
            session['user_id'] = user.id
            return redirect(url_for('home'))
            
    else:
        #else display login page
        return render_template('index.html')


@app.route("/register", methods=['POST','GET'])
def register():
    
    #redirect to home if user is already logged-in
    if session.get('logged_in') == True:
        return redirect(url_for('home'))
    
    #message to be display after registration
    result_msg = None
    
    #check if form is submitted through POST method
    if request.method == 'POST':

        #get user info
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")

        #check if fields are not empty
        if name == '' or username == '' or password == '':
            result_msg = "Please complete the fields!"
            return render_template('register.html', result_msg = result_msg)

        #hash the password using haslib module
        t_hashed = hashlib.sha3_512(password.encode())
        #convert the sequence of bytes returned by hashlib() into hex data
        t_password = t_hashed.hexdigest()

        #check if username is available
        if db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).rowcount == 0:
            
            #insert data into database
            db.execute("INSERT INTO users (name, username, password) VALUES (:name, :username, :password)", {"name": name, "username": username, "password": t_password})
            
            #commit changes
            db.commit()

            result_msg = "Account created successfuly!"
            #return render_template('reg-success.html')

        else:
            result_msg = "Error: Username "+ username +" is already used by other users!"
            #display error message
            #return render_template('reg-error.html')
        return render_template('register.html', result_msg = result_msg)

    else:
        return render_template('register.html', result_msg = result_msg)

@app.route("/home", methods=['POST','GET'])
def home():
    
    #redirect to login page if user is not logged-in
    if session.get('logged_in') is None:
        return redirect(url_for('login'))
    
    #get username session
    user = session.get('username')

    #check if the search form is submitted
    if request.method == 'POST':

        search_text = request.form.get("book_search")
        
        books = db.execute("SELECT id, title, author, isbn FROM books WHERE title ILIKE :search_text OR author ILIKE :search_text OR isbn ILIKE :search_text",{"search_text": f"%{search_text}%"}).fetchall()
        if books is None:
            flash("Book not found!")
            return render_template('books.html')

        else:
            flash(search_text)
            return render_template('books.html', books=books)

    return render_template('home.html')

@app.route("/books/book_info/<int:book_id>")
def book_info(book_id):

    #redirect to login page if user is not logged-in
    if session.get('logged_in') is None:
        return redirect(url_for('login'))
    
    has_reviewed = False;
    
    #Make sure book exist
    book = db.execute("SELECT * FROM books WHERE id = :id",{"id": book_id}).fetchone()
    if book is None:
        result_msg = "Sorry, we can't find the book you're looking for!"
        return render_template("book.html", result_msg = result_msg)

    else:
        #get reviews from users
        reviews = db.execute("SELECT users.name, reviews.rating, reviews.user_opinion, TO_CHAR(reviews.date_time, 'Mon dd, yyyy') as date_time FROM users RIGHT JOIN reviews ON users.id = reviews.user_id WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

        #check if user has already submitted review about the book
        if db.execute("SELECT id FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": session['user_id'], "book_id": book_id}).rowcount != 0:
            has_reviewed = True;
            
        #try to request data from goodreads api if available or connected to the internet
        try:
            #get book review data from goodreads api via json using the isbn
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "zGsh7G5dOXmEP6NOfvGGA", "isbns": book.isbn}).json()
            data = json.dumps(res)
            data = json.loads(data)

            #get rating count and average from the jsondata
            r_count = data['books'][0]['work_ratings_count']
            r_ave = data['books'][0]['average_rating']
            return render_template('book.html', book = book, r_count = r_count, r_ave= r_ave, reviews = reviews, has_reviewed=has_reviewed)
        except:
            return render_template('book.html', book = book, reviews = reviews, has_reviewed=has_reviewed)

    return redirect(url_for('home'))


@app.route("/add_review", methods=['POST','GET'])
def add_review():
    
    if request.method == 'POST':
        
        book_id = request.form.get('book_id')
        rating = request.form.get('star')
        
        #check if rating is valid (number) not a string
        try:
            valrating = int(rating)
            #check if rating is more than 5 or less than 1
            if 5 < valrating < 1:
                result_msg = "Please select a rating from 1 - 5 only"
                return redirect(url_for("book.html", result_msg = result_msg))
        except ValueError:
            result_msg = "Please enter a valid rating number : 1 - 5"
            return redirect(url_for("book.html", result_msg = result_msg))

        user_opinion = request.form.get('rating_text')

        #Make sure book exist
        result = db.execute("SELECT id FROM books WHERE id = :id",{"id": book_id}).fetchone()
        if result is None:
            result_msg = "Sorry, we can't find the book you're looking for!"
            return redirect(url_for("book.html", result_msg = result_msg))
        
        else:
            #check if the user has already submitted review about the book
            if db.execute("SELECT id FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": session['user_id'], "book_id": book_id}).rowcount == 0:
                
                date_now = datetime.datetime.now()

                #add review
                db.execute("INSERT INTO reviews (user_id, book_id, rating, user_opinion, date_time) VALUES (:user_id, :book_id, :rating, :user_opinion, :date_time)", {"user_id": session['user_id'], "book_id": book_id, "rating": rating, "user_opinion": user_opinion, "date_time": date_now})

                

                db.commit()
                return redirect(url_for('book_info',book_id=book_id))
            else:
                result_msg = "You can only submit 1 review in each book"
                return redirect(url_for("book.html", result_msg = result_msg))
            return redirect(url_for('book_info', book_id=book_id))

    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    
    #clear sessions
    session.clear()
    return redirect(url_for('login'))