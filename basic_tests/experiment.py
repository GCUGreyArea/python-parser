#!/usr/bin/env python3

import pymongo
from lexer import tokens
import sys
import re
import json

class SimpleQuery:
    def __init__(self, field, value):
        self._field = field
        self._value = value

    def generate(self):
        return {self._field : self._value}


class RegexQuery:
    def __init__(self,field,regex):
        self._field = field
        self._regex = regex

    def generate(self):
        return {self._field : {"$regex": self._regex}}

class Query:
    def __init__(self,qlist):
        self._qlist = qlist
        self._query = self._render()

    def _render(self):
        querry = {}

        for q in self._qlist:
            querry.update(q.generate())

        return querry

    def query(self):
        return self._query

# There should only ever be one of these. Probably need to make this a singleton object!  
class DB:
    def __init__(self):
        self._connection = pymongo.MongoClient('mongodb://localhost:27017/?directConnection=true')
        self._messages = self._connection['msg_db']['messages']
        self._updates  = self._connection['msg_db']['updates']
        self._status   = self._connection['msg_db']['status']
        self._lookup = {'messages' : self._messages,'updates':self._updates,'status':self._status}

    def messages(self):
        return self._messages
    
    def updates(self):
        return self._updates

    def status(self):
        return self._status
    
    def run_query(self,table,query):
        try:
            tbl = self._lookup[table]
            return tbl.find(query)
        except:
            print("failed badly")
            return None

# Call is_float first, then is_int otherwise you'll get a bad result!
def is_float(st):
    if re.match('\d+\.\d+$',st):
        return True
    
    return False

def is_int(st):
    if re.match('\d+$',st):
        return True
    
    return False

# This will be replaced with a proper parser
# this is a development framework to define the language!
def split_ignore_strings(st):
    string = False
    words = []
    word = ''
    for c in st:
        if c == '"':
            # end of string
            if string:
                words.append(word + '"')
                word = ''
                string = False
                continue
            # start of string
            else:
                string = True
                word += '"'
                continue
        # space in the string deliniates a word
        elif c == ' ':
            # keep going if this is a string
            if string:
                word += c
                continue
            else:
                # otherwise save the words and move on. However, at the end of
                # strings the word varaible will be empty so ignore
                if word != '':
                    words.append(word)
                    word = ''
                continue
        # normal alpha numeric character
        else:
            word += c

    if word != '':
        words.append(word)

    return words

# Parse a string into a query that can be executed on the database
# This will be replaced with a proper parsers at some point!
def parse(st):
    # query elements
    table = None
    query = None
    agregate = False
    qlist = []
    ret  = []

    # get a list split by spacing and iterate through it
    # Note: the query string has already been mnormalised so that all spaces equate to 1 other than for 
    # strings? So this won't work for that! 
    l = split_ignore_strings(st)
    # print(l)
    place = 0
    length = len(l)
    while place < length:
        adj = l[place]
        place+=1
        if adj == "and":
            continue
        # agergate should come at the end of the statement
        elif adj == 'aggregate':
            if place == length:
                agregate = True
                return (table,query,Query(qlist),agregate)
            else:
                raise ValueError('agregate can only be applied at the end of a query: "using" "table" "query name" query "agregate"')
        obj = l[place]
        place+=1
        verb = l[place]
        place+=1

        # assemble the objects
        if adj == "using":
            table = obj
            query = verb
            continue
        elif obj == 'is':
            cnv = None
            if is_float(verb):
                cnv = float(verb)
            elif is_int(verb):
                cnv = int(verb)
            else:
                cnv = verb[1:-1]

            qlist.append(SimpleQuery(adj,cnv))
            continue
        elif obj == 'like':
            qlist.append(RegexQuery(adj,verb[1:-1]))
            continue

    # table = name of table to use 
    # query = name of the map to save results in 
    # ret = list of queries to run
    # agregate = agregate the results into a single map with metadata
    return (table,query,Query(qlist),agregate)

# Used by format_results
def _inc_metadata_for_value(label,value,meta):
    meta_label = f'{label}.{value}'

    try:
        count = meta[meta_label]
        count += 1
    except KeyError:
        meta[meta_label] = 1

# The goal of this function is to deduplicate entries and create a results map
#   1. for all duplicate ewntries, create a metadata entry counting the number
#      of duplicates in the form {'metadata' : {'field.value' : count}}
#   2. where there is a new value for an existing field, cheange the entry to a
#      list and add all entries, in the form {'field' : [value1,value2]}
#   3. flatten the map so that all values can be counted in meta as jq paths as {'.name1.name2.name3' : count}
# def aggregate
def _aggregate_results(meta_label,label,map,results):
    # value is result map so lable is guarenteed
    val = map[label]

    if isinstance(val,dict):
        ml = meta_label + '.' + label
        for l in val:
            results = _aggregate_results(ml,l,val,results)
        return results

    meta = results['metadata']

    # deal wit hhte metadata entry
    lb = meta_label + '.' + label + '.' + str(val)
    try:
        count = meta[lb]
        count +=1
        meta[lb] = count 
    except KeyError:
        count = 1
        meta[lb] = count

    # now add back to the results
    ml = meta_label + '.' + label
    try:
        val_res = results[ml]
        if isinstance(val_res,list):
            if val not in val_res:
                val_res.append(val)
        elif val != val_res:
            results[ml] = [val_res,val]
    except KeyError:
        results[ml] = val

    return results

def aggregate_results(map,results):
    for label in map:
        results = _aggregate_results('',label,map,results)

    return results

def run_single_query(table,q):
    l = []
    d =  DB()
    res = d.run_query(table,q.query())
    for m in res:
        m.pop('_id',None)
        l.append(m)

    return l

def main(json_fmat,st):
    # print(st)
    # print(json_fmat)
    (t,n,q,a) = parse(st)

    l = run_single_query(t,q)

    if a:
        map = {'metadata':{}}
        for r in l:
            map = aggregate_results(r,map)

        if json_fmat == 'json':
            return json.dumps(map)
        return map
    else:
        return l

if __name__ == "__main__":
        ret = main(sys.argv[1], sys.argv[2])
        print(ret)
