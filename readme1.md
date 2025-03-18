# Documentation of Project Implementation for IPP 2024/2025
# Name and surname: Adam Veselý
# Login: xvesela00

## Design Overview

The parse.py script is designed to analyze source code written in SOL25 and convert it into XML according to the given specification.

## Internal Representation

The script uses Lark to generate an Abstract Syntax Tree (AST) based on a defined grammar. This AST is then processed in three steps: validation, transformation, and XML generation.

## Implementation details

### Parsing
- The Lark parser processes SOL25 code using a defined grammar.
- The parsed output is an AST, which serves as the internal structure.
### Semantic Validation
- Semantic Validation occurs in parallel with XML generation, removing the need to go through the entire structure multiple times.
- The AST is checked for correctness, ensuring valid constructs and proper variable usage.
- Errors like undefined variables and incorrect arity are caught and reported with their respective error codes.
### XML conversion
- The validated AST is recursively transformed into an XML tree using ElementTree.
- AST nodes are mapped to XML elements, preserving structure and metadata.
- The XML structure is then shaped into the desired form for readability.

## Conclusion
The implementation converts SOL25 source code into an XML structure for future interpretation. Future work could enhance validation, improve error handling, and modularize the script to make it more readable and easier to edit/improve on.