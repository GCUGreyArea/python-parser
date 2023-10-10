#!/usr/bin/env python3


# import json
import sys
import re

# Parse out strings and JSON content and split them into a list of found objects
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
        elif c == '"' and len(json_stack) == 0:
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
        elif c == '"' and len(str_stack) > 0:
            # end of a string
            word += c
            words.append(word)
            word = ''
        elif c == '{' or c == '[':
            if word != '':
                words.append(word)
                word = ''
            json_stack.append(c)
            word += c
        elif c == '}' or c == ']':
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


def main(st):
    st = sys.argv[1]
    words = isolate_json_or_string(st)
    
    qname_regex = r'[a-z][a-z0-9\_]*'
    exp_regex = r'\{\"[a-z\_]+\"\:.*\}'
    collect_regex = r'messages|updates|status'


    collection = None
    query = None
    expression = None
    aggregate = False
    constraint = None
    expect = ''
    for word in words:
        if word == 'using':
            expect = 'collection'
            continue
        elif expect == 'collection':
            if re.match(collect_regex,word) is None:
                print(f'unexpected token {word}')
                break
            collection = word
            expect = 'query'
            continue
        elif expect == 'query':
            if re.match(qname_regex,word) is None:
                print(f'unexpected token {word}')
                break
            query = word
            expect = 'expression'
        elif expect == 'expression':
            if re.match(exp_regex,word) is None:
                print(f'unexpected token {word}')
                break
            expression = word
            expect = 'constraint | aggregate'
        elif expect == 'constraint | aggregate':
            if word == 'constraint':
                expect = 'const_expre'
                continue
            elif word == 'aggregate':    
                aggregate = True
                expect = 'end'
        elif expect == 'const_expre':
            constraint = word
            expect = 'aggregate | end'
            continue
        elif expect == 'aggregate | end':
            if word == 'aggregate':
                if aggregate == False:
                    aggregate = True
                else: 
                    print('aggregate has already been set')
                    break
                expect = 'end'
                continue
            elif word == ';':
                break
        elif expect == 'end':
            if word != ';':
                print('unexpected token')
                break
        else:
            print(f'unexpected token {word}')
            break

                        
    print(f'collection: "{collection}", query: "{query}", expression: "{expression}", constraint: "{constraint}", aggregate: "{aggregate}"')


# Get the value for a JSON query, this is the native format for a MongoDB query
#  format 
#     using <collection> <query name> <query> constrain <constraint> aggregate ;
#     using <collection> <query name> <query> constrain <constraint> ;
#     using <collection> <query name> <query> aggregate ;
#     using <collection> <query name> <query> ; 

if __name__ == "__main__":
    main(sys.argv[1])
