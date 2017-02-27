import os
import webapp2
import jinja2
import hmac
import re
import hashlib

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
	autoescape=True)



class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		params['user'] = self.user
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_cookie(self, cookie_name, cookie_val):
		cookie_val = self.make_crypted_value(cookie_val)

		self.response.headers.add_header('Set-Cookie',
			'%s=%s; Path=/' % (cookie_name, cookie_val))

	def read_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and self.check_crypted_value(cookie_val)

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('uid')
		self.user = User.by_id(int(uid))
	
	def valid_user(self):
		user = self.request.cookies.get("uid")

	def valid_cookie(self, uid):
		user_id = uid.split('|')[0]
		pwd = uid.split('|')[1]
		u = User.get_by_id(int(user_id))

		if u and u.password == pwd:
			return True

	def make_crypted_value(self, val):
		return '%s|%s' % (val, bcrypt.hashpw(val, bcrypt.gensalt()) )

	def check_crypted_value(self, chk_value):
		val = chk_value.split('|')[0]
		if chk_value == self.make_crypted_value(val):
			return val


class Post(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	user_id = db.IntegerProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	modified = db.DateTimeProperty(auto_now = True)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)

	@classmethod
	def get_by_name(cls, name):
		return User.all().filter('name =', name).get()

class MainBlog(Handler):
	def get(self):
		posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
		self.render("blog.html", posts = posts)

class NewPost(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		subject = self.request.get('subject')
		content = self.request.get('content')

		if subject and content:
			p = Post(content = content, subject=subject)
			pkey = p.put().id()
			self.redirect("/%d" % pkey)

		else:
			error = "You need to supply both!"
			self.render("newpost.html", error = error, content = content, subject = subject)

class PermaLink(Handler):
	def get(self, post_id):
		p = Post.get_by_id(int(post_id))
		self.render("post.html", post = p)

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
			USER_ERR = "That is not a valid username!"

		if not password or not PASS_RE.match(password):
			PASS_ERR = "That is not a valid password!"

		if not verify or not (verify == password):
			VERIFY_ERR = "The Passwords do not match!"

		if email and not MAIL_RE.match(email):
			EMAIL_ERR = "The email is not valid!"

		if username:
			u = User.get_by_name(username)
			if u :
				USER_ERR = "Sorry, that username is already taken!"


		if USER_ERR or PASS_ERR or VERIFY_ERR or EMAIL_ERR:
			self.render('signup.html', USER_ERR = USER_ERR, PASS_ERR = PASS_ERR, VERIFY_ERR = VERIFY_ERR, EMAIL_ERR = EMAIL_ERR,
			username = username, email = email)
		else:
			# posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
			pwdHash = hashlib.sha256(password).hexdigest();
			u = User(username = username, password = pwdHash, email = email )
			key = u.put().id();
			self.response.headers.add_header('Set-Cookie', 'uid=%s|%s; Path=/' % (str(key), pwdHash))
			self.redirect('/welcome')

class Welcome(Handler):
	def get(self):
		uid = self.request.cookies.get('uid')
		
		if uid and self.valid_cookie(str(uid)):
			self.render('welcome.html', username = User.get_by_id(int(uid.split('|')[0])).username)
		else:
			self.redirect('/signup')

	def valid_cookie(self, uid):
		user_id = uid.split('|')[0]
		pwd = uid.split('|')[1]
		u = User.get_by_id(int(user_id))

		if u and u.password == pwd:
			return True

class Login(Handler):
	def get(self):
		self.render('login.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		pwdHash = hashlib.sha256(password).hexdigest()

		if username and password:
			q = db.GqlQuery("SELECT * FROM User WHERE username = '%s' and password = '%s'" % (str(username), pwdHash))
			user = q.get()
		
			if user:
				key = user.key().id()
				#self.write(user.username + ", " + str(key))
				self.response.headers.add_header('Set-Cookie', 'uid=%s|%s; Path=/' % (str(key), pwdHash))
				self.redirect('/welcome')
			else:
				self.render('login.html', ERROR = 'Login Invalid!')
			
		else:		
			self.render('login.html', ERROR = 'Login Invalid!')

class Logout(Handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'uid=; Path=/')
		self.redirect('/')

app = webapp2.WSGIApplication([
	('/', MainBlog),
	('/newpost', NewPost),
	('/(\d+)', PermaLink),
	('/signup', SignUp),
	('/welcome', Welcome),
	('/login', Login),
	('/logout', Logout),
], debug=True)