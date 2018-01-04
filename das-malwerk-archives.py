import requests
import datetime
import hashlib
import os
import json
import argparse

parser = argparse.ArgumentParser(description='Download samples from das-malwerk')
parser.add_argument('target', help='directory for result')
args = parser.parse_args()


def daterange(start_date, end_date):
    if start_date <= end_date:
        for n in range((end_date - start_date).days + 1):
            yield start_date + datetime.timedelta(n)
    else:
        for n in range((start_date - end_date).days + 1):
            yield start_date - datetime.timedelta(n)


zips = sorted([fn for fn in os.listdir(args.target) if fn.endswith('.zip')], reverse=True)
start_date_string = zips[0][:10] if zips else '2016-10-23'
start_date = datetime.datetime(int(start_date_string[:4]), int(start_date_string[5:7]), int(start_date_string[8:]) + 1)
for current_date in daterange(start_date, datetime.datetime.now()):
    current_date_string = current_date.strftime('%Y-%m-%d')
    dl = requests.get('http://dasmalwerk.eu/archive/%s.zip' % current_date_string, stream=True)
    if dl.status_code == 404:
        continue
    with open(os.path.join(args.target, current_date_string + '.zip'), 'wb') as fp:
        for chunk in dl:
            fp.write(chunk)
