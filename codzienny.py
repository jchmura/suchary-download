from datetime import datetime, timedelta
import os
import sys
import json
import time
import facebook
from requests import RequestException
import requests as r
from functions import load_saved, convert_to_date_time, create_suchar_to_save, output_json
try:
    from private_settings import FACEBOOK_TOKEN
except ImportError:
    FACEBOOK_TOKEN = ''


graph = facebook.GraphAPI(FACEBOOK_TOKEN)
graph.base_uri = 'https://graph.facebook.com/v3.2/'

dateLimit = datetime.now() - timedelta(days=3)
minVotes = 500
dataFile = os.environ['HOME'] + '/django/data/codzienny.json'

accepted, ids = load_saved(dataFile)
feed = graph.get_object('212969625440456/feed', limit=100, fields='created_time,picture,id,link')

start = time.clock()
requests = 1
while True:
    if 'data' not in feed:
        print('No data in feed: %s' % feed)
        break
    for entry in feed['data']:
        if 'message' in entry and 'picture' not in entry and 'link' not in entry:
            date = convert_to_date_time(entry['created_time'])
            if date < dateLimit:
                datePassed = True
                break

            try:
                requests += 1
                summary = graph.get_object(entry['id'], fields='likes.limit(1).summary(1)')
            except RequestException:
                print("ERROR: couldn't get object id: %s" % entry['id'], end='\n', file=sys.stderr)
                continue

            if 'likes' in summary:
                votes = summary['likes']['summary']['total_count']
                if votes >= minVotes:
                    new = create_suchar_to_save(entry['id'], date, votes, entry['message'])
                    if entry['id'] not in ids:
                        accepted.append(new)
                        ids.add(entry['id'])
                        print(new['id'], new['date'], new['votes'])
                    else:
                        old = next(item for item in accepted if item['id'] == new['id'])
                        accepted[accepted.index(old)] = new

    else:
        if 'paging' not in feed or 'next' not in feed['paging']:
            break
        next_page = feed['paging']['next']
        elapsedTime = time.clock() - start
        if elapsedTime > 60:
            if requests / elapsedTime > 0.5:
                print("Sleeping for 100s")
                time.sleep(100)
                start = time.clock()
                requests = 0
                print("Resuming")
        try:
            requests += 1
            feed = r.get(next_page).json()
            continue
        except RequestException as e:
            print("ERROR while requesting new page: %s" % e, end='\n', file=sys.stderr)
    break

json.dump(accepted, open(dataFile, 'w'), default=output_json, indent=4)
