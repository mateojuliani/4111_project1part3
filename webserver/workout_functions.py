import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

workout_bp = Blueprint('workout_functions', __name__)

@workout_bp.route('/add_workout')
def add_workout():
  """
  Takes user to the add workout page and renders the page 
  """
   
  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  #Get all the user meal events 
  cursor = g.conn.execute( text("""                          
                            SELECT concat(workout_id, ' | ', start_time, ' | ', end_time, ' | ', type) as name
                            FROM msj2164.workout_event
                            where calendar_id = :cal_id
                            order by start_time desc 
                            """), {"cal_id":calendar_id})
    
  results = cursor.fetchall()

  return render_template('workout_addition.html', items=results)

# Adding a new workout
@workout_bp.route('/create_new_workout', methods=['POST'])
def create_new_workout():

  #TODO: Fix this check_user_is_logged_in func
  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')
  
  start_year = int(request.form['start_year'])
  start_month = int(request.form['start_month'])
  start_day = int(request.form['start_day'])
  start_hour = int(request.form['start_hour'])
  start_minute = int(request.form['start_minute'])

  end_year = int(request.form['end_year'])
  end_month = int(request.form['end_month'])
  end_day = int(request.form['end_day'])
  end_hour = int(request.form['end_hour'])
  end_minute = int(request.form['end_minute'])
  
  workout_type = request.form["workout_type"]

  try:
    start_string = datetime.datetime(start_year, start_month, start_day, start_hour, start_minute).strftime("%Y-%m-%d %H:%M:%S") 
    end_string = datetime.datetime(end_year, end_month, end_day, end_hour, end_minute).strftime("%Y-%m-%d %H:%M:%S")
  except:
    flash("dates are not valid")
    redirect('/add_workout')

  if datetime.datetime(end_year, end_month, end_day, end_hour, end_minute) <= datetime.datetime(start_year, start_month, start_day, start_hour, start_minute):
    print("here")
    flash("Start date needs to be before end date")
    return redirect('/add_workout')


  #TODO: Check if the value already exists in the db 
  #TODO: Check if the date inputted is value, 
  # print(cal_id_val)
  # print(start_string)
  # print(end_string)
  # print(workout_type)

  try:
    cmd = 'INSERT INTO workout_event (calendar_id, start_time, end_time, type) VALUES (:calendar_id, :start_time, :end_time, :workout_type)';
    g.conn.execute(text(cmd), 
                  {
                  "calendar_id":calendar_id, 
                  "start_time":start_string, 
                  "end_time":end_string, 
                  "workout_type":workout_type
                  }
                  );
  except:
    flash("error adding code")

  #cal_id.close()  # Close the session
  return redirect('/add_workout')


