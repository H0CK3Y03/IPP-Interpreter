#!/usr/bin/env python3

import sys # for parsing CLI arguments
import lark # for parsing the grammar
import xml.etree.ElementTree as ET # for parsing the XML

# ================== Handle CLI arguments ==================

if "--help" in sys.argv or "-h" in sys.argv:
    # Only one argument with --help or -h
    if(len(sys.argv) == 2):
        print("Usage: ./parse.py < \"source-code\"")
        sys.exit(0)
    else:
        print("ERROR: Cannot combine --help or -h with other arguments")
        sys.exit(10)
elif len(sys.argv) > 2:
    print("ERROR: Too many arguments")
    sys.exit(10)

# ================== Handle CLI arguments ==================

# Store stdin in a variable
file = sys.stdin.read()

SOL25 = """
    program: class+
    
    class: "class" CLASS_NAME ":" CLASS_NAME "{" method* "}"
    
    method: selector block

    selector: VAR | (VAR ":")+
    
    block: "[" parameter* "|" statement* "]"
    
    statement: VAR ":=" expression "."
    
    expression: literal | VAR | send | "(" expression* ")" | "true" | "false" | "nil" | "self" | "super"
    
    send: selector expression*
    
    parameter: ":" VAR
    
    literal: INTEGER | STRING | CLASS_NAME | block
    
    // Tokens
    KEYWORD: "class" | "self" | "super" | "nil" | "true" | "false"
    BUILT_IN_CLASS: "Object" | "Nil" | "True" | "False" | "Integer" | "String" | "Block"
    CLASS_NAME: /[A-Z][a-zA-Z0-9]*/
    VAR: /[a-z_][a-zA-Z0-9_]*/
    INTEGER: /[+-]?[0-9]+/
    STRING: /'([^'\\]|\\\\|\\n|\\')*'/
    
    // Comments
    COMMENT: /"[^"]*"/
    %ignore COMMENT
    
    // Whitespace
    %import common.WS
    %ignore WS
"""

parser = lark.Lark(SOL25, start="program", parser="lalr")

print(parser.parse(file).pretty())


