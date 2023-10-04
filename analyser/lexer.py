#!/usr/bin/env python3

import ply.lex as lex
import sys
import re

# list of tokens 
tokens = (
    'IF',
    'THEN',
    'ELSE',
    'AND',
    'OR',
    'INT',
    'FLOAT',
    'OBJECT',
    'EQUALS',
    'ADD',
    'SUBTRACT',
    'MULTIPLY',
    'DIVIDE',
    'MODULO',
    'IS_IN',
    'IS_EQUAL_TO',
    'IS_GREATER_THAN',
    'LESS_OR_EQUAL',
    'GREATER_OR_EQUAL',
    'IS_LESS_THAN',
    'CONTAINS',
    'STRING',
    'VARIABLE'
)

# resewrved words in our limited language   ``
reserved = {
   'if'         : 'IF',
   'then'       : 'THEN',
   'else'       : 'ELSE',
   'contains'   : 'CONTAINS',
   'in'         : 'IS_IN',
   'and'        : 'AND',
   'or'         : 'OR',
   'assert'     : 'ASSERT'
}

# The statement has to differentiate between words in the 'reserved list and an
# 'object'. An object, in this language, is something that is acted on in a
# statement, so in the statement 'if some.value == "three"' some.value is the
# object "three" is a string, which is distinct.
def t_STATEMENT(t):
    r'[a-zA-Z_][a-zA-Z_0-9\_\-\.]*'
    try:
        type = reserved[t.value]
        t.value = (t.value,type)
        t.type = type
        return t
    except KeyError:
        t.value = (t.value,'OBJECT')
        t.type = 'OBJECT'
        return t

t_FLOAT = r'\d+\.\d+'
t_INT = r'\d+'
t_LESS_OR_EQUAL = r'<='
t_GREATER_OR_EQUAL = r'>='
t_EQUALS = r'='
t_SUBTRACT = r'-'
t_MULTIPLY = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'
t_IS_EQUAL_TO = r'=='
t_IS_GREATER_THAN = r'>'
t_IS_LESS_THAN = r'<'
t_STRING = r'\"[^\"]*\"'
t_VARIABLE = r'\$.+'

# Do nothing with white spaces
t_ignore  = ' '

# skip ileagal characters???
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Test the lexer
def main(st):
    lexer = lex.lex()
    lexer.input(st)
    while True:
        tok = lexer.token()
        if not tok: 
            break      # No more input
        print(tok)


# but only if run from the command line
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("please supply a string to parse")
    else:
        main(sys.argv[1])
