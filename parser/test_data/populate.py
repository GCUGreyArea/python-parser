#!/usr/bin/env python3

import pymongo

def init_mongo_db():
  print("opening mongodb")

  # connect to your Atlas cluster
  client = pymongo.MongoClient('mongodb://mongodb:27017')

  # Setup the databases and documents, deleting any content first so that we can
  # use this script to initialise each time we want to run a test
  messages = client['msg_db']['messages']
  messages.delete_many({})
  messages.insert_many([{
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "Aug  8 11:26:11",
      "machine": "DESKTOP-TJR7EI0",
      "component": "kernel driver",
      "action": "ileagal access request",
      "file": "/opt/dev/device"
    },
    "client_id": 3
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "Aug  8 12:31:25",
      "machine": "DESKTOP-TJR7EI0",
      "notification": "ilegal loggin attempt",
      "port": 223,
      "src_ip_addr": "172.16.0.12",
      "target_ip_addr": "192.168.20.31",
      "user": "vn_21",
      "status": "login attempt failed"
    },
    "client_id": 3
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "Aug  8 13:42:18",
      "machine": "system-server",
      "component": "kernel driver",
      "file": "/opt/dev/special",
      "action": "new device started"
    },
    "client_id": 1
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "Aug  8 12:25:11",
      "machine": "DESKTOP-TJR7EI0",
      "component": "user management",
      "access": "access granted",
      "src_ip_addr": "172.17.0.12"
    },
    "client_id": 3
  }])


  updates = client['msg_db']['updates']
  updates.delete_many({})
  updates.insert_many([{
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "08/08/2023 11:26:11",
      "machine": "DESKTOP-TJR7EI0",
      "component": "kernel driver",
      "action": "ileagal access request",
      "file": "/opt/dev/device"
    },
    "client_id": 3
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "08/08/203 12:31:25",
      "machine": "DESKTOP-TJR7EI0",
      "notification": "ilegal loggin attempt",
      "por": 223,
      "src_ip_addr": "172.16.0.12",
      "target_ip_addr": "192.168.20.31",
      "user": "vn_21",
      "status": "login attempt failed"
    },
    "client_id": 3
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "08/08/2023 13:42:18",
      "machine": "system-server",
      "component": "kernel driver",
      "device": "/opt/dev/special",
      "action": "new device started"
    },
    "client_id": 1
  },
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "08/08/2023 12:25:11",
      "machine": "DESKTOP-TJR7EI0",
      "component": "user management",
      "access": "access granted",
      "src_ip_addr": "172.17.0.12"
    },
    "client_id": 3
  }])

  status = client['msg_db']['status']
  status.delete_many({})
  status.insert_many([{
    "client_id": 3,
    "failed_logins": 1,
    "status": 1
  },
  {
    "client_id": 1,
    "breach_count": 0,
    "status": 0
  }])

  print("done")

init_mongo_db()

