#!/usr/bin/env python3

# This is an example for a basic parsing system for MongoDB queries for the
# existing collections in msg_db 

import json
import sys
import re
import pymongo

class JSONQuery:
    def __init__(self, table, query, constraint):
        self._table = table
        self._query = json.loads(query)
        self._constraint = None
        if constraint is not None:
            self._constraint = json.loads(constraint)

    def run_query(self, db):
        try:
            tbl = db.lookup_table(self._table)
            if self._constraint is not None and self._query is not None:
                return tbl.find(self._query,self._constraint)
            elif self._query is not None:
                return tbl.find(self._query)
        except KeyError:
            raise ValueError(f'unknown table {self._table}')


class DistinctQuery:
    def __init__(self, table, field):
        self._field = field
        self._table = table

    def run_query(self,db):
        tbl = db.lookup_table(self._table)
        return [{self._field : tbl.distinct(self._field)}]

class DB:
    def __init__(self, db_ref):
        self._connection = db_ref
        self._lookup = {
            'messages' : self._connection['msg_db']['messages'],
            'updates'  : self._connection['msg_db']['updates'],
            'status'   : self._connection['msg_db']['status']
        }

    def lookup_table(self, tbl):
        return self._lookup[tbl]
    
# tokanise to a list of strings and JSON content and split them into a list of
# found objects using a basic state machine
def isolate_json_or_string(st):
    json_stack = []
    str_stack = []
    word = ""
    ignore = False
    l = len(st)
    words = []
    for c in st:
        if ignore:
            word += c
            ignore = False
            continue
        elif c == '"' and len(json_stack) > 0:
            word += c
            continue
        elif c == '"' and len(str_stack) == 0:
            if len(str_stack) == 0:
                if word != '':
                    words.append(word)
                    word = ''
                str_stack.append(c)
                word += c
            else:
                word += c
        elif c == '\\':
            # ignore the next character whatever it is
            ignore = True
            continue
        elif (c == '{' or c == '['):
            if word != '' and len(json_stack) == 0:
                words.append(word)
                word = ''
            json_stack.append(c)
            word += c
        elif len(json_stack) > 0 and (c == '}' or c == ']'):
            json_stack.pop()
            word += c
            if len(json_stack) == 0:
                words.append(word)
                word = ''
        elif c == ' ' and len(json_stack) == 0 and len(str_stack) == 0:
            if word != '':
                words.append(word)
                word = ''
        else:
            word += c
    
    if word != '':
        words.append(word)

    return words

# parse the query string using a stae machine
def parse_string(st):
    words = isolate_json_or_string(st)
    
    qname_regex = r'[a-z][a-z0-9\_]*'
    exp_regex = r'\{\"[a-z\_\.\{\}\[\]]+\"\:.*\}'
    collect_regex = r'messages|updates|status'

    collection = None
    query = None
    expression = None
    aggregate = False
    constraint = None
    field = None
    expect = ''
    pos = 0
    for word in words:
        if word == 'using':
            expect = 'collection'
            continue
        elif expect == 'collection':
            if re.match(collect_regex,word) is None:
                raise ValueError(f'unexpected token {word}')
            collection = word
            expect = 'query'
            continue
        elif expect == 'query':
            if re.match(qname_regex,word) is None:
                raise ValueError(f'unexpected token {word}')
            query = word
            expect = 'expression | sum'
        elif expect == 'expression | sum':
            if word == 'sum':
                expect = 'field'
                continue
            elif re.match(exp_regex,word) is None:
                raise ValueError(f'unexpected token {word}')
            expression = word
            expect = 'constraint | aggregate | end'
        elif expect == 'constraint | aggregate | end':
            if word == 'constraint':
                expect = 'const_expre'
                continue
            elif word == 'aggregate':    
                aggregate = True
                expect = 'end'
                continue
            elif word == ';':
                break
            else:
                raise ValueError(f'unrecognised token {word}')
        elif expect == 'const_expre':
            constraint = word
            expect = 'aggregate | end'
            continue
        elif expect == 'aggregate | end':
            if word == 'aggregate':
                if aggregate == False:
                    aggregate = True
                else: 
                    raise ValueError(f'aggregate has already been set: possition {pos}')
                expect = 'end'
                continue
            elif word == ';':
                break
        elif expect == 'field':
            field = word
            expect = 'end'
            continue
        elif expect == 'end':
            if word != ';':
                raise ValueError(f'unexpected token: {word}')
            break
        else:
            raise ValueError(f'unexpected token {word}')

    # return the appropriate type of query as a python object that can be
    # executed
    if expression != None:
        print(f'expression : "{expression}", constraint : "{constraint}"')
        return (query,JSONQuery(collection,expression,constraint),aggregate)
    else:
        return (query,DistinctQuery(collection,field),False)



# The goal of this function is to deduplicate entries and create a results map
#   1. for all duplicate ewntries, create a metadata entry counting the number
#      of duplicates in the form {'metadata' : {'field.value' : count}}
#   2. where there is a new value for an existing field, cheange the entry to a
#      list and add all entries, in the form {'field' : [value1,value2]}
#   3. flatten the map so that all values can be counted in meta as jq paths as
#      {'.name1.name2.name3' : count} this alows direct search for the value of
#      '.name1.name2.name3' without having to travers a JSON object
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

# Get the value for a JSON query, this is the native format for a MongoDB query
#  format 
#     using <collection> <query name> <query> constrain <constraint> aggregate ;
#     using <collection> <query name> <query> constrain <constraint> ;
#     using <collection> <query name> <query> aggregate ;
#     using <collection> <query name> <query> ; 

def exec_statement(st,json_fmat, db_ref):
    (qname, q, aggregate) = parse_string(st)

    db = DB(db_ref)
    l = []
    res = q.run_query(db)

    # print(res)

    for r in res:
        # remove becaus ethis will not serialise to JSON
        print(r)
        r.pop("_id",None)
        l.append(r)
    
    if aggregate and len(l) > 0:
        map = {'metadata':{}}
        for r in l:
            aggregate_results(r,map)    
                
        l = map

    elif len(l) == 1:
        l = l[0]

    l = {qname:l}
    
    if json_fmat:
        return json.dumps(l)
        
    return l

if __name__ == "__main__":
    if sys.argv[1] == 'json':
        print(exec_statement(sys.argv[2],True))
    else:
        print(exec_statement(sys.argv[2],False))
