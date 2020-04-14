import os
import hashlib

from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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

    #check if the user is already logged-in
    if session.get('logged_in') == True:
        #display books page
        return redirect(url_for('books'))

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
            return render_template('index.html', result_msg = session['username'])
            
    else:
        #else display login page
        return render_template('index.html')


@app.route("/register", methods=['POST','GET'])
def register():
    #check session if user is already logged-in
    if session.get('logged_in') == True:
        #display books page
        return redirect(url_for('books'))
    
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

@app.route("/books")
def books():

    #check session if user is already logged-in
    if session.get('logged_in') is None:
        #display books page
        return redirect(url_for('login'))
    user = session.get('username')
    return render_template('books.html', user = user)
