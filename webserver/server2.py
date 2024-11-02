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
from flask import Flask, request, render_template, g, redirect, Response, session, url_for
import pandas as pd
import plotly.express as px


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


app.secret_key = '_5#y2L"F4_joe_Q8z\n\xec]/jhsdfsjnhfhhfehehf'


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
engine.execute("""DROP TABLE IF EXISTS test;""")
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


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print(name)
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')


@app.route('/daily_summary')
def daily_summary():
    # Access the user email from the session
    user_email = session.get('user_email')

    if not user_email:
      return redirect(url_for('login'))

    cursor = g.conn.execute("""
                            WITH user_logged_in as (
                            SELECT * FROM msj2164.User_table 
                            WHERE email = %s
                            )

                            
                            SELECT * 
                            FROM user_logged_in u
                            JOIN msj2164.Calendar c ON c.email = u.email
                            JOIN msj2164.Daily_summary ds ON c.calendar_id = ds.calendar_id
                            order by day 
                            """, (user_email,))
    
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
    return render_template('daily_summary.html', summaries=summaries, graph_html=graph_html)
    


#login in code
@app.route('/login', methods=['POST'])
def login():
    

    email = request.form['email']
    
    cursor = g.conn.execute("SELECT * FROM msj2164.User_table WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user:
        session['user_email'] = email  # Store the email in session
        cursor.close()
        return redirect(url_for('daily_summary'))
    else:
        # g.conn.execute("INSERT INTO users (email) VALUES (:email)", {'email': email})
        # session['user_email'] = email  # Store new user email in session
        cursor.close()
        return render_template('bad_login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)  
    return render_template("login.html")


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
