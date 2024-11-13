import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

daily_summary_bp = Blueprint('daily_summary', __name__)



@daily_summary_bp.route('/add_daily_summary')
def add_daily_summary():
    """
    Takes user to the add daily_summary_page
    """
    
    user_email = session.get('user_email') 
    calendar_id = session.get('calendar_id') 

    if not user_email or not calendar_id:
        return redirect('/logout')
    
    # cursor = g.conn.execute(text("""
    #                         WITH calendar_id as (
    #                         SELECT * FROM msj2164.User_table 
    #                         WHERE email = :user_email
    #                         )

                            
    #                         SELECT * 
    #                         FROM user_logged_in u
    #                         JOIN msj2164.Calendar c ON c.email = u.email
    #                         JOIN msj2164.Daily_summary ds ON c.calendar_id = ds.calendar_id
    #                         order by day 
    #                         """), {"user_email":user_email})

    cursor = g.conn.execute(text("""                            
                            SELECT * 
                            FROM msj2164.Daily_summary
                            where calendar_id = :calendar_id
                            order by day 
                            """), {"calendar_id":calendar_id})
    
    results = cursor.fetchall()
    

    summaries = [
        {
            'summary_id': int(row['summary_id']),
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
def delete_daily_summary():

    """
    This is used to delete an meal item
    """

    user_email = session.get('user_email') 
    calendar_id = session.get('calendar_id') 

    if not user_email or not calendar_id:
        return redirect('/logout') 

    ds_id_to_delete = request.form['selected_ds_delete']

    #print(meal_id_to_delete)
    try:
        cmd = 'DELETE FROM daily_summary WHERE summary_id = :ds_id_to_delete';
        g.conn.execute(text(cmd), {"ds_id_to_delete": ds_id_to_delete});
    except:
        flash("error adding data")

    
    return redirect('/add_daily_summary')

@daily_summary_bp.route('/add_new_daily_summary', methods=['POST'])
def add_new_daily_summary():
    """
    Function to add new items to the lift table
    """

    user_email = session.get('user_email') 
    calendar_id = session.get('calendar_id') 

    if not user_email or not calendar_id:
        return redirect('/logout')

    try:
        date = datetime.datetime(int(request.form['year']), int(request.form['month']), int(request.form['day']) ).strftime("%Y-%m-%d")
    except:
        flash("error adding date")
        redirect('/add_daily_summary')


    cursor = g.conn.execute(text("""                            
                            SELECT * 
                            FROM msj2164.Daily_summary
                            where calendar_id = :calendar_id
                            and day = :day
                            order by day 
                            """), {"calendar_id":calendar_id, "day":date})
    
    results = cursor.fetchall()

    if results: #if the date already exists, then don't do anything
        flash("duplicate data")
        return redirect('/add_daily_summary')

    data_to_insert = {
        "calendar_id": calendar_id, 
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

    cursor.close()
    return redirect('/add_daily_summary')