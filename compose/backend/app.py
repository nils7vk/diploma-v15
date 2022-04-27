#!/usr/bin/env python3

from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
import sys
import requests
import json
import sqlite3
import os
import psycopg2
import datetime

NHL_BASE = "https://statsapi.web.nhl.com" 
NHL_API  = "https://statsapi.web.nhl.com/api/v1"
API_VERSION = 1

canadian_teams = [ "Calgary Flames",
                   "Edmonton Oilers",
                   "Montreal Canadiens",
                   "Ottawa Senators",
                   "Toronto Maple Leafs",
                   "Winnipeg Jets",
                   "Vancouver Canucks" ]

def schedule_link(team_id, season, game_type="R"):
  return NHL_API + "/schedule?" + "teamId=" + str(team_id) + "&season=" + str(season) + "&gameType=" + game_type

def teams_link():
  return NHL_API + "/teams"

def team_roster_link(team_id, season):
  return teams_link() + "/" + str(team_id) + "?expand=team.roster&season=" + str(season)

def nhl_link(link):
  return NHL_BASE + link

def game_linescore_link(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/linescore"

def game_boxscore_link(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/boxscore"

pg_ctx = {
  "user": os.getenv("POSTGRES_USER"),
  "password": os.getenv("POSTGRES_PASSWORD"),
  "host": os.getenv("POSTGRES_HOST"),
  "port": os.getenv("POSTGRES_PORT"),
  "dbname": os.getenv("POSTGRES_DB")
}

pg_conn = None
pg_cursor = None

def nhl_db_open():
  try:
    pg_conn = psycopg2.connect("dbname={} user={} host={} password={}".format(pg_ctx["dbname"], pg_ctx["user"], pg_ctx["host"], pg_ctx["password"]))
    # no transaction
    pg_conn.autocommit = True
    cursor = pg_conn.cursor()
  except psycopg2.OperationalError as error:
      print(str(error))
      sys.exit(1)
  return cursor

def nhl_db_close():
    if pg_conn is not None:
      try:
        pg_conn.close()
      except psycopg2.OperationalError as error:
        print(str(error))
        sys.exit(1)

def nhl_swedes_init(cursor, table_name="swedes", update=False):
  sql_create = '''CREATE TABLE IF NOT EXISTS {} (
                                       gamePk INTEGER,
                                       gameType VARCHAR(256),
                                       season INTEGER,
                                       player_id INTEGER, 
                                       full_name TEXT,
                                       time_on_ice TEXT, 
                                       assists INTEGER, 
                                       goals INTEGER,
                                       team_id INTEGER,
                                       team_name TEXT,
                                       team_link TEXT)'''.format(table_name)
  if update:
    sql_drop = "DROP TABLE IF EXISTS {}".format(table_name)
    sql_query = "{};{}".format(sql_drop, sql_create)
  else:
    sql_query = "{}".format(sql_create)

  try:
    cursor.execute(sql_query)
  except psycopg2.OperationalError as error:
    print(str(error))
    sys.exit(1)

def nhl_swedes_insert(cursor, values_list, table_name="swedes"):
    insert_values = "'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'".format(*values_list)
    sql = '''INSERT INTO {} (gamePk, gameType, season, player_id, full_name, time_on_ice, assists, goals, team_id, team_name, team_link) 
             VALUES ({}) ON CONFLICT DO NOTHING'''.format(table_name, insert_values)
    try:
      cursor.execute(sql)
    except psycopg2.OperationalError as error:
      print(str(error))
      # pass this exception further
      raise

def nhl_swedes_stats_update(cursor, season, game_type):
  # function return status value
  ret = {
      "api_version": API_VERSION,
      "method": "update",
      "result": {
        "status": None
       }
  }
  try:
    res = requests.get(teams_link())
  except requests.RequestException as e:
    print(str(e))
    ret["result"]["status"] = "error"
    return ret

  conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
  db = conn.cursor()
  # Select canadian teams
  db.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, link TEXT)")
  if res.ok and 'application/json' in res.headers['content-type']:
    res_json = res.json()
    for team in res_json['teams']:
      if team['name'].upper() in (name.upper() for name in canadian_teams):
        sql = "INSERT INTO teams VALUES('{}', '{}', '{}')".format(team['id'], team['name'], team['link'])
        db.execute(sql)
  # Placeholder for home games
  db.execute("CREATE TABLE games (gamePk INTEGER, team_id INTEGER, team_link TEXT)")
  # Get teams IDs
  db.execute("SELECT id FROM teams")
  teams = db.fetchall()
  try:
    for team in teams:
      team_id = team[0]
      # Get team schedule for the specific season
      res = requests.get(schedule_link(team_id, season, game_type))
      if res.ok and 'application/json' in res.headers['content-type']:
        res_json = res.json()
        for date in res_json['dates']:
          # We are looking for home games of canadian teams
          for game in date['games']:
            gamePk = game['gamePk']
            team_name = game['teams']['home']['team']['name']
            team_link = game['teams']['home']['team']['link']
            sql = "INSERT INTO games VALUES ('{}','{}','{}')".format(gamePk, team_name, team_link)
            db.execute(sql)
  except requests.RequestException as e:
    print(str(e))
    ret["result"]["status"] = "error"
    return ret
  # init persistent table for swedes
  nhl_swedes_init(cursor, update=False)
  
  db.execute("SELECT DISTINCT gamePk FROM games")
  games = db.fetchall()
  try:
    for gamePk in games:
      res = requests.get(game_boxscore_link(gamePk[0]))
      if res.ok and 'application/json' in res.headers['content-type']:
        boxscore_info = res.json()
        for place in ('home', 'away'):
          for player_id in boxscore_info['teams'][place]['players']:
            team_home_id = boxscore_info['teams'][place]['team']['id']
            team_home_name = boxscore_info['teams'][place]['team']['name']
            team_home_link = boxscore_info['teams'][place]['team']['link']
            player = boxscore_info['teams'][place]['players'][player_id]
            if 'nationality' in player['person'] and player['person']['nationality'] == 'SWE':
              swe_player_id = player['person']['id']
              swe_player_full_name = player['person']['fullName']
              if 'skaterStats' in player['stats']:
                skey = 'skaterStats'
                swe_player_time_on_ice = player['stats'][skey]['timeOnIce']
                swe_player_assists = player['stats'][skey]['assists']
                swe_player_goals = player['stats'][skey]['goals']
              else: continue 
              # insert swedes stats into persisten database
              nhl_swedes_insert(cursor, [gamePk[0], game_type, season, swe_player_id, swe_player_full_name, swe_player_time_on_ice, \
                                           swe_player_assists, \
                                           swe_player_goals, \
                                           team_home_id, \
                                           team_home_name, \
                                           team_home_link ])
  except (requests.RequestException, psycopg2.OperationalError) as e:
    print(str(e))
    ret["result"]["status"] = "error"
    return ret
  # tell everything is ok
  ret["result"]["status"] = "ok"
  return ret

def nhl_swedes_get(cursor, season, game_type, table_name='swedes'):
  sql = "SELECT * FROM {} WHERE season={} AND gameType='{}';".format(table_name, season, game_type)
  try:
    cursor.execute(sql)
    records = cursor.fetchall()
    ret = {
      "api_version": API_VERSION,
      "method": "get",
      "result": {
         "players": []
       }
    }
    for record in records:
      rec_json = {
        "gamePk": record[1],
        "season": record[2],
        "player_id": record[3],
        "full_name": record[4],
        "time_on_ice": record[5],
        "assists": record[6],
        "goals": record[7],
        "team_id": record[8],
        "team_name": record[9],
        "team_link": record[10]
      }
      ret["result"]["players"].append(rec_json)
  except psycopg2.OperationalError as error:
      print(str(error))
      sys.exit(1)
  return ret

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1> Hello </h1>"

@app.route("/nhl/v1/get")
def get():
  now = datetime.datetime.now()
  current_year = request.args.get("season", default = now.year, type = int)
  previous_year = current_year - 1
  season = "{}{}".format(previous_year, current_year)
  game_type = request.args.get("gametype", default = 'R', type = str)
  res = nhl_swedes_get(pg_cursor, season, game_type)
  return json.dumps(res) 

@app.route("/nhl/v1/update")
def update():
  now = datetime.datetime.now()
  current_year = request.args.get("season", default = now.year, type = int)
  previous_year = current_year - 1
  season = "{}{}".format(previous_year, current_year)
  game_type = request.args.get("gametype", default = 'R', type = str)
  res = nhl_swedes_stats_update(pg_cursor, season, game_type)
  return json.dumps(res)

if __name__ == "__main__":
  pg_cursor= nhl_db_open()
  nhl_swedes_init(pg_cursor,update=True)
  app.run(host='0.0.0.0')
