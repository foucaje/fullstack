# Tournament DB

Database Excercises for a Swiss Style Tournament
This version is assuming an even number of players attending the tournament.

### Prequisites
In order to run properly you need the following:

***Python 2.7x*** is required to run the included python files.
If you do not already have python installed you can download and install directly from: https://www.python.org/downloads/

***PostgreSQL DB*** is used as the database. Please check https://www.postgresql.org/ if you do not already got the Database installed on your system.

### Configuration
First you need to create a Database and import the **tournament.sql** file to it.
If your database name is other than **tournament** you will need to modify the code for **tournament.py**
Search the function and modify the dbname according to what you have created before.
```python
def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")
```

### Running the app
You can import and use the tournament.py for your project or run the supplied tests by switching to the directory and execute
```sh
python tournament_test.py
```

### Todo
Improve and extend code to support multiple tournaments.
Implement error / exception handling