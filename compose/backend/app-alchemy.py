#!/usr/bin/env python3

from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
import requests
import sys
import json

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

def team_roster_link(team_id, season):
  return teams_link() + "/" + str(team_id) + "?expand=team.roster&season=" + str(season)

def nhl_link(link):
  return NHL_BASE + link

def game_linescore_link(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/linescore"

def game_boxscore_link(gamePk):
  return NHL_API + "/game/" + str(gamePk) + "/boxscore"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# create in-memory database
db = SQLAlchemy(app)

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text, nullable=False)

if __name__ == "__main__":
    # create our database
    db.create_all()

    try:
        # get list of nhl teams
        res = requests.get(teams_link())
    except requests.RequestEception as e:
        print(str(e))
        quit()

    if res.ok and 'application/json' in res.headers['content-type']:
        res_json = res.json()
        for team in res_json['teams']:
            # select canadian teams from the list
            if team['name'].upper() in (name.upper() for name in canadian_teams):
              _team = Team(id=team['id'], name=team['name'], link=team['link'])
              db.session.add(_team)
        db.session.commit()

    for team in Team.query.all():
        print(f"id={team.id}, name={team.name}, link={team.link}")
