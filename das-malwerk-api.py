import requests
import hashlib
import os
import json
import argparse

parser = argparse.ArgumentParser(description='Download samples from das-malwerk')
parser.add_argument('target', help='directory for result')
args = parser.parse_args()


def get_new_target_filename():
    i = 0
    while os.path.exists(os.path.join(args.target, '%06i.bin' % i)):
        i += 1
    return os.path.join(args.target, '%06i' % i)


existing_json_hashes = [
    hashlib.sha256(open(os.path.join(args.target, fn), 'rb').read()).hexdigest()
    for fn in os.listdir(args.target) if fn.endswith('.json')
]
r = requests.get('http://dasmalwerk.eu/api')
for row in r.json()['items']:
    if 'Filename' not in row:
        continue
    if hashlib.sha256(json.dumps(row).encode('utf-8')).hexdigest() in existing_json_hashes:
        continue

    fn = get_new_target_filename()

    fp = open(fn + '.json', 'w')
    fp.write(json.dumps(row))
    fp.close()

    fp = open(fn + '.bin', 'wb')
    dl = requests.get('http://dasmalwerk.eu/zippedMalware/%s.zip' % row['Filename'], stream=True)
    for chunk in dl:
        fp.write(chunk)
    fp.close()
