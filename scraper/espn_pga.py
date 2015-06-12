from lxml import html
import requests
import collections

INDEX_NAME = 3
INDEX_TO_PAR = 4
INDEX_STATUS = 6
INDEX_ROUND_1 = 7
INDEX_ROUND_2 = 8
INDEX_ROUND_3 = 9
INDEX_ROUND_4 = 10

Stats = collections.namedtuple('Stats', ('name', 'score_to_par', 'cut', 'holes', 'rounds'))

# Process the raw status field to see if the golfer was cut
# or what hole they are on.
# returns (cut, partial_round_holes)
def process_status(status):
  # Cut after 36 holes
  if status == 'CUT' or status == 'WD':
    return (True, 0)
  # +2, E, -4 are all end of round scores.
  elif (status == 'F' or '+' in status or '-' in status):
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
  if raw_score == 'E' or raw_score == '-':
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
    if score == '-':
      hole_count -= 18
  hole_count += partial_round_holes
  return hole_count


page = requests.get('http://espn.go.com/golf/leaderboard')
tree = html.fromstring(page.text)

# Get the list of golfers.
golfer_element_list = tree.get_element_by_id('regular-leaderboard').find_class('tablehead leaderboard')[0].find_class('sl')
for element in golfer_element_list:
  item_list = element.findall('td')

  # Remove withdrawn goilfers.
  status = '%s' % item_list[INDEX_STATUS].text_content()
  if (status == 'WD'):
    continue

  cut, incomplete_hole_count = process_status(status)
  rounds = [
    item_list[INDEX_ROUND_1].text_content(),
    item_list[INDEX_ROUND_2].text_content(),
    item_list[INDEX_ROUND_3].text_content(),
    item_list[INDEX_ROUND_4].text_content(),
  ]

  stats = Stats(
    name=item_list[INDEX_NAME].text_content(),
    score_to_par=process_score(item_list[INDEX_TO_PAR].text_content()),
    cut=cut,
    holes=calculate_hole_count(rounds, incomplete_hole_count),
    rounds=[round if round != '-' else '' for round in rounds]
  )
  print '%s Cut: %s Holes: %d Score: %d' % (stats.name, stats.cut, stats.holes, stats.score_to_par)
  print 'Rounds: %s %s %s %s' % (stats.rounds[0], stats.rounds[1], stats.rounds[2], stats.rounds[3])
