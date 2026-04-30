"""
x86-64 汇编器 - 词法分析器（支持中英双语）
"""

import re
import json
import os
from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Token类型"""
    INSTRUCTION = auto()
    REGISTER = auto()
    LABEL = auto()
    LABEL_REF = auto()
    IMMEDIATE = auto()
    DIRECTIVE = auto()
    SECTION = auto()
    NEWLINE = auto()
    COMMENT = auto()
    COMMA = auto()
    COLON = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    PLUS = auto()
    MINUS = auto()
    EOF = auto()


@dataclass
class Token:
    """Token"""
    type: TokenType
    value: str
    line: int
    col: int


class Config:
    """配置加载器"""
    _instance = None
    _config = None
    
    @classmethod
    def get(cls):
        if cls._config is None:
            cls._config = cls._load()
        return cls._config
    
    @classmethod
    def _load(cls):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def get_instructions(cls):
        return set(cls.get()['instructions'].keys())
    
    @classmethod
    def get_zh_to_en(cls):
        return cls.get()['keywords']['zh_to_en']
    
    @classmethod
    def get_registers(cls):
        cfg = cls.get()
        regs = {}
        for size in cfg['registers']:
            regs.update(cfg['registers'][size])
        return regs


class Tokenizer:
    """词法分析器"""
    
    @classmethod
    def tokenize(cls, source: str) -> list[Token]:
        """词法分析"""
        tokens = []
        lines = source.split('\n')
        line_num = 0
        
        # 加载配置
        instructions = Config.get_instructions()
        zh_to_en = Config.get_zh_to_en()
        registers = Config.get_registers()
        
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
                
                result = cls._read_token(line, col, line_num, instructions, zh_to_en, registers)
                if result is None:
                    raise SyntaxError(f"无法识别的字符 '{line[col]}' at line {line_num}, col {col}")
                
                token, end = result
                if token.type != TokenType.NEWLINE:
                    tokens.append(token)
                col = end
            
            tokens.append(Token(TokenType.NEWLINE, '\n', line_num, len(line)))
        
        tokens.append(Token(TokenType.EOF, '', line_num, 0))
        return tokens
    
    @classmethod
    def _read_token(cls, line: str, start: int, line_num: int, instructions, zh_to_en, registers):
        """读取单个Token，返回(token, end_position)"""
        if start >= len(line):
            return None
        
        c = line[start]
        
        # 符号
        if c == ',':
            return Token(TokenType.COMMA, c, line_num, start), start + 1
        if c == ':':
            return Token(TokenType.COLON, c, line_num, start), start + 1
        if c == '[':
            return Token(TokenType.LBRACKET, c, line_num, start), start + 1
        if c == ']':
            return Token(TokenType.RBRACKET, c, line_num, start), start + 1
        if c == '+':
            return Token(TokenType.PLUS, c, line_num, start), start + 1
        if c == '-':
            return Token(TokenType.MINUS, c, line_num, start), start + 1
        
        # 数字
        if c.isdigit():
            end = start
            while end < len(line) and (line[end].isdigit() or line[end] in 'abcdefABCDEFx'):
                end += 1
            value = line[start:end]
            if value.startswith('$'):
                value = value[1:]
            return Token(TokenType.IMMEDIATE, value, line_num, start), end
        
        # 标识符/指令/寄存器/标签/中文
        if c.isalpha() or c == '_' or c == '.' or '\u4e00' <= c <= '\u9fff':
            end = start
            while end < len(line) and (line[end].isalnum() or line[end] in '_.' or '\u4e00' <= line[end] <= '\u9fff'):
                end += 1
            value = line[start:end]
            
            # 中文指令/寄存器转换
            if value in zh_to_en:
                value = zh_to_en[value]
            
            value_lower = value.lower()
            
            # 寄存器
            if value_lower in registers:
                return Token(TokenType.REGISTER, value_lower, line_num, start), end
            
            # 指令
            if value_lower in instructions:
                return Token(TokenType.INSTRUCTION, value_lower.upper(), line_num, start), end
            
            # 伪指令
            if value.startswith('.'):
                return Token(TokenType.DIRECTIVE, value, line_num, start), end
            
            # 标签定义
            if end < len(line) and line[end] == ':':
                return Token(TokenType.LABEL, value, line_num, start), end + 1
            
            return Token(TokenType.LABEL_REF, value, line_num, start), end
        
        return None
