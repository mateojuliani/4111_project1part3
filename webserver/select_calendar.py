import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

calendar_id_bp = Blueprint('calendar_id', __name__)

@calendar_id_bp.route('/select_calendar')
def select_calendar():
    """
    Select Calendar
    """

    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('logout'))
    # print(email)
    # print(session.get('user_email'))

    cursor = g.conn.execute(text("SELECT calendar_id FROM msj2164.Calendar WHERE email = :email"), {"email":user_email})
    cal = cursor.fetchall()
    cursor.close()
    
    return render_template('select_calendar.html', items = cal)


@calendar_id_bp.route('/create_new_calendar', methods=['POST'])
def create_new_calendar():
    """
    Creates a new calendar
    """

    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('logout'))
    # print(email)
    # print(session.get('user_email'))

    data_to_insert = {"email":user_email}

    try:
        cmd = 'INSERT INTO Calendar(email) VALUES (:email)';
        g.conn.execute(text(cmd), data_to_insert);
    except:
        flash("error adding data")

    return redirect('/select_calendar')

@calendar_id_bp.route('/delete_calendar', methods=['POST'])
def delete_calendar():
    """
    Deletes a calendar
    """

    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('logout')) 

    cal_id = request.form['selected_cal_id_to_delete']

    try:
        cmd = 'DELETE FROM Calendar WHERE calendar_id = :cal_id';
        g.conn.execute(text(cmd), {"cal_id": cal_id});
    except:
        flash("error deleting data")

    return redirect('/select_calendar')

@calendar_id_bp.route('/select_calendar_to_view', methods=['POST'])
def select_calendar_to_view():
    """
    Selects calendar and goes to landing page
    """

    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('logout')) 

    session['calendar_id'] = request.form['selected_calendar']

    return redirect('/landing_page')


@calendar_id_bp.route('/delete_user', methods=['POST'])
def delete_user():
    """
    Deletes a user
    """

    user_email = session.get('user_email') #TODO: Check that this isnt using an ORM

    if not user_email:
        return redirect(url_for('logout')) 

    try:
        cmd = 'DELETE FROM User_table WHERE email = :user_email';
        g.conn.execute(text(cmd), {"user_email": user_email});
    except:
        flash("error deleting data")

    return redirect('/logout')
    