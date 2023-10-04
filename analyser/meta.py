#!/usr/bin/env python3

from analyser_yaml import load_yaml
import sys
import re

class Meta: 
    def __init__(self, map):
        try:
            self._uuid = map['id']
        except KeyError:
            raise ValueError("metadata rule must have a unique uuid")
        
        try: 
            tbl = map['tables']
            self._process_tables(tbl)
        except KeyError:
            pass

        statements = [] 
        try:
            statements = map['statements']
        except KeyError:
            raise ValueError(f"matadata definition {self._uuid} has no statements")

        self._compile_statements(statements)

    def _process_tables(self,tbls):
        self._tbls = {}
        for tbl in tbls:
            s = set()
            name = ''
            try:
                name = tbl['name']
            except KeyError:
                raise ValueError("Each table definition needs to have a name")
            
            values = []
            try:
                values = tbl['values']
            except KeyError:
                raise ValueError(f"Table {name} has not values section")
            
            self._tbls[name] = s
            for v in values:
                s.add(v)

    def _compile_statements(self,statements):
        self._st_list = []
        for st in statements:
            norm = self._normalise_statement(st)
            print(f"Normalised : {norm}")
            self._st_list.append(norm)

        print(f"num statements {len(self._st_list)}")


    # We want to reduce all spaces to 1 and remove newlies and tabs, but only if
    # they are not part of a string
    def _normalise_statement(self,state):
        try:
            st = state['statement']
            nst = ""
            l = len(st)
            p = 0
            skip = False
            space_count = 0
            while p < l:
                c = st[p]
                p += 1
                if c == '"':
                    if skip == False:
                        skip == True
                    else: 
                        skip == False
                if skip == False:                
                    if c == '\n':
                        continue
                    elif c == '\t': 
                        continue
                    elif c == ' ':
                        if space_count == 1: 
                            continue
                        space_count += 1
                    else:
                        space_count = 0

                    nst += c
            return nst
               
        except KeyError:
            raise ValueError(f"statements needs to contain at least one statement {state}")


def main(dir):
    yaml = load_yaml(dir)
    # print(f"reading drectory {dir}")
    # print(f"loading {yaml[0]}")
    Meta(yaml[0])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("please supply a directory to parse")
    else:
        main(sys.argv[1])
