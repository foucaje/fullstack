import os
import webapp2
import jinja2
import re
import hmac

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

salt = 'Ad7Cd3smGf15p32z'


def hash(value):
    return hmac.new(salt, str(value)).hexdigest()


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    user = db.ReferenceProperty(User)


class Comment(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    content = db.TextProperty(required=True)
    user = db.ReferenceProperty(User)
    post = db.ReferenceProperty(Post)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        params['user'] = self.user
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.request.cookies.get('uid')
        self.user = self.valid_cookie(str(uid))

        p = Post.all().order('-created').fetch(limit=2)
        self.recentposts = p

    def valid_cookie(self, uid):
            if '|' in uid:
                user_id = uid.split('|')[0]
                user_hash = uid.split('|')[1]

                if user_hash == hash(user_id):
                    u = User.get_by_id(int(user_id))

                    if u:
                        return u

    def login(self, uid, hash_id):
        self.response.headers.add_header('Set-Cookie', 'uid=%s|%s; Path=/'
                                         % (str(uid), hash_id))


class Blog(Handler):
    def get(self):
        posts = Post.all().order('-created')

        if posts:
            self.render('blog.html', posts=posts)
        else:
            self.render('blog.html')


class NewPost(Handler):
    def get(self):
        if self.user:
            self.render('newpost.html')
        else:
            self.redirect('/login')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(content=content, subject=subject,
                     user=self.user)
            pkey = p.put().id()
            self.redirect('/%d' % pkey)

        else:
            error = 'You need to supply both!'
            self.render('newpost.html',
                        error=error,
                        content=content,
                        subject=subject)


class PermaLink(Handler):
    def get(self, post_id):
        delete = self.request.get('delete')
        edit = self.request.get('edit')

        if edit and self.user:
            p = Post.get_by_id(int(post_id))
            if p:
                self.render('edit.html', subject=p.subject,
                            content=p.content)

        elif delete and self.user:
            p = Post.get_by_id(int(post_id))
            if p:
                p.delete()
                self.redirect('/')
        else:
            p = Post.get_by_id(int(post_id))
            self.render('post.html', post=p)

    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content and post_id:
            p = Post.get_by_id(int(post_id))
            if p and p.user.username == self.user.username:
                p.content = content
                p.subject = subject
                p.put()

            self.redirect('/')

        else:
            error = 'You need to supply both!'
            self.render('edit.html', error=error,
                        content=content,
                        subject=subject)


class SignUp(Handler):
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

        if not username or not USER_RE.match(username):
            USER_ERR = 'That is not a valid username!'
        if not password or not PASS_RE.match(password):
            PASS_ERR = 'That is not a valid password!'
        if not verify or (verify != password):
            VERIFY_ERR = 'The Passwords do not match!'
        if email and not MAIL_RE.match(email):
            EMAIL_ERR = 'The email is not valid!'

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
    def get(self):
        if self.user:
            self.render('welcome.html')
        else:
            self.redirect('/signup')


class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password:
            pwdHash = hash(password)
            user = db.GqlQuery("SELECT * FROM User WHERE username = '%s' "
                               "and password = '%s'"
                               % (str(username), pwdHash)).get()

            if user:
                uid = user.key().id()
                self.login(uid, hash(uid))
                self.redirect('/welcome')
            else:
                self.render('login.html', ERROR='Login Invalid!')

        else:
            self.render('login.html', ERROR='Login Invalid!')


class Logout(Handler):
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
