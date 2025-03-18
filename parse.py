# Author: Adam Vesely
# Login: xvesela00
# file: parse.py

#!/usr/bin/env python3

import sys # for parsing CLI arguments
import lark # for parsing the grammar
import xml.etree.ElementTree as ET # for parsing the XML
from xml.dom import minidom
import re

# ================== Handle CLI arguments ==================

if "--help" in sys.argv or "-h" in sys.argv:
    # Only one argument with --help or -h
    if(len(sys.argv) == 2):
        print("Usage: ./parse.py < \"source-code\"")
        sys.exit(0)
    else:
        print("ERROR: Cannot combine --help or -h with other arguments", file=sys.stderr)
        sys.exit(10)
elif len(sys.argv) > 2:
    print("ERROR: Too many arguments", file=sys.stderr)
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
    
    literal: INTEGER | STRING | CLASS_NAME | block
    
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
assign_order_index = 1
arg_order_index = 1
selector_string_control = ""
parameter_control = []

# Extract the first comment from the source code
def extract_first_comment(source_code):
    match = re.search(r'"([^"]*)"', source_code)  # Match first comment
    return match.group(1) if match else None

def get_selector_arity(selector_string):
    return selector_string.count(":")

def ast_to_xml(ast):
    global assign_order_index
    global arg_order_index
    global selector_string_control
    global parameter_control
    if isinstance(ast, lark.Tree):

        if ast.data == "program":
            root = ET.Element("program", language="SOL25")
            description = extract_first_comment(file)
            if description:
                root.set("description", description)
            for child in ast.children:
                root.append(ast_to_xml(child))
            return root
        
        elif ast.data == "class":
            class_element = ET.Element("class", name=ast.children[0], parent=ast.children[1])
            for method in ast.children[2:]:
                class_element.append(ast_to_xml(method))
            return class_element
        
        elif ast.data == "method":
            # Extract the 'selector' subtree
            selector_tree = ast.children[0]  # First child is 'selector'
            # Ensure it's a Tree and contains VAR tokens
            if isinstance(selector_tree, lark.Tree) and selector_tree.data == "selector":
                parameters = [child for child in ast.children[1].children if isinstance(child, lark.Tree) and child.data == "parameter"]
                selector_parts = [child for child in selector_tree.children if isinstance(child, lark.Token) and child.type == "VAR"]
                # Join them with ":" and append ":" at the end
                selector_string = ":".join(token.value for token in selector_parts) + ":"
            else:
                selector_string = ""  # Default if no selector is found
            selector_string_control = selector_string
            # Create the <method> XML element
            if len(selector_parts) == 1 and len(parameters) == 0:
                method_element = ET.Element("method", selector=selector_parts[0].value)
                selector_string_control = selector_parts[0].value
            else:
                method_element = ET.Element("method", selector=selector_string)

            if len(parameters) != get_selector_arity(selector_string_control):
                print("ERROR: Arity mismatch", file=sys.stderr)
                sys.exit(33)

            method_element.append(ast_to_xml(ast.children[1]))  # Block
            return method_element
        
        elif ast.data == "block":
            assign_order_index = 1
            block_element = ET.Element("block")
            
            # Determine arity: count parameters
            parameters = [child for child in ast.children if isinstance(child, lark.Tree) and child.data == "parameter"]
            parameter_control = [parameter.children[0].value for parameter in parameters]
            block_element.set("arity", str(len(parameters)))
            param_index = 1
            for child in ast.children:
                if isinstance(child, lark.Tree) and child.data == "parameter":
                    param = ET.Element("parameter", name=child.children[0], order=str(param_index))
                    block_element.append(param)
                    param_index += 1
                else:
                    block_element.append(ast_to_xml(child))
            return block_element
        
        elif ast.data == "statement":
            assign_element = ET.Element("assign", order=str(assign_order_index))
            assign_order_index += 1
            if ast.children[0] in parameter_control:
                print("ERROR: Cannot assign to parameter", file=sys.stderr)
                sys.exit(34)
            var_element = ET.Element("var", name=ast.children[0])
            expr_element = ET.Element("expr")
            expr_element.append(ast_to_xml(ast.children[1]))
            assign_element.append(var_element)
            assign_element.append(expr_element)
            return assign_element
        
        elif ast.data == "literal":
            if isinstance(ast.children[0], lark.Tree) and ast.children[0].data == "block":
                return ast_to_xml(ast.children[0])
             # Determine the class type based on the token type
            if isinstance(ast.children[0], lark.Token):
                if ast.children[0].type == "INTEGER":
                    class_type = "Integer"
                elif ast.children[0].type == "STRING":
                    class_type = "String"
                elif ast.children[0].type == "CLASS_NAME":
                    class_type = ast.children[0].value  # Could be an object class
                else:
                    class_type = "Unknown"

                return ET.Element("literal", {"class": class_type, "value": ast.children[0].value})

            return ET.Element("literal", {"class": "Unknown", "value": str(ast.children[0])})
        
        elif ast.data == "expression":
            arg_order_index = 1
            exprbase = ast.children[0]
            exprtail = ast.children[1]
            # selectors
            if exprtail.data == "exprtail" and len(exprtail.children) > 0:
                exprsel = exprtail.children[0]  # First child is 'exprsel'
        
                if isinstance(exprsel, lark.Tree) and exprsel.data == "exprsel":
                    # Collect all VAR tokens (selectors)
                    selector_parts = [child for child in exprsel.children if isinstance(child, lark.Token) and child.type == "VAR"]
                    # Join the tokens with ":" and append ":" at the end
                    selector_string = ":".join(token.value for token in selector_parts) + ":"
                    
                    selector_element = ET.Element("send", selector=selector_string)
                    expr_element = ET.Element("expr")
                    selector_element.append(expr_element)
                    expr_element.append(ast_to_xml(exprbase))
                    # handles arguments
                    ast_args(exprsel, selector_element)
                else:
                    selector_element = ET.Element("send", selector=exprtail.children[0])
                    expr_element = ET.Element("expr")
                    selector_element.append(expr_element)
                    expr_element.append(ast_to_xml(exprbase))
            return selector_element
            
        elif ast.data == "exprbase":
            return ast_to_xml(ast.children[0])

    elif isinstance(ast, lark.Token):
        return ET.Element("var", name=ast.value)
    return ET.Element("unknown" + ast.data)

