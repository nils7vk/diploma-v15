#!/usr/bin/env python3

import sys
import requests
import json
import sqlite3

NHL_API = "https://statsapi.web.nhl.com/api/v1"
NHL_TEAMS = NHL_API + "/teams"

canadian_teams = [ "Calgary Flames",
                   "Edmonton Oilers",
                   "Montreal Canadiens",
                   "Ottawa Senators",
                   "Toronto Maple Leafs",
                   "Winnipeg Jets",
                   "Vancouver Canucks" ]

def schedule_link(team_id, season, game_type="R"):
  return NHL_API + "/schedule?" + "teamId=" + str(team_id) + "&season=" + season + "&gameType=" + game_type

if __name__ == "__main__":
  try:
    res = requests.get(NHL_TEAMS)
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
  # Get teams IDs
  db.execute("SELECT id FROM teams")
  
  records = db.fetchall()
  for record in records:
    team_id = record[0]
    # Get team schedule for the specific season
    res = requests.get(schedule_link(team_id, "20202021"))
    if res.ok and 'application/json' in res.headers['content-type']:
      res_json = res.json()
      for date in res_json['dates']:
        # We are looking for home games
        for game in date['games']:
          print(game['gamePk'])
          print(game['teams']['home']['team'])
