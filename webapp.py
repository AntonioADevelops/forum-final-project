from flask import Flask, redirect, url_for, session, request, flash, jsonify
from flask_oauthlib.client import OAuth
#from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template
from flask import Markup

# from zoneinfo import ZoneInfo
# import datetime #refer to https://stackoverflow.com/questions/40358675/flask-get-local-time
# import gridfs used for retrieving document data 
import pymongo
import pprint
import os

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

from bson.objectid import ObjectId

app = Flask(__name__)

app.debug = False #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]

client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['messages'] #1. put the name of your collection in the quotes

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates

#call this function whenever you need to display the posts on a page.
def get_posts():
    posts = collection.find({})
    formatted_posts=""
    for post in posts:
        formatted_posts = formatted_posts + Markup("<div class=\"row\"><div class=\"col-sm-8\"><div class=\"posts\"><div class=\"u-icons-div\"><img class=\"u-icons\" src=\"/static/u-icon_placeholder.png\"></div><div class=\"u_name\"><p>" + post["username"] + "</p></div><div class=\"u-title\"><p>" + post["post_title"] + "</p></div><form action=\"/\" method=\"POST\"><button type=\"submit\" name=\"delete\" value=" + post['_id'] + ">Delete</button></form><div class=\"u-post\"><p>" + post["post_content"] + "</p><a class=\"reply\"><img class=\"reply-icon\" src=\"/static/reply.svg\"><p class=\"reply-text\">reply</p></a><form action=\"/\" method=\"post\"><input type=\"text\" class=\"reply-field\"></form></div></div></div></div>")   
    return formatted_posts     

def add_posts():
    u_post = {'username': session['user_data']['login'],
               'post_title': request.form['title'],
               #'post_time': datetime.datetime.utcnow(),
               'post_content': request.form['post']}

    collection.insert_one(u_post)
    
def admin():
    admin = False
    if session['user_data']['login'] == "AntonioADevelops" or "sanchez-christian":
        admin = True
    return admin  
    
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/', methods=['GET', 'POST'])
def home():
    if "title" in request.form:
        add_posts()

    # if admin() == True and request.method == 'POST':
    #     collection.delete_one({"_id": "ObjectId"})
    
    return render_template('home.html', user_posts = get_posts())
    
@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if ('github_token' in session):
        return render_template('posts.html')
    else:
        return redirect("/")

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    S_Logout = Markup('<div class="alert alert-info"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Success!</strong> You were logged out</div>')
    flash(S_Logout)
    return render_template('home.html', user_posts = get_posts())

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        B_Login = Markup('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Fail!</strong> Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args) + '</div>')
        flash(B_Login)     
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            S_Login = Markup('<div class="alert alert-success"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Success!</strong> You were logged in as ' + session['user_data']['login'] + '.</div>')
            flash(S_Login)
        except Exception as inst:
            session.clear()
            print(inst)
            F_Login = Markup('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Fail!</strong> Unable to login, please try again.</div>')
            flash(F_Login)
    return render_template('home.html', user_posts = get_posts())

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run(debug=True)