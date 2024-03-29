import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from app import app
from app.forms import LoginForm, RegisterForm, FormOne, FormZero, FormTwo
from flask import render_template, session, request, redirect, url_for, flash, jsonify
from os import getenv
from pymongo import MongoClient
from matchalgo import match, stats
from dotenv import load_dotenv
load_dotenv()
from flask_socketio import SocketIO
socketio = SocketIO(app)

myclient = MongoClient(getenv("MONGO_URI"))
mydb = myclient["diversify"]

def assignSession(username):
    session["username"] = username

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form=LoginForm()
    if form.validate_on_submit():
        user = mydb.users.find_one({'username': form.username.data})
        if user and user['password'] == form.password.data:
            assignSession(user['username'])
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
        assignSession(form.username.data)
    return render_template("signin.html", form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form=RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirmPassword = form.confirmPassword.data
        if password != confirmPassword:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        if mydb.users.find_one({'username': username}):
            flash('Username already taken')
            return redirect(url_for('signup'))
        mydb.users.insert_one({"username": username, "email": email, "password": password, "name": "", "age": "", "country": "", "occupation": "",  "interests":"", "sports": "", "songs": "","languages": "", "food": "","gender": "", "ethnicity": "", "class": "", "university": "", "complete": ""})
        assignSession(username)
        return redirect(url_for('dashboard'))
    return render_template("signup.html", form=form)

@app.route("/dashboard")
def dashboard():
    if not 'username' in session:
        return redirect(url_for('signin'))
    user = mydb.users.find_one({'username': session['username']})
    if user['complete'] != 'true':
        return redirect(url_for('startform'))
    else:
        users = mydb.users.find( { "username": { "$ne" : session['username'] }} )
        user_array = [user for user in users]
        me = mydb.users.find_one({'username': session['username']});
        scores = match(me, user_array)
    return render_template("dashboard.html", session=session, scores=scores)

@app.route("/form/start")
def startform():
    return render_template("startform.html", session=session)

@app.route("/form/0", methods=['GET', 'POST'])
def formzero():
    form=FormZero()
    if form.validate_on_submit():
        name = form.name.data
        age = form.age.data
        country = form.country.data
        occupation = form.occupation.data
        mydb.users.update_one({"username": session['username']}, { "$set" : {"name": name, "age": age, "country": country, "occupation": occupation}})
        return redirect(url_for('formone'))
    return render_template("formzero.html", form=form, session=session)

@app.route("/form/1", methods=['GET', 'POST'])
def formone():
    form=FormOne()
    if form.validate_on_submit():
        interests = form.interests.data
        sports = form.sports.data
        songs = form.songs.data
        languages = form.languages.data
        food = form.food.data
        mydb.users.update_one({"username": session['username']},{"$set": {"interests": interests, "sports": sports, "songs": songs, "languages": languages, "food": food}})
        return redirect(url_for('formtwo'))
    return render_template("formone.html", session=session, form=form)

@app.route("/form/2", methods=['GET', 'POST'])
def formtwo():
    form=FormTwo()
    if form.validate_on_submit():
        gender = form.gender.data
        ethnicity = form.ethnicity.data
        social = form.social.data
        university = form.university.data
        mydb.users.update_one({"username": session['username']},{"$set" :{"gender": gender, "ethnicity": ethnicity, "class": social, "university": university, "complete": "true"}})
        session["formComplete"] = True
        return redirect(url_for('dashboard'))
    return render_template("formtwo.html", session=session, form=form)

@app.route("/mystats")
def mystats():
    users = mydb.users.find( { "username": { "$ne" : session['username'] }} )
    user_array = [user for user in users]
    me = mydb.users.find_one({'username': session['username']});
    scores = match(me, user_array)
    data = stats(me, scores)
    return render_template("data.html", data=data)


@app.route("/chat",methods=['GET', 'POST'])
def sessions():
    if not 'username' in session:
        return redirect(url_for('signin'))
    user = mydb.users.find_one({'username': session['username']})
    if user['complete'] != 'true':
        return redirect(url_for('startform'))
    else:
        users = mydb.users.find( { "username": { "$ne" : session['username'] }} )
        user_array = [user for user in users]
        me = mydb.users.find_one({'username': session['username']});
        scores = match(me, user_array)
    return render_template('session.html',session=session, scores=scores)

def messageReceived(methods=['GET', 'POST']):
    from twilio.rest import Client 
 
    account_sid = 'AC81c745528c0842aac5e2f5f8727ade82' 
    auth_token = 'Redacted' 
    client = Client(account_sid, auth_token) 
    user = mydb.users.find_one({'username': session['username']})
 
    message = client.messages.create(messaging_service_sid='MGc116909a1016558d0670a56e0b08190b',body=f'You got a message from {user}',to='+918210196210')
                         
 
    print(message.sid)
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)