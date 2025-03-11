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

# SOL25 Grammar
SOL25 = """
    program: class+
    
    class: "class" CLASS_NAME ":" CLASS_NAME "{" method* "}"
    
    method: selector block

    selector: VAR | (VAR ":")+
    
    block: "[" parameter* "|" statement* "]"

    parameter: ":" VAR
    
    statement: VAR ":=" expression "."
    
    expression: exprbase  exprtail
    
    exprbase: literal | VAR | "(" expression* ")"

    exprtail: VAR | exprsel

    exprsel: (VAR ":" exprbase)*
    
    literal: INTEGER | STRING | CLASS_NAME | block | "true" | "false" | "nil" | "self" | "super"
    
    // Tokens
    KEYWORD: "class" | "self" | "super" | "nil" | "true" | "false"
    BUILT_IN_CLASS: "Object" | "Nil" | "True" | "False" | "Integer" | "String" | "Block"
    CLASS_NAME: /[A-Z][a-zA-Z0-9]*/
    VAR: /[a-z_][a-zA-Z0-9_]*/
    INTEGER: /[+-]?[0-9]+/
    STRING: /'([^'\\\\]|\\\\.|\\n)*'/
    
    // Comments
    COMMENT: /"[^"]*"/
    %ignore COMMENT
    
    // Whitespace
    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = lark.Lark(SOL25, start="program", parser="lalr")

# Convert the AST to an XML element
def ast_to_xml(ast):
    """Recursively converts a Lark AST to an XML element."""
    if isinstance(ast, lark.Tree):
        element = ET.Element(ast.data)
        for child in ast.children:
            element.append(ast_to_xml(child))
        return element
    elif isinstance(ast, lark.Token):
        element = ET.Element("token", type=ast.type)
        element.text = ast.value
        return element
    return None


# Parse the input file and convert to XML
try:
    ast = parser.parse(file)
    xml_root = ast_to_xml(ast)

    # Convert to a formatted XML string
    xml_string = ET.tostring(xml_root, encoding="utf-8").decode("utf-8")

    print(xml_string)  # Output XML to stdout

except lark.exceptions.LarkError as e:
    print(f"ERROR: Parsing failed: {e}", file=sys.stderr)
    sys.exit(1)