@workout_bp.route('/delete_workout', methods=['POST'])
def delete_workout():

  """
  This is used to delete an workout item
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout') 

  

  try:
    workout_id_to_delete = request.form['selected_workout_to_delete'].split("|")[0]
    cmd = 'DELETE FROM workout_event WHERE workout_id = :workout_id_to_delete';
    g.conn.execute(text(cmd), {"workout_id_to_delete": workout_id_to_delete});
  except:
    flash("error in deleting the workout")

  
  return redirect('/add_workout')

@workout_bp.route('/edit_current_workout', methods=['POST', 'GET'])
def edit_current_workout():

  
  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  check_workout_exit = g.conn.execute(text("""
                            
                            SELECT * FROM msj2164.workout_event 
                            WHERE calendar_id = :calendar_id
                            

                            """), {"calendar_id":calendar_id})
  
  workout_exist = check_workout_exit.fetchall()

  #This is used to check that a meal exists, otherwise the user gets logged out
  if not workout_exist:
    check_workout_exit.close()
    return redirect('/add_workout')
  check_workout_exit.close()

  if not user_email or not calendar_id:
    return redirect('/logout')

  if 'selected_workout' in request.form:
    workout_selected = request.form['selected_workout']
    workout_id = workout_selected.split("|")[0]
    session['workout_id'] = workout_id

  elif 'workout_id' in session:
    workout_id = session['workout_id']
  
  else:
    return redirect('/')

  #get lift items
  cursor_lift = g.conn.execute(text("""
                            WITH workout_id as (
                            SELECT * FROM msj2164.workout_event 
                            WHERE workout_id = :workout_id
                            )
                            SELECT * 
                            FROM workout_id as m
                            JOIN msj2164.Lift f ON m.workout_id = f.workout_id
                            """), {"workout_id":workout_id})
    
  results_lift = cursor_lift.fetchall()
    

  lifts = [
        {
            'lift_id':row['lift_id'],
            'type': row['type'],
            'weight': row['weight'],
            'reps': row['reps'],
            'sets': row['sets'],

        }
        for row in results_lift
  ]

  #get cardio items

  cursor_cardio = g.conn.execute(text("""
                            WITH workout_id as (
                            SELECT * FROM msj2164.workout_event 
                            WHERE workout_id = :workout_id
                            )
                            SELECT * 
                            FROM workout_id as m
                            JOIN msj2164.cardio f ON m.workout_id = f.workout_id
                            """), {"workout_id":workout_id})
    
  results_cardio = cursor_cardio.fetchall()
    

  cardios = [
        {
            'cardio_id':row['cardio_id'],
            'type': row['type'],
            'duration': row['duration'],
        }
        for row in results_cardio
  ]

  return render_template('/add_lift_cardio.html', lifts = lifts, cardios = cardios)

@workout_bp.route('/add_new_lift', methods=['POST'])
def add_new_lift():
  """
  Function to add new items to the lift table
  """

  # TODO: Set this up properly
  # This is an good way to handle making sure workout id is valid
  workout_id = session.get('workout_id')
  if not workout_id:
    return redirect('/edit_current_workout')

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  data_to_insert = {
    "workout_id": workout_id, 
    "type": request.form['type'], 
    "weight": request.form['weight'], 
    "reps": request.form['reps'], 
    "sets": request.form['sets'], 
  }

  try:
    cmd = 'INSERT INTO Lift(workout_id, type, weight, reps, sets) VALUES (:workout_id, :type, :weight, :reps, :sets)';
    g.conn.execute(text(cmd), data_to_insert);
  except:
    flash("error adding data")

  return redirect('/edit_current_workout')

@workout_bp.route('/add_new_cardio', methods=['POST'])
def add_new_cardio():
  """
  Function to add new items to the cardio table
  """

  # TODO: Set this up properly
  # This is an interesting way to handle making sure workout id is valid
  workout_id = session.get('workout_id')
  if not workout_id:
    return redirect('/edit_current_workout')

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  data_to_insert = {
    "workout_id": workout_id, 
    "type": request.form['type'], 
    "duration": request.form['duration'], 
  }

  #TODO: add this try catch to all of this stuff  
  try:
    cmd = 'INSERT INTO cardio(workout_id, type, duration) VALUES (:workout_id, :type, :duration)';
    g.conn.execute(text(cmd), data_to_insert);
  except:
    #TODO: investigate if we can use rollback? rollback()
    #Tbd if flash does anything?
    #flash("An error occured with adding the data. Please revise inputs")
    return redirect('/edit_current_workout')

  return redirect('/edit_current_workout')

@workout_bp.route('/delete_lift', methods=['POST'])
def delete_lift():
  """
  This is used to delete a lift item
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  try:
    cmd = 'DELETE FROM Lift WHERE lift_id = :lift_id';
    g.conn.execute(text(cmd), {"lift_id": request.form["selected_lift_to_delete"]});
  except:
    flash("Error Deleting Lift")

  return redirect('/edit_current_workout')

@workout_bp.route('/delete_cardio', methods=['POST'])
def delete_cardio():
  """
  This is used to delete a cardio item
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  try:
    cmd = 'DELETE FROM cardio WHERE cardio_id = :cardio_id';
    g.conn.execute(text(cmd), {"cardio_id": request.form["selected_cardio_to_delete"]});
  except:
    flash("Error Deleting Cardio")

  return redirect('/edit_current_workout')


@workout_bp.route('/return_add_workout')
def return_add_workout():
  session.pop('workout_id', None) 
  return redirect('/add_workout')