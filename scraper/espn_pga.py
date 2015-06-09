from lxml import html
import requests

INDEX_NAME = 2
INDEX_STATUS = 3
INDEX_ROUND_1 = 4
INDEX_ROUND_2 = 5
INDEX_ROUND_3 = 6
INDEX_ROUND_4 = 7

# Process the raw status field to see if the golfer was cut
# or what hole they are on.
# return (cut, holes_completed)
def process_status(status):
  past_holes = 54
  # Cut after 36 holes
  if status == 'CUT':
    return (True, 36)
  # +2, E, -4 are all end of round scores.
  elif (status == 'E' or '+' in status or '-' in status):
    return (False, past_holes + 18)
  # Otherwise its a hole count for the day.
  else:
    hole_count = int(status)
    return (False, past_holes + hole_count)

page = requests.get('http://espn.go.com/golf/leaderboard')
tree = html.fromstring(page.text)

# Get the list of golfers.
golfer_element_list = tree.get_element_by_id('regular-leaderboard').find_class('tablehead leaderboard')[0].find_class('sl')
for element in golfer_element_list:
  item_list = element.findall('td')
  status = '%s' % item_list[INDEX_STATUS].text_content()
  cut, hole_count = process_status(status)
  print item_list[INDEX_NAME].text_content()
  print 'Cut: %s' % cut
  print 'Hole Count: %d' % hole_count
  print item_list[INDEX_ROUND_1].text_content()
  print item_list[INDEX_ROUND_2].text_content()
  print item_list[INDEX_ROUND_3].text_content()
  print item_list[INDEX_ROUND_4].text_content()
