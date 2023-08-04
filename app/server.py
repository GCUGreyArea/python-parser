#!/usr/bin/env python3

from flask import Flask,request
from parse import parse_message
from framework import Framework


app = Flask(__name__)
f = Framework('rules')

@app.route('/parse', methods=['POST'])
def parse():
   msg = request.form.get('message')

   Ret = None

   try: 
      Ret = f.parse_fragment(msg,'root:regex')
   except Exception:
      app.logging.error('Exception thrown')

   if Ret is not None:
      (p,t) = Ret
      return f.generate_json_output(p,t)
    
   return '{"match":"none"}'

if __name__ == '__main__':
   # https://pythonspeed.com/articles/docker-connection-refused/
   app.logger.info('Starting server')
   app.run(host='0.0.0.0',port=5000)