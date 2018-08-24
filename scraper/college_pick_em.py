from lxml import html
import hashlib
import requests
import collections
import json
import hmac
import argparse

# Command line arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--secret', type=str, required=True,
                    help='Key used to sign API requests.')
parser.add_argument('--espn_cookie', type=str, required=True,
                    help='Needed to make espn scraping requests.')
parser.add_argument('--doc_id', type=str, required=True,
                    help='Coda document ID.')
parser.add_argument('--table_id', type=str, required=True,
                    help='Coda table ID.')
args = parser.parse_args()

ESPN_URL = 'http://fantasy.espn.com/college-football-pickem/2018/en/entry'

def log_and_assert(value, label):
  if not value:
    raise Exception('No value for %s' % label)
  print "%s: %s" % (label, value)


####################
## Start the script.
####################

cookie = {'espn_s2': args.espn_cookie}
page = requests.get(ESPN_URL, cookies=cookie)
tree = html.fromstring(page.text)

week_label = tree.find_class('sp-nav-listitem')[0].find_class('label name')[0].text_content()
log_and_assert(week_label, 'Week')

# Get the list of match ups.
matchups = tree.find_class('matchupRow')
if len(matchups) != 10:
  raise Exception('Unkown error expected 10 games and found %s' % len(matchups))

for game in matchups:

  # Game Information
  matchup_id = int(game.get('data-matchupid'))
  game_date = game.find_class('pickem-date')[0].text_content().replace('Date: ', '')
  game_time = game.find_class('pickem-time')[0].text_content().replace('Time: ', '')
  game_datetime = "%s %s" % (game_date, game_time)

  # Team Information
  # Name
  teams = game.find_class('pickem-team-name')
  away_team = teams[0].find_class('link-text')[0].text_content()
  home_team = teams[1].find_class('link-text')[0].text_content()

  # Percentages
  percentages = game.find_class('games-greenbar-pickem')
  away_team_percent = percentages[0].text_content()
  home_team_percent = percentages[1].text_content()

  # Logo
  images = game.find_class('pickem-teams')
  away_img = images[0].find_class('opponentImage')[0].attrib['src']
  home_img = images[1].find_class('opponentImage')[0].attrib['src']

  # Record
  records = game.find_class('pickem-team-record')
  away_record = records[0].text_content()
  home_record = records[1].text_content()

  # Log for debugging
  # Assert so we don't wipeout good data when an issue occurs
  log_and_assert(matchup_id, 'Matchup id')
  log_and_assert(game_date, 'Date')
  log_and_assert(game_time, 'Time')
  log_and_assert(away_team, 'Away team name')
  log_and_assert(home_team, 'Home team name')
  log_and_assert(away_team_percent, 'Away team percentage')
  log_and_assert(home_team_percent, 'Home team percentage')
  log_and_assert(away_img, 'Away image')
  log_and_assert(home_img, 'Home image')
  log_and_assert(away_record, 'Away record')
  log_and_assert(home_record, 'Home record')

  headers = {'Authorization': 'Bearer %s' % args.secret}
  uri = 'https://coda.io/apis/v1beta1/docs/%s/tables/%s/rows' % (args.doc_id, args.table_id)
  payload = {
    'rows': [
      {
        'cells': [
          {'column': 'Week', 'value': week_label},
          {'column': 'Time', 'value': game_datetime},
          {'column': 'Matchup ID', 'value': matchup_id},
          {'column': 'Away', 'value': away_team},
          {'column': 'Away %', 'value': away_team_percent},
          {'column': 'Away Image', 'value': away_img},
          {'column': 'Away Record', 'value': away_record},
          {'column': 'Home', 'value': home_team},
          {'column': 'Home %', 'value': home_team_percent},
          {'column': 'Home Image', 'value': home_img},
          {'column': 'Home Record', 'value': home_record},
        ],
      },
    ],
    'keyColumns': ['Matchup ID'],
  }

  req = requests.post(uri, headers=headers, json=payload)
  req.raise_for_status() # Throw if there was an error.
  res = req.json()
