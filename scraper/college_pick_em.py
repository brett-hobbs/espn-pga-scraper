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
                    help='Key used to authenticate API requests.')
parser.add_argument('--espn_cookie', type=str, required=True,
                    help='Needed to make espn scraping requests.')
parser.add_argument('--doc_id', type=str, required=True,
                    help='Coda document ID.')
parser.add_argument('--table_id', type=str, required=True,
                    help='Coda table ID.')
parser.add_argument('--dryrun', type=bool, default=False,
                    help='Don not send API updates')
args = parser.parse_args()

ESPN_URL = 'http://fantasy.espn.com/college-football-pickem/2018/en/entry'

def log_and_assert(value, label):
  if not value:
    raise Exception('No value for %s' % label)
  print "%s: %s" % (label, value)

def find_decendant(elem, classname, index=0):
  return elem.find_class(classname)[index]

def find_decendant_text(elem, classname, index=0):
  elem = find_decendant(elem, classname, index)
  return elem.text_content()

####################
## Start the script.
####################

cookie = {'espn_s2': args.espn_cookie}
page = requests.get(ESPN_URL, cookies=cookie)
tree = html.fromstring(page.text)

week_label = tree.find_class('sp-nav-listitem current')[0].find_class('label name')[0].text_content()
log_and_assert(week_label, 'Week')

# Get the list of match ups.
matchups = tree.find_class('matchupRow')
#if len(matchups) != 10:
#  raise Exception('Unkown error expected 10 games and found %s' % len(matchups))

rows = []

for game in matchups:

  # Game Information
  matchup_id = int(game.get('data-matchupid'))
  game_date = find_decendant_text(game, 'pickem-date').replace('Date: ', '')
  game_time = find_decendant_text(game, 'pickem-time').replace('Time: ', '')
  game_datetime = "%s %s" % (game_date, game_time)

  # Team Information
  # Name
  teams = game.find_class('pickem-team-name')
  away_team = find_decendant_text(teams[0], 'link-text')
  home_team = find_decendant_text(teams[1], 'link-text')

  # Percentages
  percentages = game.find_class('games-greenbar-pickem')
  away_team_percent = percentages[0].text_content()
  home_team_percent = percentages[1].text_content()

  # Logo
  images = game.find_class('pickem-teams')
  away_img = find_decendant(images[0], 'opponentImage').attrib['src']
  home_img = find_decendant(images[1], 'opponentImage').attrib['src']

  # Record
  records = game.find_class('pickem-team-record')
  away_record = records[0].text_content()
  home_record = records[1].text_content()

  # Get the scores if the game has started
  scores = game.find_class('opponent-score')
  away_score = ''
  home_score = ''
  if scores:
    away_score = scores[0].text_content()
    home_score = scores[1].text_content()
    log_and_assert(away_score, 'Away score')
    log_and_assert(home_score, 'Home score')

  # Get the winner if the game is over
  winner = ''
  if game.find_class('away winner'):
    winner = away_team
  if game.find_class('home winner'):
    winner = home_team
  print "Winner: %s" % winner

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
  rows.append(
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
        {'column': 'Winner', 'value': winner},
      ],
    }
  )

# Create payload for the API call
payload = {
  'rows': rows,
  'keyColumns': ['Matchup ID'],
}

if not args.dryrun:
  req = requests.post(uri, headers=headers, json=payload)
  req.raise_for_status() # Throw if there was an error.
  res = req.json()
else:
  print '\nRunning in dryrun mode, payload:'
  print payload
