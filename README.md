# MathFSG

> FSG语言的数学领域扩展

## 项目概述

MathFSG 是 FSG 语言的数学领域扩展，旨在将形式化数学推理与 FSG 汇编语言相结合。

**核心目标：**
- 提供数学表达式的形式化表示
- 支持定理证明和模型检查
- 与 FSG 语言无缝集成

## 快速开始

```python
# 解析数学FSG表达式
from lang.parser import Parser
from lang.interpreter import Interpreter

parser = Parser()
interpreter = Interpreter()

# 解析并执行
ast = parser.parse("∀ x : Nat, x + 0 = x")
result = interpreter.evaluate(ast)
print(result)
```

## 项目结构

```
MathFSG/
├── asm/                 # 汇编层
│   ├── __init__.py
│   ├── config.json      # 配置文件
│   ├── encoder.py       # 编码器
│   ├── parser.py        # 汇编解析器
│   └── tokenizer.py     # 词法分析器
├── lang/                # 语言层
│   ├── __init__.py
│   ├── parser.py        # 数学表达式解析器
│   ├── interpreter.py   # 解释器
│   ├── model_checker.py # 模型检查器
│   └── mathfsg.mfsg     # 示例文件
├── README.md            # 项目说明
└── LICENSE              # 许可证
```

## 核心模块

### 汇编层 (`asm/`)

| 模块 | 说明 |
|------|------|
| `config.json` | 汇编配置 |
| `encoder.py` | 数学表达式编码 |
| `parser.py` | 汇编语法解析 |
| `tokenizer.py` | 词法分析 |

### 语言层 (`lang/`)

| 模块 | 说明 |
|------|------|
| `parser.py` | 数学FSG语法解析 |
| `interpreter.py` | 表达式解释执行 |
| `model_checker.py` | 模型检查和验证 |

## 依赖

- Python >= 3.10
- FSG-language (作为依赖)

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | - | 初始版本 |

## 作者

蜉蝣子 ♡

## 许可证

MIT License

---

*蜉熵阁 · MathFSG项目*
