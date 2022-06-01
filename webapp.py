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
from bson.objectid import ObjectId
# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = False #Change this to False for production
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

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
messages = db['messages']

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates

#call this function whenever you need to display the posts on a page.

def admin():
    admin = False
    if session['user_data']['login'] == "AntonioADevelops" or "sanchez-christian":
        admin = True
    return admin  

def get_posts():
    posts = messages.find({})
    formatted_posts=""
    for post in posts:
        ObjID = str(post['_id'])
        # formatted_posts = formatted_posts + Markup("<div class=\"media-border p-3\"><div class=\"posts\"></div><div class=\"card mb-2\"><div class=\"card-body p-2 p-sm-3\"><div class=\"media forum-item\"><form action=\"/thread\"><button class=\"u-icon\"><img src=\"/static/u-icon_placeholder.png\" class=\"mr-3 rounded-circle u-icon\" name=\"reply\" width=\"50\" alt=\"User\"></button></form><div class=\"media-body\"><div class=\"delete_div\"><form action=\"/delete\" method=\"post\"><button class=\"media-heading delete\" type=\"submit\" name=\"delete\" value=\"" + ObjID + "\">&#10005</button></form></div><div class=\"u-name\"><h6><form action=\"/thread\"><button class=\"text-body u-username\" name=\"reply\">" + post["username"] + "</button></form></h6></div><div class=\"u-title\"><p>" + post["post_title"] + "</p></div><div class=\"u-post\"><p>" + post["post_content"] + "</p><form action=\"/thread\"><button class=\"reply\" type=\"submit\" name=\"reply\" value=\"" + ObjID + "\"><img class=\"reply-icon\" src=\"/static/reply.svg\"><p class=\"reply-text\">reply</p></button></div></div></div></div></div></div></div>")
        formatted_posts = formatted_posts + Markup("<div class=\"media-border p-3\"><div class=\"posts\"><div class=\"card mb-2\"><div class=\"card-body p-2 p-sm-3\"><div class=\"media forum-item\"><form action=\"/thread\" method=\"post\"><button class=\"u-icon\" name=\"reply\" value=\"" + ObjID + "\"><img src=\"/static/u-icon_placeholder.png\" class=\"mr-3 rounded-circle\" width=\"50\" alt=\"User\"></button></form><div class=\"media-body\"><div class=\"delete_div\"><form action=\"/delete\" method=\"post\"><button class=\"media-heading delete\" type=\"submit\" name=\"delete\" value=\"" + ObjID + "\">&#10005</button></form></div><div class=\"u-name\"><h6><form action=\"/thread\" method=\"post\"><button class=\"text-body u-username\" name=\"reply\" value=\"" + ObjID + "\">" + post["username"] + "</button></form></h6></div><div class=\"u-title\"><p>" + post["post_title"] + "</p></div><div class=\"u-post\"><p>" + post["post_content"] + "</p><form action=\"/thread\" method=\"post\"><button class=\"reply\" name=\"reply\" value=\"" + ObjID + "\"><img class=\"reply-icon\" src=\"/static/reply.svg\"><p class=\"reply-text\">reply</p></button></form></div></div></div></div></div></div></div>")
    return formatted_posts

def get_replies():
    posts = messages.find({})
    formatted_replies=""
    for post in posts:
        ObjID = str(post['_id'])
        for replies in post['replies']:
            reply_content = replies['reply_content']
            reply_name = replies['reply_name']
            formatted_replies = formatted_replies + Markup("<div class=\"media-border p-3\"><div class=\"media p-3\"><div class=\"media-body\"><div class=\"posts\"><div class=\"card mb-2\"><div class=\"card-body p-2 p-sm-3\"><div class=\"media forum-item\"><img src=\"/static/u-icon_placeholder.png\" class=\"mr-3 rounded-circle u-icon\" width=\"50\" alt=\"User\"><div class=\"media-body\"><div class=\"delete_div\"></div><div class=\"u-name\"><h6><p class=\"text-body u-username\">" + reply_name + "</p></h6></div><div class=\"u-post\"><p>" + reply_content + "</p></div></div></div></div></div></div></div></div></div>")
    return formatted_replies

def get_post_thread():
    postID = ObjectId(request.form['reply'])
    post = messages.find_one({"_id": postID})
    ObjID = str(post['_id'])     
    post_thread = Markup("<div class=\"media-border p-3\"><div class=\"posts\"><div class=\"card mb-2\"><div class=\"card-body p-2 p-sm-3\"><div class=\"media forum-item\"><img src=\"/static/u-icon_placeholder.png\" class=\"mr-3 rounded-circle u-icon\" width=\"50\" alt=\"User\"><div class=\"media-body\"><div class=\"delete_div\"><form action=\"/delete\" method=\"post\"><button class=\"media-heading delete\" type=\"submit\" name=\"delete\" value=\"" + ObjID + "\">&#10005</button></form></div><div class=\"u-name\"><h6><p class=\"text-body u-username\">" + post["username"] + "</p></h6></div><div class=\"u-title\"><p>" + post["post_title"] + "</p></div><div class=\"u-post\"><p>" + post["post_content"] + "</p><form action=\"/thread\" method=\"post\" class=\"reply-field-form\"><input class=\"reply-field\" onfocus=\"this.value=''\" type=\"text\" value=\"Post a reply...\" name=\"ureply\"><button type=\"submit\" class=\"reply\" name=\"reply\" value=\"" + ObjID + "\"><img class=\"reply-icon\" src=\"/static/reply.svg\"><p class=\"reply-text\">reply</p></button></form></div></div></div></div></div></div></div>")
    return post_thread
    
