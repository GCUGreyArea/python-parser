#!/usr/bin/env python3

from lexer import tokens
import ply.yacc as yacc
from experiment import RegexQuery, SimpleQuery, Query

# Need to differentiate between databases and documents! 
def p_regex_expression(p):
    'REGEX_EXPRESSION : OBJECT LIKE STRING'
    p[0] = RegexQuery(p[1],p[2])

def p_simple_expression(p):
    'SIMPLE_QUERRY : OBJECT IS INT | OBJECT IS FLOAD | OBJECT IS STRING'
    p[0] = SimpleQuery(P[1],p[2])


