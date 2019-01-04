# Automated Scrapers

## college-pick-em

Python script that

* Scrapes weekly college pick em match ups from ESPN College Pick em:
  * Teams
  * Game time
  * Percentage of fans picking each team
  * Score

* Writes them to a table in Coda.io document with an upsert

Sample command `python scraper/college_pick_em.py --doc_id x --table_id x --secret x --espn_cookie x`

First 3 args are for the Coda API call, the final one is a valid ESPN auth cookie since the page is authenticated.

Included are configuration files that make this pretty easy to schedule on Heroku using Heroku Scheduler.

![](https://d3vv6lp55qjaqc.cloudfront.net/items/131v2U1H43262P0f1J0r/Screen%20Shot%202019-01-04%20at%206.45.41%20AM.png?X-CloudApp-Visitor-Id=2970276&v=76f4c12b)

## espn-pga-scraper

Scraper for PGA leaderboards on ESPN. Scrapes round by round scores and sends a webhook for each golfer.



