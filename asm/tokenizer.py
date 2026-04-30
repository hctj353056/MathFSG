"""
x86-64 汇编器 - 词法分析器
"""

import re
from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Token类型"""
    INSTRUCTION = auto()      # 指令
    REGISTER = auto()          # 寄存器
    LABEL = auto()            # 标签
    LABEL_REF = auto()         # 标签引用
    IMMEDIATE = auto()        # 立即数
    DIRECTIVE = auto()        # 伪指令
    SECTION = auto()          # 段声明
    NEWLINE = auto()          # 换行
    COMMENT = auto()          # 注释
    COMMA = auto()            # 逗号
    COLON = auto()            # 冒号
    LBRACKET = auto()         # 左括号
    RBRACKET = auto()         # 右括号
    PLUS = auto()             # 加号
    MINUS = auto()            # 减号
    EOF = auto()              # 文件结束


@dataclass
class Token:
    """Token"""
    type: TokenType
    value: str
    line: int
    col: int


# 指令集
INSTRUCTIONS = {
    # 数据传送
    'mov', 'movq', 'movzx', 'movsx',
    'push', 'pop', 'lea',
    # 算术运算
    'add', 'addq', 'sub', 'subq',
    'mul', 'imul', 'div', 'idiv',
    'inc', 'dec', 'neg',
    # 逻辑运算
    'and', 'or', 'xor', 'not', 'cmp',
    'test', 'shl', 'shr', 'sal', 'sar',
    # 控制流
    'jmp', 'je', 'jne', 'jz', 'jnz',
    'jl', 'jle', 'jg', 'jge', 'ja', 'jae', 'jb', 'jbe',
    'call', 'ret', 'syscall', 'int',
    # 其他
    'nop', 'hlt', 'cpuid', 'rdtsc',
}

# 寄存器
REGISTERS = {
    'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp',
    'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15',
    'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp',
    'r8d', 'r9d', 'r10d', 'r11d', 'r12d', 'r13d', 'r14d', 'r15d',
    'ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp',
    'r8w', 'r9w', 'r10w', 'r11w', 'r12w', 'r13w', 'r14w', 'r15w',
    'al', 'bl', 'cl', 'dl', 'sil', 'dil', 'bpl', 'spl',
    'r8b', 'r9b', 'r10b', 'r11b', 'r12b', 'r13b', 'r14b', 'r15b',
    'ah', 'bh', 'ch', 'dh',
}


class Tokenizer:
    """词法分析器"""
    
    @classmethod
    def tokenize(cls, source: str) -> list[Token]:
        """词法分析"""
        tokens = []
        lines = source.split('\n')
        line_num = 0
        
        for line in lines:
            line_num += 1
            col = 0
            # 去掉注释
            if ';' in line:
                line = line[:line.index(';')]
            
            while col < len(line):
                # 跳过空白
                while col < len(line) and line[col] in ' \t':
                    col += 1
                if col >= len(line):
                    break
                
                token = cls._read_token(line, col, line_num)
                if token is None:
                    raise SyntaxError(f"无法识别的字符 '{line[col]}' at line {line_num}, col {col}")
                
                if token.type != TokenType.NEWLINE:
                    tokens.append(token)
                col += len(token.value)
            
            # 每行末尾加NEWLINE
            tokens.append(Token(TokenType.NEWLINE, '\\n', line_num, len(line)))
        
        tokens.append(Token(TokenType.EOF, '', line_num, 0))
        return tokens
    
    @classmethod
    def _read_token(cls, line: str, start: int, line_num: int) -> Token:
        """读取单个Token"""
        if start >= len(line):
            return None
        
        c = line[start]
        
        # 空白
        if c in ' \t':
            return Token(TokenType.NEWLINE, c, line_num, start)
        
        # 换行
        if c == '\n':
            return Token(TokenType.NEWLINE, c, line_num, start)
        
        # 符号
        if c == ',':
            return Token(TokenType.COMMA, c, line_num, start)
        if c == ':':
            return Token(TokenType.COLON, c, line_num, start)
        if c == '[':
            return Token(TokenType.LBRACKET, c, line_num, start)
        if c == ']':
            return Token(TokenType.RBRACKET, c, line_num, start)
        if c == '+':
            return Token(TokenType.PLUS, c, line_num, start)
        if c == '-':
            return Token(TokenType.MINUS, c, line_num, start)
        
        # 数字
        if c.isdigit():
            end = start
            while end < len(line) and (line[end].isdigit() or line[end] in 'abcdefABCDEFx'):
                end += 1
            value = line[start:end]
            # 处理$前缀
            if value.startswith('$'):
                value = value[1:]
            return Token(TokenType.IMMEDIATE, value, line_num, start)
        
        # 标识符/指令/寄存器/标签
        if c.isalpha() or c == '_' or c == '.':
            end = start
            while end < len(line) and (line[end].isalnum() or line[end] in '_.'):
                end += 1
            value = line[start:end]
            value_lower = value.lower()
            
            # 寄存器（带%前缀或直接识别）
            if value_lower in REGISTERS:
                return Token(TokenType.REGISTER, value_lower, line_num, start)
            
            # 指令
            if value_lower in INSTRUCTIONS:
                return Token(TokenType.INSTRUCTION, value_lower.upper(), line_num, start)
            
            # 伪指令
            if value.startswith('.'):
                return Token(TokenType.DIRECTIVE, value, line_num, start)
            
            # 标签定义（末尾有:）
            if end < len(line) and line[end] == ':':
                return Token(TokenType.LABEL, value, line_num, start)
            
            # 标签引用或指令（末尾无:）
            upper = value.upper()
            if upper in INSTRUCTIONS:
                return Token(TokenType.INSTRUCTION, upper, line_num, start)
            
            return Token(TokenType.LABEL_REF, value, line_num, start)
        
        return None
