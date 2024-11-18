import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Blueprint
import pandas as pd
import plotly.express as px
import datetime

meals_bp = Blueprint('meal_functions', __name__)

#BUG: If the user has no meals or workouts, and they try to edit it, they will be logged out since the form does not exist


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

  food_search_bar = ["meal_id", "start_time", "type", "food_id", "name", "grams", "calories", "carbs", "fats", "protein"]

  try:
    food_column_search = session["meal_column_search"] 
    food_search_value  = session["meal_search_value"] 
  except:
    food_column_search = 'True'
    food_search_value = 'True'

  try:
    cursor_2 = g.conn.execute(
      text("""
      WITH base AS (
      SELECT m.meal_id, start_time, type, food_id, name, grams, calories, carbs, fats, protein
      FROM  msj2164.meal_event as m
      LEFT JOIN msj2164.Food f ON f.meal_id = m.meal_id
      WHERE calendar_id = :cal_id 
      order by start_time desc
      )
      SELECT *
      FROM base 
      where {} = :food_search_value
          """.format(food_column_search)), {"cal_id":calendar_id, "food_search_value":food_search_value} 
    )
  except:
    session.pop('meal_column_search', None) 
    session.pop('meal_search_value', None)
    cursor.close()
    #cursor_2.close() 
    return redirect('/add_meal') #this feels dangerous


  results_2 = cursor_2.fetchall()
  cursor.close()
  cursor_2.close()

  return render_template('meal_addition.html', items=results, food_search_bar = food_search_bar, meals_table = results_2)


@meals_bp.route('/search_meals', methods=['POST'])
def search_meals():

  session["meal_column_search"] = request.form["meal_column_search"]
  session["meal_search_value"] = request.form["meal_search_value"]
  return redirect('/add_meal')

@meals_bp.route('/reset_meal_filter', methods=['POST'])
def reset_meal_filter():

  session.pop('meal_column_search', None) 
  session.pop('meal_search_value', None) 
  return redirect('/add_meal')


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

  try:
    date_time_string = datetime.datetime(year, month, day, hour, minute).strftime("%Y-%m-%d %H:%M:%S") 
  except:
    flash("date not valid")
    return redirect('/add_meal')

  
  #TODO: Check if the value already exists in the db 
  #TODO: Check if the date inputted is value, 

  try:
    cmd = 'INSERT INTO meal_event(calendar_id, start_time, type) VALUES (:calendar_id, :start_time, :meal_type)';
    g.conn.execute(text(cmd), 
                  {
                  "calendar_id":calendar_id, 
                  "start_time":date_time_string, 
                  "meal_type":meal_type
                  }
                  );
  except:
    flash("error adding data")

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

  

  #print(meal_id_to_delete)
  try:
    meal_id_to_delete = request.form['selected_meal_to_delete'].split("|")[0]
    cmd = 'DELETE FROM meal_event WHERE meal_id = :meal_id_to_delete';
    g.conn.execute(text(cmd), {"meal_id_to_delete": meal_id_to_delete});
  except:
    flash("could not delete meal")

  
  return redirect('/add_meal')

#edit a current meal
@meals_bp.route('/edit_current_meal', methods=['POST', 'GET'])
def edit_current_meal():


  #TODO: Add a check to make sure there is a meal event to begin with, i.e. meal 

  user_email = session.get('user_email') 
  calendar_id = session.get('calendar_id') 

  check_meals_exit = g.conn.execute(text("""
                            
                            SELECT * FROM msj2164.meal_event 
                            WHERE calendar_id = :calendar_id
                            

                            """), {"calendar_id":calendar_id})
  
  meal_exist = check_meals_exit.fetchall()

  #This is used to check that a meal exists, otherwise the user gets logged out
  if not meal_exist:
    check_meals_exit.close()
    return redirect('/add_meal')
  check_meals_exit.close()


  #make sure a session is active 
  if not user_email or not calendar_id:
    return redirect('/logout')

  if 'selected_meal' in request.form:
    meal_selected = request.form['selected_meal']
    meal_id = meal_selected.split("|")[0]
    session['meal_id'] = meal_id

  elif 'meal_id' in session:
    meal_id = session['meal_id']
  
  else:
    return redirect('/logout')


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

  try:
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
  except:
    flash("error adding new food item")

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