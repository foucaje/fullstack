# Multi User Blog

This is a Multiuser Blog app for the Google App Engine, written in python 2.7.

You can:
  - sign up for a new account
  - post somethnig new, as well as like and comment other users posts

### Tech

The Mult User Blog runs on the Google App Engine.

### Prequisites
A google account is required to make use of the cloud service / sdk.

***Python 2.7x*** is required to run the included python files.
If you do not already have python installed you can download and install directly from: https://www.python.org/downloads/

***jinja2*** is used as template engine, you can check it at the Python Package Index (PyPI) or directly at http://jinja.pocoo.org/.
you can use PIP to install the package by typing
```sh
pip install Jinja2
```
***GOOGLE APP ENGINE SDK***
If you do not already have the SDK installed you can download at https://cloud.google.com/appengine/docs/standard/python/download
Please follow the instructions to properly set up and init the sdk on your machine, important:
```sh
gcloud components install app-engine-python-extras
```

### Configuration
There is nothig much to configure in this version.
However you should have a loot at the blog.py file and edit the salt value for the hashing function.

### GOOGLE APP ENGINE
To deploy on the GAE you need an account at the [GOOGLE APP ENGINE](https://cloud.google.com/appengine/)
Head over to the cloud konsole then create a new project.

***deploy to the cloud***
use the commandline to switch to the project directory on your harddrive
You can deploy to the by typing
```sh
gcloud app deploy
```

***test locally***
use the google app commandline to switch to the project directory on your harddrive
```sh
dev_appserver.py .
```
to run the app server in the current directory


### Todos
 - adding one of the many editors to format a post properly
 - adding a module to better sanitize HTML / JavaScript inputs

 
