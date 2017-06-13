# Simple Catalog App

This app is a simple catalog app where users can add, edit and delete items in different categories. We are using a simple sqlite DB and the flask framework.

### Prequisites
A google account is required as it is used for authorization and authentication.

***Python 2.7x*** is required to run the included python files.
If you do not already have python installed you can download and install directly from: https://www.python.org/downloads/ or use your favorite package manager

***flask*** is used developing the server. For more information check http://flask.pocoo.org/
again you can use your favorite package manager, or use pip
```sh
pip install flask
```

***SQLAlchemy*** is used for the Database management. So you will need to get that too ;-)
```sh
pip install sqlalchemy
```

### GOOGLE oauth2 
Go to https://console.developers.google.com and create a new project.
- go to **credentials** and select **oauth consent screen** fill the form and save
- while still on the **credentials** page click **credentials** and *Add Credentials* select  **OAuth 2.0 client ID**
- next choose **web application** and fill the form, set **Authorized Javascript origins** to your webserver root and dont forget the port. for example http://localhost:5000
- now also set the **Authorized redirect URI** and point to *gCallback* for example: http://localhost:5000/gCallback
- save and note your **CLIENT ID** and **CLIENT KEY**, also download the *client_secret.json* file.

Please note that google changes the developer console from time to time, so the instructions may not mirror the exact way...

### Configuration
- put your client_secret.json file into the app root directory.
- change your **CLIENT ID** in the templates/login.html file accordingly

### Running
On your first run you may want to populate some test Categories by running
```sh
python fillCategories.py
```
then run
```sh
python app.py
```