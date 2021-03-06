""" A Multi-User-Blog Module for the Google App Engine

This Module is developed along the Udacity FullStack NanoDegree
by Jerome Foucauld in March 2017

"""
import os
import webapp2
import jinja2
import re
import hmac

from google.appengine.ext import db

# Setting up the Jinja2 template modules
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# A Random string used as salt for hashing
salt = 'Ad7Cd3smGf15p32z'


def hash(value):
    """Hashing function to create hash values
    Argument:
        value: a value to hash

    Returns:
        A hmac hashed string
    """
    return hmac.new(salt, str(value)).hexdigest()


class User(db.Model):
    """ The User DB Model Class
    """
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)


class Post(db.Model):
    """ The Post DB Model Class
    References:
        User
    """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User, collection_name='posts')


class Comment(db.Model):
    """ The Comment DB Model Class
    Comments to a Post

    References:
        User
        Post
    """
    created = db.DateTimeProperty(auto_now_add=True)
    content = db.TextProperty(required=True)
    user = db.ReferenceProperty(User)
    post = db.ReferenceProperty(Post, collection_name='comments')


class Like(db.Model):
    """ The Like DB Model Class
    Likes to a Post
    The Model is called Vote instead of like to avoid
    keyname conflict with SQL databases

    References:
        User Model
        Post Model
    """
    post = db.ReferenceProperty(Post, collection_name='likes')
    user = db.ReferenceProperty(User)


class Handler(webapp2.RequestHandler):
    """ The Parent webapp2 Request Handler
    """
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        params['user'] = self.user
        params['recentposts'] = self.recentposts
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.request.cookies.get('uid')
        self.user = self.valid_cookie(str(uid))

        recentposts = Post.all().order('-created').fetch(limit=5)
        self.recentposts = recentposts

    # This functions validates the cookie data
    def valid_cookie(self, uid):
            if '|' in uid:
                user_id = uid.split('|')[0]
                user_hash = uid.split('|')[1]

                if user_hash == hash(user_id):
                    u = User.get_by_id(int(user_id))

                    return u

    # The login function to write a cookie
    def login(self, uid, hash_id):
        self.response.headers.add_header('Set-Cookie', 'uid=%s|%s; Path=/'
                                         % (str(uid), hash_id))


class Blog(Handler):
    """ The Blog Handler Class
    Handles and renders the "Home" site showing all posts
    """
    def get(self):
        posts = Post.all().order('-created')
        if posts:
            self.render('blog.html', posts=posts)
        else:
            self.render('blog.html')


class NewPost(Handler):
    """ The new Post Handler Class
    Handles and renders the new post page
    """
    def get(self):
        if self.user:
            self.render('newpost.html')
        else:
            self.redirect('/login')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        # Checking if content and subject (required) are available
        if self.user:
            if subject and content:
                p = Post(content=content, subject=subject,
                         user=self.user).put()
                pkey = p.id()
                self.redirect('/%d' % pkey)

            else:
                error = 'You need to supply both!'
                self.render('newpost.html',
                            error=error,
                            content=content,
                            subject=subject)
        else:
            self.redirect('/login')


