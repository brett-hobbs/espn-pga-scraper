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
parser.add_argument('--doc_url', type=str, required=True,
                    help='API endpoint for the document.')
parser.add_argument('--prod', type=bool, default=False,
                    help='Send API requests to production.')
parser.add_argument('--tournament_state', choices=['before', 'during', 'after'],
                    default='before',
                    help='Whether the tournament is in progress or not.')
parser.add_argument('--signature_header', type=str, required=True,
                    help='Header name for signature.')
args = parser.parse_args()

# ESPN changes the columns depending on the state of the
# tournament.
if args.tournament_state == 'before':
  INDEX_NAME = 1
  INDEX_TO_PAR = -1
  INDEX_STATUS = 2
elif args.tournament_state == 'during':
  INDEX_NAME = 3
  INDEX_TO_PAR = 4
  INDEX_STATUS =  6
  INDEX_ROUND_1 = 7
  INDEX_ROUND_2 = 8
  INDEX_ROUND_3 = 9
  INDEX_ROUND_4 = 10
elif args.tournament_state == 'after':
  INDEX_NAME = 2
  INDEX_TO_PAR = 3
  INDEX_STATUS =  3
  INDEX_ROUND_1 = 4
  INDEX_ROUND_2 = 5
  INDEX_ROUND_3 = 6
  INDEX_ROUND_4 = 7

# Prod vs Dev column ids.
COL_IDS = {
  'name':    'c-Iwp7VTcuGg' if args.prod else 'c-gkJ7VUzTIw',
  'cut':     'c-WQp7Vd5REQ' if args.prod else 'c-gkJ7VUvwng',
  'holes' :  'c-Wwp7VQa06w' if args.prod else 'c-gkJ7Vb3NbA',
  'score' :  'c-Iwp7VZEJLQ' if args.prod else 'c-gkJ7VeyP9A',
  'round1' : 'c-Iwp7VQEGhQ' if args.prod else 'c-gkJ7Vez0Pg',
  'round2' : 'c-Iwp7Vb0QHQ' if args.prod else 'c-MbWAVWipYw',
  'round3' : 'c-Uwp7VWjnNQ' if args.prod else 'c-M7WAVfnU9A',
  'round4' : 'c-Vgp7VWLxIA' if args.prod else 'c-N7WAVbeoZg',
}

ESPN_URL = 'http://espn.go.com/golf/leaderboard'

Stats = collections.namedtuple('Stats', ('name', 'score_to_par', 'cut', 'holes', 'rounds'))

# Process the raw status field to see if the golfer was cut
# or what hole they are on.
# returns (cut, partial_round_holes)
def process_status(status):
  # Cut after 36 holes
  if status == 'CUT' or status == 'WD':
    return (True, 0)
  # +2, E, F, -4 are all end of round scores.
  elif (status == 'F' or
        status == 'E' or
        '+' in status or
        '-' in status):
    return (False, 0)
  # Start time means they haven't teed off yet.
  elif ('AM' in status or 'PM' in status):
    return (False, 0)
  # Otherwise its a hole count for the day.
  else:
    hole_count = int(status)
    return (False, hole_count)

def process_score(raw_score):
  # Cut after 36 holes
  if raw_score == 'CUT':
    return
  elif raw_score == 'E' or raw_score == '-':
    return 0
  elif '-' in raw_score:
    return int(raw_score)
  else:
    return int(raw_score)

# Based on round scores and incomplete hole count
# caluculate total holes.
# returns total_hole_count
def calculate_hole_count(rounds, partial_round_holes):
  hole_count = 72
  for score in rounds:
    if score == 0:
      hole_count -= 18
  hole_count += partial_round_holes
  return hole_count

# Parse the row columns for stats.
def get_stats(item_list):
  status = '%s' % item_list[INDEX_STATUS].text_content()
  cut, incomplete_hole_count = process_status(status)
  rounds = [0, 0, 0, 0]
  score_to_par = ''
  if args.tournament_state != 'before':
    score_to_par = process_score(item_list[INDEX_TO_PAR].text_content()),
    rounds = [
      item_list[INDEX_ROUND_1].text_content(),
      item_list[INDEX_ROUND_2].text_content(),
      item_list[INDEX_ROUND_3].text_content(),
      item_list[INDEX_ROUND_4].text_content(),
    ]
    rounds=[int(round) if round != '-' else 0 for round in rounds]

  return Stats(
    name=item_list[INDEX_NAME].text_content(),
    score_to_par=score_to_par,
    cut=cut,
    holes=calculate_hole_count(rounds, incomplete_hole_count),
    rounds=rounds
  )

## Start the script.
page = requests.get(ESPN_URL)
tree = html.fromstring(page.text)

# Get the list of golfers.
golfer_element_list = tree.get_element_by_id('regular-leaderboard').find_class('tablehead leaderboard')[0].find_class('sl')
for element in golfer_element_list:
  item_list = element.findall('td')

  # Remove withdrawn goilfers.
  status = '%s' % item_list[INDEX_STATUS].text_content()
  if (status == 'WD'):
    continue

  stats = get_stats(item_list)

  # Construct the payload for the request.
  raw_payload = {
    COL_IDS['name'] : stats.name,
    COL_IDS['cut'] : stats.cut,
    COL_IDS['holes'] : stats.holes,
    COL_IDS['score'] : stats.score_to_par,
    COL_IDS['round1'] : stats.rounds[0],
    COL_IDS['round2'] : stats.rounds[1],
    COL_IDS['round3'] : stats.rounds[2],
    COL_IDS['round4'] : stats.rounds[3],
  }
  payload = json.dumps(raw_payload, separators=(',', ':'))

  # Send the request.
  signature = hmac.new(args.secret, msg=payload, digestmod=hashlib.sha1).hexdigest()
  headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
  headers[args.signature_header] = signature
  r = requests.post(args.doc_url, data=payload, headers=headers, verify=False)
  print 'Request sent: %s' % r.status_code

