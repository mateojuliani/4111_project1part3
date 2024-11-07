#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash
import pandas as pd
import plotly.express as px
import datetime
#import blueprints
from workout_functions import workout_bp
from meal_functions import meals_bp
from daily_summary import daily_summary_bp
from select_calendar import calendar_id_bp



tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = '_5#y2L"F4_joe_Q8z\n\xec]/jhsdfsjnhfhhfehehf'

app.register_blueprint(workout_bp)
app.register_blueprint(meals_bp)
app.register_blueprint(daily_summary_bp)
app.register_blueprint(calendar_id_bp)

# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "msj2164"
DB_PASSWORD = "healthdb"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

#DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"
DATABASEURI = "postgresql://msj2164:healthdb@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it

# Mateo - 11/1/24 - Commented out 
#engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

def check_user_is_logged_in():
  user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

  if not user_email:
    return redirect(url_for('login'))
  
  else: return user_email

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    """
    Code to login from main page
    """
    
    session.pop('user_email', None) 
    session.pop('calendar_id', None)
    session.pop('meal_id', None) 
    session.pop('workout_id', None) 

    email = request.form['email']
    
    cursor = g.conn.execute(text("SELECT * FROM msj2164.User_table WHERE email = :email"), {"email":email})
    user = cursor.fetchone()
    
    if user:
        session['user_email'] = email  # Store the email in session
        cursor.close()
        return redirect("/select_calendar")
        #return redirect(url_for('landing_page'))
    else:
        # g.conn.execute("INSERT INTO users (email) VALUES (:email)", {'email': email})
        # session['user_email'] = email  # Store new user email in session
        cursor.close()
        return render_template('bad_login.html')

#Log out
@app.route('/logout')
def logout():
    """
    Code to logout from the dashboard
    """
    session.pop('user_email', None) 
    session.pop('calendar_id', None)
    session.pop('meal_id', None) 
    session.pop('workout_id', None) 
    return render_template("login.html")

@app.route('/add_new_user_page', methods=['POST'])
def add_new_user_page():
    """
    takes user to page to add new user
    """
    
    return render_template("add_user_page.html")

@app.route('/add_new_user', methods=['POST'])
def add_new_user():
    """
    Code to add a new user
    For now, it is empty
    """

    data_to_insert = {"email":request.form["email"],
                      "name":request.form["name"],
                      "height":request.form["height"]
                      }

    try:
        cmd = 'INSERT INTO User_table(email, name, height) VALUES (:email, :name, :height)';
        g.conn.execute(text(cmd), data_to_insert);
        #print("added_name")
    except:
        flash("error adding data")

    return redirect("/")

@app.route('/landing_page')
def landing_page():
    """
    Main app page
    """
    # Get current user email
    user_email = session.get('user_email') 
    calendar_id = session.get('calendar_id')

    if not user_email or not calendar_id:
      return redirect(url_for('logout'))

    cursor = g.conn.execute(text("""
                            SELECT * 
                            FROM msj2164.Daily_summary
                            where calendar_id = :calendar_id
                            order by day 
                            """), {"calendar_id":calendar_id})
    
    results = cursor.fetchall()
    

    summaries = [
        {
            'summary_id': row['summary_id'],
            'calendar_id': row['calendar_id'],
            'day': row['day'],
            'rating': row['rating'],
            'weight': row['weight'],
            'sleep_quality': row['sleep_quality'],
            'notes': row['notes']
        }
        for row in results
    ]

    data_plot_1 = [(row['day'], row['rating']) for row in results]
    df = pd.DataFrame(data_plot_1, columns=['day', 'rating'])

    fig = px.line(df, x='day', y='rating', title='Daily Ratings Over Time')
    graph_html = fig.to_html(full_html=False)

    cursor.close()  # Close the session
    return render_template('landing_page.html', summaries=summaries, graph_html=graph_html)
    


#end of meal, start of workout

# Adding a new workout page


#TODO: Some of these things you cant get bc i believe you just put them as POST, not GET
#Maybe that is how the 

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
