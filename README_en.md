# MathFSG

> Mathematical extension for FSG language

## Project Overview

MathFSG is a mathematical domain extension for the FSG language, aiming to combine formal mathematical reasoning with FSG assembly language.

**Core Goals:**
- Provide formal representation of mathematical expressions
- Support theorem proving and model checking
- Seamless integration with FSG language

## Quick Start

```python
# Parse MathFSG expressions
from lang.parser import Parser
from lang.interpreter import Interpreter

parser = Parser()
interpreter = Interpreter()

# Parse and evaluate
ast = parser.parse("∀ x : Nat, x + 0 = x")
result = interpreter.evaluate(ast)
print(result)
```

## Project Structure

```
MathFSG/
├── asm/                 # Assembly Layer
│   ├── __init__.py
│   ├── config.json      # Configuration
│   ├── encoder.py       # Encoder
│   ├── parser.py        # Assembly Parser
│   └── tokenizer.py     # Tokenizer
├── lang/                # Language Layer
│   ├── __init__.py
│   ├── parser.py        # Mathematical Expression Parser
│   ├── interpreter.py   # Interpreter
│   ├── model_checker.py # Model Checker
│   └── mathfsg.mfsg     # Example File
├── README.md            # Documentation (Chinese)
├── README_en.md         # Documentation (English)
└── LICENSE              # License
```

## Core Modules

### Assembly Layer (`asm/`)

| Module | Description |
|--------|-------------|
| `config.json` | Assembly configuration |
| `encoder.py` | Mathematical expression encoding |
| `parser.py` | Assembly syntax parsing |
| `tokenizer.py` | Lexical analysis |

### Language Layer (`lang/`)

| Module | Description |
|--------|-------------|
| `parser.py` | MathFSG syntax parsing |
| `interpreter.py` | Expression evaluation |
| `model_checker.py` | Model checking and verification |

## Dependencies

- Python >= 3.10
- FSG-language (as dependency)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | - | Initial version |

## Author

FuYou ♡

## License

MIT License

---

*FuShangGe · MathFSG Project*
