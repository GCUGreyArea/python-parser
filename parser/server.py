#!/usr/bin/env python3

from flask import Flask,request
from framework import Framework
from pymongo import MongoClient
from bson.json_util import loads
from simple_query import exec_statement
from test_data.populate import init_mongo_db
import json

app = Flask(__name__)
f = Framework('rules')

# db connections
client = MongoClient('mongodb://mongodb:27017')


@app.route('/parse', methods=['POST'])
def parse():
   msg = request.form.get('message')
   meta = request.form.get('meta')

   messages = client['msg_db']['messages']

   mdict = json.loads(meta)
   # print(meta)

   Ret = None
   try: 
      Ret = f.parse_fragment(msg,'root:regex')
   except Exception as e:
      app.logging.error('Exception thrown')
      return '{"exception":' + e + '}'

   if Ret is not None:
      (p,t) = Ret
      Out = f.generate_output_map(p,t)

      Out.update(mdict)

      Json = json.dumps(Out)
      BJson = loads(Json)
      messages.insert_one(BJson)

      return Json
    
   return '{"match":"none"}'

@app.route('/query',methods=['POST'])
def query():
   messages = client['msg_db']['messages']
   updates  = client['msg_db']['updates']
   status   = client['msg_db']['status']

   # Connection map
   cn_map = {
      'messages' : messages,
      'updates'  : updates,
      'status'   : status
   }

   print("QUERY...")
   query = request.form.get('query')
   return exec_statement(query,'json', cn_map)

@app.route('/show', methods=['GET'])
def show():
   print("show...")
   return f.to_string()

@app.route('/populate', methods=['GET'])
def populate():
   init_mongo_db()
   return '{"status":"ok"}'


if __name__ == '__main__':
   # https://pythonspeed.com/articles/docker-connection-refused/
   print('Starting server')
   app.run(host='0.0.0.0',port=5000)