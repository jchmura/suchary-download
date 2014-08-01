#!/usr/bin/env python2
from __future__ import print_function
from datetime import datetime, timedelta
from urllib2 import URLError
import os
import sys
import json
import time
import facebook
from functions import load_saved, convert_to_date_time, create_suchar_to_save, output_json
try:
    from private_settings import FACEBOOK_TOKEN
except ImportError:
    FACEBOOK_TOKEN = ''


graph = facebook.GraphAPI(FACEBOOK_TOKEN)

dateLimit = datetime.now() - timedelta(days=3)
minVotes = 1000
dataFile = os.environ['HOME'] + '/devel/django/suchary/data/zacny.json'

accepted, ids = load_saved(dataFile)
feed = graph.get_object('262364993797732/feed', limit=100)

start = time.clock()
requests = 1
while True:
    for entry in feed['data']:
        if 'message' in entry and 'link' not in entry and 'picture' not in entry:
            date = convert_to_date_time(entry['created_time'])
            if date < dateLimit:
                datePassed = True
                break

            try:
                requests += 1
                summary = graph.get_object(entry['id'], fields='likes.limit(1).summary(1)')
            except URLError:
                print("ERROR: couldn't get object id: " + entry['id'], end='\n', file=sys.stderr)
                continue
            except facebook.GraphAPIError as e:
                print("ERROR: %s, id: " % e + entry['id'], end='\n', file=sys.stderr)
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
                        old = (item for item in accepted if item['id'] == new['id']).next()
                        accepted[accepted.index(old)] = new

    else:
        next = feed['paging']['next']
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
            feed = graph.raw_request(next)
            continue
        except facebook.GraphAPIError, e:
            print("ERROR while requesting new page: %s" % e, end='\n', file=sys.stderr)
    break

json.dump(accepted, open(dataFile, 'w'), default=output_json, indent=4)