class PermaLink(Handler):
    """ The Permalink Handler Class
    Handles and renders the a single post according the provided post_id
    In addition, it handels likes and comments related to it
    """
    def get(self, post_id):
        delete = self.request.get('delete')
        edit = self.request.get('edit')
        like = self.request.get('like')
        comment_id = self.request.get('comment_id')

        p = Post.get_by_id(int(post_id))
        c = None

        if comment_id:
            c = Comment.get_by_id(int(comment_id))

        if self.user:

            # Checking we can delete this post
            if delete and delete == 'post':
                if p and p.user.key() == self.user.key():
                    p.delete()
                    self.redirect('/')
                else:
                    self.render('post.html', post=p,
                                error="You can only delete your own post")

            # Checking we can delete this comment
            elif delete and delete == 'comment' and comment_id:
                if c and c.user.key() == self.user.key():
                    c.delete()
                    self.render('post.html', post=p,
                                success='Successfully deleted!')
                else:
                    self.render('post.html', post=p,
                                error="You can only delete your own comment")

            # Checking we can edit this post
            elif edit and edit == 'post':
                if p and p.user.key() == self.user.key():
                    self.render('edit.html', subject=p.subject,
                                content=p.content, post_id=post_id)
                else:
                    self.render('post.html', post=p,
                                error="You can only edit your own post")

            # Checking we can edit this comment
            elif edit and edit == 'comment' and comment_id:
                if c and c.user.key() == self.user.key():
                    upd_com = c.content
                    self.render('post.html', post=p, comment_id=comment_id,
                                upd_com=upd_com)
                else:
                    self.render('post.html', post=p,
                                error="You can only edit your own comment")

            # Checking if we can like this post
            elif like:
                if p and p.user.key() != self.user.key():
                    result = Like.all().filter(
                        'post =', p.key()).filter(
                        'user =', self.user.key()
                        ).get()

                    if result:
                        self.redirect('/')
                    else:
                        Like(post=p, user=self.user).put()
                        self.redirect('/')
                else:
                    self.redirect('/')

            # None of the above handled, so just show the direct link
            self.render('post.html', post=p)

        else:
            self.render('post.html', post=p)

    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')
        comment = self.request.get('comment')
        upd_com = self.request.get('upd_com')
        upd_com_id = self.request.get('upd_com_id')

        p = Post.get_by_id(int(post_id))

        # Updating the Post after edit, if the logged in user is also author
        if subject and content and p and self.user:
            if p.user.key() == self.user.key():
                p.content = content
                p.subject = subject
                p.put()
                self.render('post.html', post=p,
                            success='Successfully updated!')

        # Adding a new comment
        elif p and comment and self.user:
            new = Comment(content=comment, user=self.user, post=p)
            new.put()
            self.render('post.html', post=p)

        # Editing a comment
        elif upd_com and upd_com_id and self.user:
            update = Comment.get_by_id(int(upd_com_id))
            if update.author.key() == self.user.key():
                update.content = upd_com
                update.put()
                self.render('post.html', post=p,
                            success='Successfully updated!')

        else:
            error = 'I am sorry, there was an error with your request'
            self.render('edit.html', error=error,
                        content=content,
                        subject=subject)


class SignUp(Handler):
    """ The SignUp Handler Class
    Handles and renders the new user Signup page
    """
    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        PASS_RE = re.compile(r"^.{3,20}$")
        MAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
        USER_ERR = PASS_ERR = VERIFY_ERR = EMAIL_ERR = ""

        # Checking if the supplied values are valid
        if not username or not USER_RE.match(username):
            USER_ERR = 'The username you have entered is invalid!'
        if not password or not PASS_RE.match(password):
            PASS_ERR = 'The password you have entered is invalid!'
        if not verify or (verify != password):
            VERIFY_ERR = 'The passwords do not match!'
        if email and not MAIL_RE.match(email):
            EMAIL_ERR = 'The email you have entered is not valid!'

        # Checking for duplicate usernames
        if username:
            u = User.all().filter('username =', username).get()
            if u:
                USER_ERR = "Sorry, that user already exist"

        if USER_ERR or PASS_ERR or VERIFY_ERR or EMAIL_ERR:
            self.render('signup.html',
                        USER_ERR=USER_ERR,
                        PASS_ERR=PASS_ERR,
                        VERIFY_ERR=VERIFY_ERR,
                        EMAIL_ERR=EMAIL_ERR,
                        username=username,
                        email=email)
        else:
            pwdHash = hash(password)
            user = User(username=username, password=pwdHash, email=email)
            user.put()
            uid = user.key().id()
            self.login(uid, hash(uid))
            self.redirect('/welcome')


class Welcome(Handler):
    """ The welcome Handler Class
    Handles and renders the welcome page after login or signup
    """
    def get(self):
        if self.user:
            self.render('welcome.html')
        else:
            self.redirect('/signup')


class Login(Handler):
    """ The login Handler Class
    Handles and renders the login page
    """
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            pwdHash = hash(password)
            user = User.all().filter('username = ', str(username)).filter(
                                     'password =', pwdHash).get()

            if user:
                uid = user.key().id()
                self.login(uid, hash(uid))
                self.redirect('/welcome')
            else:
                self.render('login.html', ERROR='Login Invalid!')

        else:
            self.render('login.html', ERROR='Login Invalid!')


class Logout(Handler):
    """ The logout Handler Class
    Handles the user logout by clearing the cookie
    """
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'uid=; Path=/')
        self.redirect('/')


app = webapp2.WSGIApplication([
                               ('/', Blog),
                               ('/newpost', NewPost),
                               ('/(\d+)', PermaLink),
                               ('/signup', SignUp),
                               ('/welcome', Welcome),
                               ('/login', Login),
                               ('/logout', Logout)
                              ], debug=True)