def ast_args(exprsel, selector_element, arg_order_index=1):
    # arguments
    for i in range(len(exprsel.children)):
        child = exprsel.children[i]
        if isinstance(child, lark.Tree) and child.data == "exprbase":
            arg_element = ET.Element("arg", order=str(arg_order_index))
            arg_order_index += 1
            expr_element = ET.Element("expr")
            expr_element.append(ast_to_xml(child))
            arg_element.append(expr_element)
            selector_element.append(arg_element)

def has_class_and_method(ast, class_name, method_name):
    # Traverse the AST to find the class with the given name
    if isinstance(ast, lark.Tree):
        if ast.data == "class":
            # Check if class name matches
            if ast.children[0].value == class_name:
                # Once class is found, look for the method with the specified name
                for method in ast.children[2:]:  # methods are in children[2:]
                    if method.data == "method" and method.children[0].children[0] == method_name:
                        return True
        else:
            return has_class_and_method(ast.children[0], class_name, method_name)
    return False

def fix_self_closing_tags(xml_string):
    # Use regex to add a space before the closing slash in self-closing tags
    return re.sub(r'<(\w+ [^/>]+)(/>)', r'<\1 />', xml_string)


try:
    ast = parser.parse(file)
    xml_root = ast_to_xml(ast)
    if xml_root is not None:
        xml_string = ET.tostring(xml_root, encoding="utf-8").decode("utf-8")
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
        # Check if "Main" class with "run" method exists in the AST
        if not has_class_and_method(ast, "Main", "run"):
            print("Class 'Main' or method 'run' not found.", file=sys.stderr)
            sys.exit(31)
        # Add the XML encoding at the top of the string
        xml_with_encoding = '<?xml version="1.0" encoding="UTF-8"?>' + pretty_xml.lstrip('<?xml version="1.0" ?>')
        # Fix the self-closing tags to include space before the forward slash
        fixed_xml = fix_self_closing_tags(xml_with_encoding)
        print(fixed_xml)
    else:
        print("ERROR: XML conversion failed", file=sys.stderr)
        sys.exit(35)
except lark.exceptions.LexError as e:
    print(f"ERROR: Lexical analysis failed: {e}", file=sys.stderr)
    sys.exit(21)
except lark.exceptions.ParseError as e:
    print(f"ERROR: Parse error: {e}", file=sys.stderr)
    sys.exit(22)
except lark.exceptions.LarkError as e:
    print(f"ERROR: Parsing failed: {e}", file=sys.stderr)
    sys.exit(22)
