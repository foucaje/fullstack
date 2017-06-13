from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from setup_database import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps
import random
import string
import httplib2
import json
import requests

app = Flask(__name__, static_url_path='', static_folder='static')

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Project"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Decorator to wrap around functions we need to login for
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def render(template, **params):

    if 'username' in login_session:
        params['user'] = login_session['email']
    return render_template(template, **params)

# Create anti-forgery state token
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    return render('login.html', STATE=state)



@app.route('/gCallback', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/userinfo/v2/me"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['email'] = data['email']
   
    # see if user exists, if it doesn't make a new one
    user = getUser(data['email'])
    if not user:
        user = createUser(login_session)

    return redirect(url_for('listCategories'))


def createUser(login_session):
    newUser = User(Name=login_session['username'], Email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(Email=login_session['email']).one()
    return user

def getUser(email):
    try:
        user = session.query(User).filter_by(Email=email).one_or_none()
        return user
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

#A JSON Endpoint to list all items of a given category
@app.route('/catalog/<string:category_name>/JSON')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(Name=category_name).one()
    items = session.query(Item).filter_by(
        Category=category).all()
    return jsonify(Category=category.Name, Items=[i.serialize for i in items])


# Show all categories
@app.route('/')
@app.route('/catalog/')
def listCategories():
    categories = session.query(Category).order_by(asc(Category.Name))
    latestItems = session.query(Item).order_by(Item.Created.desc()).limit(10).all()

    return render('catalog.html', categories=categories, latestItems=latestItems)


#Show a Category
@app.route('/catalog/<string:category_name>')
def showCategory(category_name):
    categories = session.query(Category).order_by(asc(Category.Name))
    category = session.query(Category).filter_by(Name=category_name).one_or_none()

    if category:
        items = session.query(Item).filter_by(Category=category).all()
        return render('catalog.html', categories=categories, active_category=category, items=items)
    else:
        flash('Category %s does not exit!') % category_name
        return redirect(url_for('listCategories'))


#Create a new category
@app.route('/category/add/', methods=['GET', 'POST'])
@login_required
def addCategory():

    if request.method == 'POST':
        name = request.form['name']
        newCategory = session.query(Category).filter_by(Name=name).one_or_none()
        if not newCategory:
            user = session.query(User).filter_by(Email=login_session['email']).one_or_none()
            newCategory = Category(Name=name)
            session.add(newCategory)
            session.commit()
            return redirect(url_for('listCategories'))
        else:
            return render('newCategory.html', name=name, ERROR='This Category already exist!')
    else:
        return render('newCategory.html')

#Add Item
@app.route('/catalog/<string:category_name>/add', methods=['GET', 'POST'])
@login_required
def addItem(category_name):
    
    categories = session.query(Category).order_by(asc(Category.Name))
    category = session.query(Category).filter_by(Name=category_name).one_or_none()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        newItem = session.query(Item).filter_by(Name=name).one_or_none()

        if not newItem:
            user = session.query(User).filter_by(Email=login_session['email']).one_or_none()
            newItem = Item(Name=name, Description=description, Category=category, User=user)
            session.add(newItem)
            session.commit()
            return redirect(url_for('listCategories'))
        else:
            return render('newItem.html', name=name, description=description, ERROR='This Item does already exist!')
    else:
         return render('newItem.html')

#Edit Item
@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods=['GET', 'POST'])
@login_required
def editItem(category_name, item_name):
    category = session.query(Category).filter_by(Name=category_name).one_or_none()
    item = session.query(Item).filter_by(Name=item_name).one_or_none()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        user = session.query(User).filter_by(Email=login_session['email']).one_or_none()

        # If the Item is valid an we are the owner, we can update!
        if item and item.User == user:
            session.query(Item).filter_by(Name=item_name).update({'Name': name, 'Description': description})
            session.commit()
            
        return redirect(url_for('listCategories'))
    else:
         return render('editItem.html', name=item.Name, description=item.Description)
        
#Show Item
@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(category_name, item_name):
    categories = session.query(Category).order_by(asc(Category.Name))
    category = session.query(Category).filter_by(Name=category_name).one_or_none()
    item = session.query(Item).filter_by(Name=item_name).one_or_none()

    if item:
        return render('item.html', item=item, categories=categories, active_category=category)
    else:
        return redirect(url_for('listCategories'))

#Delete Item
@app.route('/catalog/<string:category_name>/<string:item_name>/delete')
@login_required
def deleteItem(category_name, item_name):
    item = session.query(Item).filter_by(Name=item_name).one_or_none()

    if item and item.User.Email == login_session['email']:
        session.delete(item)
        session.commit()
     
    return redirect(url_for('listCategories'))

#Logout
@app.route('/logout')
def logout():
    #Disconnect from Google OAuth2
    gdisconnect()

    #Delete Session variables
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']

    return redirect(url_for('listCategories'))
   


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)