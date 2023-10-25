#!/usr/bin/env python3

from flask import Flask,request
from framework import Framework
from pymongo import MongoClient
from bson.json_util import loads
from simple_query import exec_statement
import json

app = Flask(__name__)
f = Framework('rules')
client = MongoClient('mongodb://mongodb:27017')
db = client['msg_db']['messages']


@app.route('/parse', methods=['POST'])
def parse():
   msg = request.form.get('message')
   meta = request.form.get('meta')

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
      db.insert_one(BJson)

      return Json
    
   return '{"match":"none"}'

@app.route('/query',methods=['POST'])
def query():
   print("QUERY...")
   query = request.form.get('query')
   return exec_statement(query,'json', client)

@app.route('/show', methods=['GET'])
def show():
   print("show...")
   return f.to_string()

if __name__ == '__main__':
   # https://pythonspeed.com/articles/docker-connection-refused/
   print('Starting server')
   app.run(host='0.0.0.0',port=5000)