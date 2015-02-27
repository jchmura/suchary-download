from datetime import datetime, timedelta
import os
import wykop
import json
from functions import load_saved, convert_to_date_time, output_json
try:
    from private_settings import WYKOP
except ImportError:
    WYKOP = {}


def create_suchar_to_save(id, date, url, votes, body):
    dst = {'id': id, 'date': date, 'url': url, 'votes': int(votes), 'body': body}
    return dst


api = wykop.WykopAPI(WYKOP['APP_KEY'], WYKOP['SECRET_KEY'])

dateLimit = datetime.now() - timedelta(days=5)
minVotes = 100
dataFile = os.environ['HOME'] + '/django/data/wykop.json'

accepted, ids = load_saved(dataFile)
page = -1

while True:
    page += 1
    sucharPage = api.tag('suchar', page)
    for suchar in sucharPage['items']:
        date = convert_to_date_time(suchar['date'])
        if date < dateLimit:
            datePassed = True
            break

        if suchar['type'] == 'entry' and not suchar['embed'] and suchar['vote_count'] >= minVotes:
            new = create_suchar_to_save(suchar['id'], date, suchar['url'], suchar['vote_count'], suchar['body'])
            if new['id'] not in ids:
                print(new['id'], new['date'], new['votes'])
                accepted.append(new)
                ids.add(new['id'])
            else:
                old = (item for item in accepted if item['id'] == suchar['id']).next()
                accepted[accepted.index(old)] = new
    else:
        continue
    break

json.dump(accepted, open(dataFile, 'w'), default=output_json, indent=4)
