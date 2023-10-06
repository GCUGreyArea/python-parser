#!/usr/bin/env python3


import ply.yacc as yacc
from lexer import tokens

# Grammar 

# STATEMENT := IF EXP THEN EXP
# COMP_OB := INT | FLOAT | STRING | OBJECT
# SEP := EQUALS | PLUS_EQUALS | MINUS_EQUALS | MUL_EQUALS 
# EXP := COMP_OBJ SEP COMP_OB
# COMPLEX_EXP := EXP | EXP AND EXP | EXP OR EXP  
