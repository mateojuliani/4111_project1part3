import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

meals_bp = Blueprint('meal_functions', __name__)



# Adding a new meal
@meals_bp.route('/add_meal')
def add_meal():
  """
  Takes user to the add meal page adn renders the ppage 
  """
   
  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  #Get all the user meal events 
  cursor = g.conn.execute( text("""                          
                            SELECT concat(meal_id, ' | ', start_time, ' | ', type) as name
                            FROM msj2164.meal_event
                            where calendar_id = :cal_id
                            order by start_time desc 
                            """), {"cal_id":calendar_id})
    
  results = cursor.fetchall()
  cursor.close()

  return render_template('meal_addition.html', items=results)

#create a new meal 
@meals_bp.route('/create_new_meal', methods=['POST'])
def create_new_meal():

  """
  This is used to create a new entry in the meal_event table
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  year = int(request.form['year'])
  month = int(request.form['month'])
  day = int(request.form['day'])
  hour = int(request.form['hour'])
  minute = int(request.form['minute'])
  meal_type = request.form['meal-type']

  date_time_string = datetime.datetime(year, month, day, hour, minute).strftime("%Y-%m-%d %H:%M:%S") 
  
  #TODO: Check if the value already exists in the db 
  #TODO: Check if the date inputted is value, 

  cmd = 'INSERT INTO meal_event(calendar_id, start_time, type) VALUES (:calendar_id, :start_time, :meal_type)';
  g.conn.execute(text(cmd), 
                 {
                "calendar_id":calendar_id, 
                 "start_time":date_time_string, 
                 "meal_type":meal_type
                 }
                 );

  #cal_id.close()  # Close the session
  return redirect('/add_meal')

@meals_bp.route('/delete_meal', methods=['POST'])
def delete_meal():

  """
  This is used to delete an meal item
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  meal_id_to_delete = request.form['selected_meal_to_delete'].split("|")[0]

  #print(meal_id_to_delete)
  cmd = 'DELETE FROM meal_event WHERE meal_id = :meal_id_to_delete';
  g.conn.execute(text(cmd), {"meal_id_to_delete": meal_id_to_delete});

  
  return redirect('/add_meal')

#edit a current meal
@meals_bp.route('/edit_current_meal', methods=['POST', 'GET'])
def edit_current_meal():

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  if 'selected_meal' in request.form:
    meal_selected = request.form['selected_meal']
    meal_id = meal_selected.split("|")[0]
    session['meal_id'] = meal_id

  elif 'meal_id' in session:
    meal_id = session['meal_id']
  
  else:
    return redirect('/')


  cursor = g.conn.execute(text("""
                            WITH meal_id as (
                            SELECT * FROM msj2164.meal_event 
                            WHERE meal_id = :meal_id
                            )

                            
                            SELECT * 
                            FROM meal_id as m
                            JOIN msj2164.Food f ON m.meal_id = f.meal_id
                            """), {"meal_id":meal_id})
    
  results = cursor.fetchall()
    

  meal = [
        {
            'food_id':row['food_id'],
            'name': row['name'],
            'grams': row['grams'],
            'calories': row['calories'],
            'carbs': row['carbs'],
            'fats': row['fats'],
            'protein': row['protein'],
        }
        for row in results
  ]

  return render_template('/add_food_item.html', meal = meal)

@meals_bp.route('/add_new_food_item', methods=['POST'])
def add_new_food_item():
  """
  Function to add new items to the 
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')
  
  meal_id = session.get('meal_id')

  food_name = (request.form['food_name'])
  grams = (request.form['grams'])
  calories = (request.form['calories'])
  carbs = (request.form['carbs'])
  fats = (request.form['fats'])
  protein = request.form['protein']

  cmd = 'INSERT INTO Food (meal_id, name, grams, calories, carbs, fats, protein) VALUES (:meal_id, :name, :grams, :calories, :carbs, :fats, :protein)';
  #TODO: Might need to change these to help with sql injections
  g.conn.execute(text(cmd), 
                 {
                 "meal_id": meal_id, 
                 "name": food_name, 
                 "grams": grams, 
                 "calories": calories, 
                 "carbs": carbs, 
                 "fats": fats, 
                 "protein": protein
                 });

  return redirect('/edit_current_meal')

@meals_bp.route('/delete_food_item', methods=['POST'])
def delete_food_item():
  """
  This is used to delete a foods
  """

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  if not user_email or not calendar_id:
    return redirect('/logout')

  try:
    cmd = 'DELETE FROM Food WHERE food_id = :food_id';
    g.conn.execute(text(cmd), {"food_id": request.form["selected_food_to_delete"]});
  except:
    flash("Error Deleting Food")

  return redirect('/edit_current_meal')

@meals_bp.route('/return_add_meal')
def return_add_meal():
  session.pop('meal_id', None)
  return redirect('/add_meal')

@meals_bp.route('/return_dashboard')
def return_dashboard():
  session.pop('meal_id', None)
  session.pop('workout_id', None)
  return redirect('/landing_page')