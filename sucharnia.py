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

DATE_LIMIT = datetime.now() - timedelta(days=3)
MAX_OVER_DATE = 10
MIN_VOTES = 150
DATA_FILE = os.environ['HOME'] + '/django/data/sucharnia.json'

accepted, ids = load_saved(DATA_FILE)
feed = graph.get_object('495903230481274/feed', limit=100)

start = time.time()
over_date = 0
try:
    while True:
        for entry in feed['data']:
            if 'message' in entry and 'picture' not in entry and 'link' not in entry:
                date = convert_to_date_time(entry['created_time'])
                if date < DATE_LIMIT:
                    if over_date > MAX_OVER_DATE:
                        over_date = 0
                        break
                    else:
                        over_date += 1
                        continue
                else:
                    over_date = 0

                try:
                    time.sleep(1)
                    summary = graph.get_object(entry['id'], fields='likes.limit(1).summary(1)')
                except RequestException:
                    print("ERROR: couldn't get object id: " + entry['id'], file=sys.stderr)
                    continue

                if 'likes' in summary:
                    votes = summary['likes']['summary']['total_count']
                    if votes >= MIN_VOTES:
                        new = create_suchar_to_save(entry['id'], date, votes, entry['message'])
                        if entry['id'] not in ids:
                            accepted.append(new)
                            ids.add(entry['id'])
                            print(new['id'], new['date'], new['votes'])
                        else:
                            old = next(item for item in accepted if item['id'] == new['id'])
                            accepted[accepted.index(old)] = new

        else:
            next_page = feed['paging']['next']
            try:
                time.sleep(3)
                print("Next page")
                feed = r.get(next_page).json()
                continue
            except RequestException as e:
                print("ERROR while requesting new page: %s" % e, file=sys.stderr)
        break
except Exception as e:
    print(e, file=sys.stderr)
finally:
    json.dump(accepted, open(DATA_FILE, 'w'), default=output_json, indent=4)
