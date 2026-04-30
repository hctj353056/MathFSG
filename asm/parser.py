"""
x86-64 汇编器 - 语法解析器
"""

from dataclasses import dataclass
from typing import Optional
from .tokenizer import Token, TokenType


@dataclass
class Operand:
    """操作数"""
    type: str  # 'reg', 'imm', 'mem', 'label'
    value: any
    size: int = 8  # 字节数


@dataclass
class Instruction:
    """指令"""
    mnemonic: str
    operands: list[Operand]
    line: int


@dataclass
class Label:
    """标签"""
    name: str
    address: int
    line: int


@dataclass
class Section:
    """段"""
    name: str
    instructions: list


class Parser:
    """语法解析器"""
    
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.labels = {}  # 标签定义 {name: address}
        self.current_address = 0
        self.label_refs = []  # 待解析的标签引用 [(address, label_name), ...]
    
    def peek(self) -> Token:
        """查看当前Token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)
    
    def advance(self) -> Token:
        """消费Token"""
        token = self.peek()
        self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """期望Token"""
        token = self.peek()
        if token.type != token_type:
            raise SyntaxError(f"期望 {token_type}, 得到 {token.type} at line {token.line}")
        return self.advance()
    
    @classmethod
    def parse(cls, tokens: list[Token]) -> list[Instruction]:
        """解析Token流"""
        parser = cls(tokens)
        return parser._parse_all()
    
    def _parse_all(self) -> list[Instruction]:
        """解析所有指令"""
        instructions = []
        sections = {'_start': []}  # 默认段
        current_section = '_start'
        
        while self.peek().type != TokenType.EOF:
            token = self.peek()
            
            if token.type == TokenType.NEWLINE:
                self.advance()
                continue
            
            elif token.type == TokenType.DIRECTIVE:
                self.advance()
                # 处理伪指令
                if token.value in ('.text', '.section', '.data', '.bss'):
                    current_section = token.value[1:] if token.value.startswith('.') else token.value
                    if current_section not in sections:
                        sections[current_section] = []
                continue
            
            elif token.type == TokenType.SECTION:
                self.advance()
                current_section = token.value
                if current_section not in sections:
                    sections[current_section] = []
                continue
            
            elif token.type == TokenType.LABEL:
                # 标签定义
                label_name = self.advance().value
                self.labels[label_name] = self.current_address
                continue
            
            elif token.type == TokenType.INSTRUCTION:
                instr = self._parse_instruction()
                instructions.append(instr)
                sections[current_section].append(instr)
                self.current_address += self._estimate_size(instr)
                continue
            
            else:
                self.advance()
        
        # 解析标签引用
        for instr in instructions:
            for i, op in enumerate(instr.operands):
                if op.type == 'label' and op.value in self.labels:
                    instr.operands[i] = Operand('imm', self.labels[op.value], op.size)
        
        return instructions
    
    def _parse_instruction(self) -> Instruction:
        """解析单条指令"""
        mnemonic = self.advance().value.upper()
        operands = []
        
        while self.peek().type not in (TokenType.NEWLINE, TokenType.EOF) and self.peek().type != TokenType.INSTRUCTION:
            if self.peek().type == TokenType.COMMA:
                self.advance()
                continue
            
            op = self._parse_operand()
            if op:
                operands.append(op)
        
        return Instruction(mnemonic, operands, self.peek().line)
    
    def _parse_operand(self) -> Optional[Operand]:
        """解析操作数"""
        token = self.peek()
        
        if token.type == TokenType.REGISTER:
            self.advance()
            return Operand('reg', token.value.lower(), self._register_size(token.value))
        
        elif token.type == TokenType.IMMEDIATE:
            self.advance()
            value = token.value
            if value.startswith('$'):
                value = value[1:]
            if value.startswith('0x'):
                value = int(value, 16)
            else:
                value = int(value)
            return Operand('imm', value, 8)
        
        elif token.type == TokenType.LABEL_REF:
            self.advance()
            return Operand('label', token.value, 8)
        
        elif token.type == TokenType.LBRACKET:
            self.advance()
            op = self._parse_memory_operand()
            self.expect(TokenType.RBRACKET)
            return op
        
        elif token.type == TokenType.MINUS:
            # 负数立即数
            self.advance()
            token = self.expect(TokenType.IMMEDIATE)
            value = token.value
            if value.startswith('0x'):
                value = int(value, 16)
            else:
                value = int(value)
            return Operand('imm', -value, 8)
        
        return None
    
    def _parse_memory_operand(self) -> Operand:
        """解析内存操作数"""
        token = self.peek()
        
        # 寄存器间接寻址 [%reg]
        if token.type == TokenType.REGISTER:
            self.advance()
            reg = token.value.lower()
            disp = 0
            scale = 1
            
            # 检查是否有偏移
            if self.peek().type == TokenType.PLUS:
                self.advance()
                if self.peek().type == TokenType.REGISTER:
                    self.advance()
                    reg2 = token.value.lower()
                    scale = 1
                    # 检查scale
                    if self.peek().type == TokenType.IMMEDIATE:
                        scale = int(self.advance().value)
                elif self.peek().type == TokenType.IMMEDIATE:
                    disp = int(self.advance().value)
            
            return Operand('mem', (reg, disp, scale), 8)
        
        # 数字偏移 [数字]
        elif token.type == TokenType.IMMEDIATE:
            disp = int(self.advance().value)
            reg = 'rax'
            if self.peek().type == TokenType.PLUS:
                self.advance()
                if self.peek().type == TokenType.REGISTER:
                    reg = self.advance().value.lower()
            return Operand('mem', (reg, disp, 1), 8)
        
        else:
            return Operand('mem', ('rax', 0, 1), 8)
    
    @staticmethod
    def _register_size(reg: str) -> int:
        """获取寄存器大小"""
        if reg.endswith(('q', 'd', 'w', 'b')):
            suffix = reg[-1]
            return {'q': 8, 'd': 4, 'w': 2, 'b': 1}.get(suffix, 8)
        return 8


    @staticmethod
    def _estimate_size(instr: Instruction) -> int:
        """估算指令字节数"""
        sizes = {
            'NOP': 1, 'HLT': 1, 'RET': 1,
            'PUSH': 1, 'POP': 1,
            'INC': 2, 'DEC': 2,
        }
        
        base = sizes.get(instr.mnemonic, 2)
        
        for op in instr.operands:
            if op.type == 'imm':
                if -128 <= op.value < 128:
                    base += 1
                elif -2147483648 <= op.value < 2147483648:
                    base += 4
                else:
                    base += 8
            elif op.type == 'mem':
                base += 4  # disp32
        
        return base
