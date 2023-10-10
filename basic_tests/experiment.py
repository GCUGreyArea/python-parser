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
    

class JSONQuery:
    def __init__(self, q,c):
        self._query = json.loads(q)
        self._constraint = None
        if c is not None:
            self._constraint = json.loads(c)

    def run_query(self,db,table):
        tbl = db.lookup_table(table)
        if tbl is not None:
            if self._constraint is not None and self._query is not None:
                return tbl.find(self._query,self._constraint)
            elif self._query is not None:
                return tbl.find(self._query)

class DistinctQuery:
    def __init__(self,field):
        self._field = field

    def run_query(self,db,table):
        tbl = db.lookup_table(table)
        if tbl is not None:
            return tbl.distinct(self._field)

class Query:
    def __init__(self,qlist,clist):
        self._qlist = qlist
        self._clist = clist
        self._query = self._render_query()
        self._constraint = self._render_constraint()

    def _render_query(self):
        querry = {}

        for q in self._qlist:
            querry.update(q.generate())

        return querry
    
    def _render_constraint(self):
        constraint = {}

        for c in self._clist:
            constraint.update(c.generate())

    def query(self):
        return self._query
    
    def run_query(self, tbl):
        return tbl.find(self._query)
    

# class ListValues:
#     def __init__(self,field):
#         self._field = field

#     def run_query(self,db,tbl):
#         table = db.lookup_table(tbl)

# There should only ever be one of these. Probably need to make this a singleton object!  
class DB:
    def __init__(self):
        self._connection = pymongo.MongoClient('mongodb://localhost:27017/?directConnection=true')
        self._messages = self._connection['msg_db']['messages']
        self._updates  = self._connection['msg_db']['updates']
        self._status   = self._connection['msg_db']['status']
        self._lookup = {'messages' : self._messages,'updates':self._updates,'status':self._status}

    # def messages(self):
    #     return self._messages
    
    # def updates(self):
    #     return self._updates

    # def status(self):
    #     return self._status
    
    def lookup_table(self, tbl):
        return self._lookup[tbl]
    
    # def run_query(self,table,query,constraint = None):
    #     try:
    #         tbl = self._lookup[table]
    #         if constraint is not None:
    #             return tbl.find(query,constraint)
    #         else:
    #             return tbl.find(query)
    #     except:
    #         print("failed badly")
    #         return None

# Call is_float first, then is_int otherwise you'll get a bad result!
def is_float(st):
    if re.match('\d+\.\d+$',st):
        return True
    
    return False

def is_int(st):
    if re.match('\d+$',st):
        return True
    
    return False

# Get the value for a JSON query, this is the native format for a MongoDB query
#  format 
#     using <collection> <query name> <query> constrain <constraint> aggregate ;
#     using <collection> <query name> <query> constrain <constraint> ;
#     using <collection> <query name> <query> aggregate ;
#     using <collection> <query name> <query> ; 

def get_json_query(st):
    r = re.compile(R'^using (?P<table>[a-z]+) (?P<query>[a-z][a-z0-=9\_]+)\s+(?P<expression>\{\"[a-z\_]+\"\s*\:\s*.*})\s*(constraint (?P<constraint>\{\"[a-z\_]+\"\s*\:\s*.*}) (?P<aggregate>(aggregate)*))*\s*;$')
    m = r.match(st)
    if m:
        it = r.groupindex.items()
        if len(it) < 3:
            return None
        
        table = None
        qname = None
        qvalue = None
        aggregate = None
        constraint = None
        for name, index in it:
            val = m.group(index)
            if table == None and name == 'table':
                table = val
            elif qname == None and name == 'query':
                qname = val
            elif qvalue == None and name == 'expression':
                qvalue = val
            elif aggregate == None and name == 'aggregate':
                aggregate = val
            elif constraint == None and name == 'constraint':
                constraint = val
            else: 
                print(f"bad query {st}")
                return None

        return (table,qname,JSONQuery(qvalue,constraint),aggregate)
    
    return None

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
    # check if this is a json query
    ret = get_json_query(st)

    if ret is not None:
        (table,query,q,aggregate) = ret
        return (table,query,q,aggregate)


    return None

    # otherwise parse it
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
                raise ValueError('agregate can only be applied at the end of a query: "using" "table" "query name" query "aggregate"')
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

# We need to ad this function into Query so that things can be abstracted out!
def run_single_query(table,q):
    l = []
    d =  DB()
    res = q.run_query(d,table)
    for m in res:
        m.pop('_id',None)
        l.append(m)

    return l

def main(json_fmat,st):

    # d = DB()

    # l = []
    # res = d.run_query('messages',{'client_id':3},{'_id':0,'rule':1,'tokens.file':1})
    # for m in res:
    #     l.append(m)

    #     map = {'metadata':{}}
    #     for r in l:
    #         map = aggregate_results(r,map)
    # return map

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
        if json_fmat == 'json':
            return json.dumps(l)
        return l

if __name__ == "__main__":
        ret = None
        if len(sys.argv) == 3:
            ret = main(sys.argv[1], sys.argv[2])
        else:
            ret= main('no',sys.argv[1])
        print(ret)
