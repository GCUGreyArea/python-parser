#!/usr/bin/env python3

import sys
import os
import re
import copy
from analyser_yaml import load_yaml


class Eval:
    def __init__(self,list):
        # has the format (low,high,value)
        self._list = []
        for map in list:
            try: 
                r = map['range']
                m = map['map']
                self._list.append((r[0],r[1],m))
            except KeyError as e:
                raise ValueError(f"evaluation rule must contain \"range\" and \"map\"")
    
    def exec(self,n):
        print("Eval")
        for (low,high,map) in self._list:
            if n >= low:
                if n <= high:
                    return map

class Subs:
    def __init__(self,map):
        self._map = map

    def exec(self,n):
        try:
            return self._map[n]
        except KeyError:
            raise ValueError(f"map does not contain {n}")

class Refmat:
    def __init__(self,t):
        self._to_type = t

    def exec(self,n):
        if isinstance(n,str):
            if self._to_type == "int":
                return int(n)
        elif isinstance(n,int):
            if self._to_type == "str":
                return str(n)
        
        return n

class Update:
    def __init__(self, ptn):
        self._ptn = ptn

    def make_string(self,values):
        place = 0
        st = copy.copy(self._ptn)
        while place < len(values):
            tag = "$" + str(place+1)
            v = ''
            if isinstance(values[place],int):
                v = str(values[place])
            else:
                v = values[place]
            st = st.replace(tag,v)
            place += 1

        return st


class Rule: 
    def __init__(self,map):
        self._uuid = map['id']
        self._map_ids = [] 
        self._update = None
        
        for id in map['patterns']:
            self._map_ids.append(id)
        self._field = map['field']
        try:
            self._regex = re.compile(map['regex'])
            try: 
                update = map['update']
                self._update = Update(update['pattern'])
            except KeyError:
                raise ValueError(f"regex rule must have an update section")
        except KeyError:
            self._regex = None

        cnv = map['conversions']
        self._cnv = {}
        for c in cnv:
            count = 0
            for field,action in c.items():
                # This is a hack! There should only be one of these!
                count += 1
                if count > 2:
                    raise ValueError(f"bad rule {self._uuid}")

                try: 
                    sub_map = action["substitute"]
                    self._cnv[field] = Subs(sub_map)
                    continue
                except KeyError:
                    pass

                try:
                    eval = action["evaluate"]
                    self._cnv[field] = Eval(eval)
                    continue
                except KeyError:
                    pass

                try:
                    refmat = action["reformat"]
                    self._cnv[field] = Refmat(refmat)
                except KeyError: 
                    raise ValueError(f"rule must contain either a \"substitute\", an \"evaluate\", or a \"reformat\" directive")

    def uuid(self):
        return self._uuid   
    
    def map_id(self):
        return self._map_ids
    
    # Rempa will take the token and, 
    # if it is a compound token, use a regex 
    # to break it down further then transform the 
    # message text usign the transformation pattern 
    # declared in the rules .YAML file
    def reformat(self,map):
        tkns = map['tokens']
        t = tkns[self._field]
        if self._regex is not None:
            m = self._regex.match(t)
            values = []
            # collect the values for the updater
            if m:
                for name, index in self._regex.groupindex.items():
                    v = None
                    val = m.group(index)
                    try:
                        v = self._cnv[name].exec(val)
                    except KeyError:
                        v = val

                    values.append(v)

                # update the token value
                print(f"values {values}")
                tkns[self._field] = self._update.make_string(values)
        else:
            r = self._cnv[self._field] 
            tkns[self._field] = r.exec(t)
        

class Converter:
    def __init__(self,dir):
        # Find all flies that end in "yaml" and who's names are a mix of letters and numbers
        Files = [
            os.path.join(dp, f)
            for dp, dn, fn in os.walk(os.path.expanduser(dir))
            for f in fn
            if re.match(r"[\w\d]+\.yaml", f)
        ]

        if len(Files) == 0:
            raise ValueError(f"no yaml files found in {dir}")
        
        for File in Files:
            self.get_conversion_rule(File)

    def get_conversion_rule(self,file):
        self._rules = {}
        rules = load_yaml(file)
        for rule in rules: 
            r = Rule(rule)
            for id in r.map_id():
                try:
                    rlist = self._rules[id]
                    rlist.append(r)
                except KeyError:
                    l = []
                    l.append(r)
                    self._rules[id] = l


    def reformat(self,msg):
        p = msg['pattern']
        if p is not None:
            print(f"found {p}")
        if isinstance(p,str):
            try:
                rlist = self._rules[p]
                for r in rlist:
                    r.reformat(msg)
            except KeyError:
                pass
        else:
            for ptn in p:
                try: 
                    rlist = self._rules[ptn]
                    for r in rlist:
                        r.reformat(msg)
                except KeyError:
                    pass
        return msg

def main(dir):
    print(f"reading drectory {dir}")
    c = Converter(dir)
    msg = {"rule": "b489a151-6e84-43ce-86d2-40e21791b26b", "pattern": "11d83e62-4b21-4dd5-bc67-d56eab522686", "tokens": {"date": "Jun  8 11:26:11", "machine": "DESKTOP-TJR7EI0", "component": "kernel", "file": "/var/logs/syslog", "state": "denied", "user": "barry", "level": 5}}
    
    print(f"msg 1: {msg}")
    msg = c.reformat(msg)
    print(f"msg 2: {msg}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("please supply a directory to parse")
    else:
        main(sys.argv[1])
