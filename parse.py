import sys # for parsing CLI arguments
import lark # for parsing the grammar

# ================== Handle CLI arguments ==================

if "--help" in sys.argv or "-h" in sys.argv:
    # Only one argument with --help or -h
    if(len(sys.argv) == 2):
        print("Usage: python parse.py [OPTION] [FILE]")
        sys.exit(0)
    else:
        print("Usage: python parse.py [OPTION] [FILE]")
        sys.exit(10)

# ================== Handle CLI arguments ==================

# Store stdin in a variable
file = sys.stdin.read()

keywords = [
    "class",
    "self",
    "super",
    "nil",
    "true",
    "false"
]

in_built_classes = [
    "Object",
    "Nil",
    "True",
    "False",
    "Integer",
    "String",
    "Block"
]

print(file)