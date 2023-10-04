#!/usr/bin/env python3

# Analysis module. This will be a mongodb app tha gathers parsed results from
# the parsing app, and analyses them for preoblems. Remeber that in a real world
# app the results would be from log files being collected off customer networks.
# We will simulate this and push new messages into our server. The server will
# tag them with the customer ID and metadata about colection. All this, and the
# results of parsing will then be stored in a mongdb database. Triggers ill be
# set up so that when corrolations occur, indicating a problem, an alert will be
# pushed to another app  that will be used to display status. This will probably
# use some kind of pub / sub message queue, possibly rabbit.

# We also want to do analysis on the parsed results as they come in to determin
# the kind of event they represent. this needs to be abased on conditional logic
# that asserts new values based on existing ones. An example of this might be an
# integer value being resolved to 'ok','serious', and 'critical', which would be
# asserted into metadata, or transformed in the message, so that it can become
# part of the analysis.

# Any language needs only act on JSON, so can use JQ syntax. 
# .path == value 
# .path contains value
# .path[] contains value
# .path[n] [== | > | <] value 
# .path [== | > | <]
# 
# A statement myight look like if .access == 'denied' assert risk_level = critical

# Perhaps this is a more long term goal. Mayne to start with we just store the
# parsed results in a database.


# mongodb://mongodb:27017 

from pymongo import MongoClient
from bson.json_util import loads
import json
from time import sleep
from conversions import Converter
import threading


print("right at the start")

# Setup the interface to our database
client = MongoClient('mongodb://mongodb:27017')
msg_db = client['msg_db']['messages']
update_db = client['update']['messages']
cnv = Converter('rules')

sleep(1)

# TODO: Make this use native notfications instead of polling
def process_new_messages(number):
    msg_list = []
    print(f"processing new messages: {number}")
    rec = msg_db.find().sort('_id',-1).limit(number)
    for r in rec:
        print(r)
        msg = cnv.reformat(r)
        if msg is not None:
            msg_list.append(msg)
    return msg_list

def run_analiser():
    print("starting analyser")
    count = msg_db.count_documents({})
    print(f"running analyser : {count}")
    while True:
        tmp = msg_db.count_documents({})
        if tmp > count:
            msg_list = process_new_messages(tmp - count)

            # Update the reformated db
            for msg in msg_list:
                print(msg)
                msg.pop('_id',None)
                Json = json.dumps(msg)
                BJson = loads(Json)
                update_db.insert_one(BJson)

            count = tmp
        sleep(1)

def run_events():
    while True:
        pass

if __name__ == '__main__':
    print("==> doing something...<==")
    athread = threading.Thread(target=run_analiser, daemon=True)
    athread.start()
    athread.join()
    # run_analiser()

