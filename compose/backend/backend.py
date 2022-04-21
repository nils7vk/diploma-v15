#!/usr/bin/env python3

import sys
import requests
import json
import sqlite3

NHL_BASE = "https://statsapi.web.nhl.com" 
NHL_API  = "https://statsapi.web.nhl.com/api/v1"
NHL_SEASON = 20202021

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

def team_roster(team_id, season):
  return teams_link() + "/" + str(team_id) + "?expand=team.roster&season=" + str(season)

def nhl_link(link):
  return NHL_BASE + link

def game_linescore(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/linescore"

def game_boxscore(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/boxscore"

if __name__ == "__main__":
  try:
    res = requests.get(teams_link())
  except requests.RequestException as e:
    print(str(e))
    quit()

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
  for team in teams:
    team_id = team[0]
    # Get team schedule for the specific season
    res = requests.get(schedule_link(team_id, NHL_SEASON))
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
 
  db.execute("SELECT DISTINCT gamePk FROM games")
  games = db.fetchall()
  for gamePk in games:
    res = requests.get(game_boxscore(gamePk[0]))
    if res.ok and 'application/json' in res.headers['content-type']:
      boxscore_info = res.json()
      for player_id in boxscore_info['teams']['home']['players']:
        team_home_id = boxscore_info['teams']['home']['team']['id']
        team_home_name = boxscore_info['teams']['home']['team']['name']
        team_home_link = boxscore_info['teams']['home']['team']['link']
        player = boxscore_info['teams']['home']['players'][player_id]
        if player['person']['birthCountry'] == 'SWE':
          swe_player_id = player['person']['id']
          swe_player_full_name = player['person']['fullName']
          if 'skaterStats' in player['stats']:
            skey = 'skaterStats'
            swe_player_time_on_ice = player['stats'][skey]['timeOnIce']
            swe_player_assists = player['stats'][skey]['assists']
            swe_player_goals = player['stats'][skey]['goals']
          else: continue 
          swe_player_team_id = team_home_id
          swe_player_team_name = team_home_name
          swe_player_team_link = team_home_link
          print("{} {} {} {} {}".format(swe_player_id, swe_player_full_name, swe_player_time_on_ice, swe_player_assists, swe_player_goals))