def get_post_thread2():
    postID = ObjectId(request.form['reply'])
    post = messages.find_one({"_id": postID})
    ObjID = str(post['_id'])    
    post_thread = Markup("<div class=\"media-border p-3\"><div class=\"posts\"><div class=\"card mb-2\"><div class=\"card-body p-2 p-sm-3\"><div class=\"media forum-item\"><img src=\"/static/u-icon_placeholder.png\" class=\"mr-3 rounded-circle u-icon\" width=\"50\" alt=\"User\"><div class=\"media-body\"><div class=\"delete_div\"><form action=\"/delete\" method=\"post\"><button class=\"media-heading delete\" type=\"submit\" name=\"delete\" value=\"" + ObjID + "\">&#10005</button></form></div><div class=\"u-name\"><h6><p class=\"text-body u-username\">" + post["username"] + "</p></h6></div><div class=\"u-title\"><p>" + post["post_title"] + "</p></div><div class=\"u-post\"><p>" + post["post_content"] + "</p><form action=\"/thread\" method=\"post\" class=\"reply-field-form\"><input class=\"reply-field\" onfocus=\"this.value=''\" type=\"text\" value=\"Post a reply...\" name=\"ureply\"><button type=\"submit\" class=\"reply\" name=\"reply\" value=\"" + ObjID + "\"><img class=\"reply-icon\" src=\"/static/reply.svg\"><p class=\"reply-text\">reply</p></button></form></div></div></div></div></div></div></div>")
    return post_thread

def add_posts():
    u_post = {'username': session['user_data']['login'],
               'post_title': request.form['title'],
               #'post_time': datetime.datetime.utcnow(),
               'post_content': request.form['post'],
               'replies': []
               }

    messages.insert_one(u_post)
    
def add_replies():     
    postID = ObjectId(request.form['reply'])
    messages.update_one(
        {"_id": postID},
        {"$push": {"replies": {"reply_name":session['user_data']['login'], "reply_content": request.form['ureply']}}}
    )
    
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/', methods=['GET', 'POST'])
def home():
    if "title" in request.form:
        add_posts()
    
    return render_template('home.html', user_posts = get_posts())
    
@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if ('github_token' in session):
        return render_template('posts.html')
    else:
        return redirect(url_for('/'))

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

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

@app.route('/thread', methods=['GET', 'POST'])
def thread():
    F_Reply = Markup('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Fail!</strong> Unable to post reply. Please log in before trying to reply. </div>')
    S_Reply = Markup('<div class="alert alert-success"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Success!</strong> Your reply has been successfully posted. </div>')      
    if request.method == 'POST':
        if 'user_data' not in session and 'ureply' in request.form:
            flash(F_Reply)
            return render_template('thread.html', post_thread = get_post_thread2(), thread_replies = get_replies())
        
        elif 'user_data' in session and 'ureply' in request.form:
            flash(S_Reply)
            add_replies()
            return render_template('thread.html', post_thread = get_post_thread2(), thread_replies = get_replies())
        # elif 'user_data' in session:
        #     add_replies()
        return render_template('thread.html', post_thread = get_post_thread(), thread_replies = get_replies())
                
    if request.method == "GET":
        return redirect('/')


@app.route('/delete', methods=['GET', 'POST'])
def delete_button():
    if request.method == 'POST':
        S_Delete = Markup('<div class="alert alert-success"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Success!</strong> The post has been successfully deleted. </div>')
        F_Delete = Markup('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Fail!</strong> Unable to delete post. Cannot delete other users\' posts. </div>')
        F_Delete2 = Markup('<div class="alert alert-danger"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Fail!</strong> Unable to delete post. Please login to delete a post. </div>')
        posts = messages.find({})
        postID = ObjectId(request.form['delete'])
              
        for post in posts: #scans through all documents in the database   
            if 'user_data' not in session:
                flash(F_Delete2)
                return render_template('home.html', user_posts = get_posts())
            
            elif post['username'] == session['user_data']['login'] or admin() == True:
                if post['_id'] == postID:
                    messages.delete_one(({'_id': postID}))
                    flash(S_Delete)
                    return render_template('home.html', user_posts = get_posts())
                
            elif post['username'] != session['user_data']['login'] or admin() == False:
                flash(F_Delete)
                return render_template('home.html', user_posts = get_posts())   
              
        return render_template('home.html', user_posts = get_posts())
    
    elif request.method == 'GET':
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)