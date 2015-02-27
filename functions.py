from datetime import datetime
import json
from os.path import isfile


def output_json(obj):
    if isinstance(obj, datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()

        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return str(obj)


def input_json(obj):
    new_dic = {}

    for key in obj:
        try:
            if float(key) == int(float(key)):
                new_key = int(key)
            else:
                new_key = float(key)

            new_dic[new_key] = obj[key]
            continue
        except ValueError:
            pass

        try:
            new_dic[str(key)] = datetime.strptime(obj[key], '%Y-%m-%d %H:%M:%S')
            continue
        except (TypeError, ValueError):
            pass

        new_dic[str(key)] = obj[key]

    return new_dic


def load_saved(file):
    if isfile(file):
        try:
            saved = json.load(open(file, 'r'), object_hook=input_json)
        except ValueError:
            saved = []
    else:
        saved = []
    ids = set()
    for suchar in saved:
        ids.add(suchar['id'])
    return saved, ids


def convert_to_date_time(date):
    year = int(date[:4])
    month = int(date[5:7])
    day = int(date[8:10])
    hour = int(date[11:13])
    minute = int(date[14:16])
    second = int(date[17:19])
    suchar_date = datetime(year, month, day, hour, minute, second)
    return suchar_date


def create_suchar_to_save(id, date, votes, body):
    dst = {'id': id, 'date': date, 'votes': votes, 'body': body}
    return dst