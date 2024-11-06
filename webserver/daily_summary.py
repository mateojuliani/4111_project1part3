import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

daily_summary_bp = Blueprint('daily_summary', __name__)

def check_user_is_logged_in(): #this is a bad practice but oh well im too lazy to change it
  user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

  if not user_email:
    return redirect(url_for('login'))
  
  else: return user_email


@daily_summary_bp.route('/add_daily_summary')
def add_daily_summary():
    """
    Takes user to the add daily_summary_page
    """
    
    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('login'))
    
    cursor = g.conn.execute(text("""
                            WITH user_logged_in as (
                            SELECT * FROM msj2164.User_table 
                            WHERE email = :user_email
                            )

                            
                            SELECT * 
                            FROM user_logged_in u
                            JOIN msj2164.Calendar c ON c.email = u.email
                            JOIN msj2164.Daily_summary ds ON c.calendar_id = ds.calendar_id
                            order by day 
                            """), {"user_email":user_email})
    
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



    return render_template('daily_summary_addition.html', summaries=summaries)


@daily_summary_bp.route('/delete_daily_summary', methods=['POST'])
def delete_meal():

    """
    This is used to delete an meal item
    """

    user_email = check_user_is_logged_in() #tbd if this works 

    ds_id_to_delete = request.form['selected_ds_delete']

    #print(meal_id_to_delete)
    cmd = 'DELETE FROM daily_summary WHERE summary_id = :ds_id_to_delete';
    g.conn.execute(text(cmd), {"ds_id_to_delete": ds_id_to_delete});

    
    return redirect('/add_daily_summary')

@daily_summary_bp.route('/add_new_daily_summary', methods=['POST'])
def add_new_daily_summary():
    """
    Function to add new items to the lift table
    """

    user_email = check_user_is_logged_in()
    # TODO: Set this up properly
    # This is an good way to handle making sure workout id is valid
    cal_id = g.conn.execute(text("""
                                WITH user_logged_in as (
                                SELECT * FROM msj2164.User_table 
                                WHERE email = :user_email
                                )
                            
                                SELECT calendar_id
                                FROM user_logged_in u
                                JOIN msj2164.Calendar c ON c.email = u.email
                                LIMIT 1
                                """), {"user_email":user_email})
    
    cal_id_val = cal_id.fetchone()[0]

    

    date = datetime.datetime(int(request.form['year']), int(request.form['month']), int(request.form['day']) ).strftime("%Y-%m-%d")

    data_to_insert = {
        "calendar_id": cal_id_val, 
        "day": date, 
        "rating": request.form['rating'], 
        "weight": request.form['weight'], 
        "sleep_quality": request.form['sleep_quality'], 
        "notes": request.form['notes'], 
    }
    try:
        cmd = 'INSERT INTO daily_summary(calendar_id, day, rating, weight, sleep_quality, notes) VALUES (:calendar_id, :day, :rating, :weight, :sleep_quality, :notes)';
        g.conn.execute(text(cmd), data_to_insert);
    except:
        flash("error adding data")

    return redirect('/add_daily_summary')