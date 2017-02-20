import os
import webapp2
import jinja2
import codecs
import re

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
	autoescape=True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class MainPage(Handler):
	def get(self):
		self.render('rot13.html')

	def post(self):
		textValue = self.request.get('text')
		if textValue:
			text = codecs.encode(textValue, 'rot_13')
			self.render('rot13.html', textValue = text)
		else:
			self.render('rot13.html')

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
		if not verify or (verify != password):
			VERIFY_ERR = "The Passwords do not match!"
		if email and not MAIL_RE.match(email):
			EMAIL_ERR = "The email is not valid!"

		if USER_ERR or PASS_ERR or VERIFY_ERR or EMAIL_ERR:
			self.render('signup.html', USER_ERR = USER_ERR, PASS_ERR = PASS_ERR, VERIFY_ERR = VERIFY_ERR, EMAIL_ERR = EMAIL_ERR,
			username = username, email = email)
		else:
			self.redirect('/welcome?username=' + username)


class Welcome(Handler):
	def get(self):
		username = self.request.get('username')
		self.render('welcome.html', username = username)

	

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', SignUp),
    ('/welcome', Welcome),
], debug=True)
