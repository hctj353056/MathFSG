"""
MathFSG 形式系统语言 - 解析器
"""

import re


class TokenType:
    """Token类型"""
    DEFINED = '定义'
    TYPE = '类型'
    ASSERT = '断言'
    LBRACE = '{'
    RBRACE = '}'
    LBRACKET = '['
    RBRACKET = ']'
    LPAREN = '('
    RPAREN = ')'
    QUOTE = "'"
    COLON = ':'
    SEMICOLON = ';'
    EQUAL = '='
    PLUS = '+'
    MINUS = '-'
    STAR = '*'
    SLASH = '/'
    NUMBER = '数字'
    IDENT = '标识符'
    STRING = '字符串'
    COMMENT = '注释'
    NEWLINE = '换行'
    EOF = '文件结束'


class Token:
    """Token"""
    def __init__(self, type_, value, line=0, col=0):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """词法分析器"""
    
    KEYWORDS = {'定义', '写作', '类型', '断言', '存在', '且', '或', '若', '则'}
    
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
    
    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ''
    
    def advance(self):
        ch = self.source[self.pos] if self.pos < len(self.source) else ''
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    def tokenize(self):
        """词法分析"""
        tokens = []
        
        while self.pos < len(self.source):
            ch = self.peek()
            
            # 跳过空白
            if ch in ' \t\r':
                self.advance()
                continue
            
            # 注释
            if ch == '#':
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
                tokens.append(Token(TokenType.COMMENT, self.source[start:self.pos], self.line, self.col))
                continue
            
            # 换行
            if ch == '\n':
                self.advance()
                tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.col))
                continue
            
            # 符号 {符号} 形式（只有前面是空白/行首时才识别）
            if ch == '{':
                # 检查是否前面是空白或行首
                is_symbol = False
                if self.col == 1:  # 行首
                    is_symbol = True
                elif self.pos == 0 or self.source[self.pos - 1] in ' \t\n':
                    # 找 } 的位置
                    brace_pos = self.source.find('}', self.pos)
                    if brace_pos != -1:
                        content = self.source[self.pos:brace_pos]
                        # 内容必须是单个符号（运算符或标识符）
                        if content and not any(c in content for c in '\n\r'):
                            is_symbol = True
                
                if is_symbol:
                    start_col = self.col - 1
                    self.advance()  # 跳过 {
                    # 收集符号内容（除了 } 之外的所有字符）
                    sym = ''
                    while self.pos < len(self.source) and self.source[self.pos] != '}':
                        sym += self.source[self.pos]
                        self.pos += 1
                    if self.pos < len(self.source):
                        self.pos += 1  # 跳过 }
                    tokens.append(Token(TokenType.LBRACE, sym, self.line, start_col))
                    tokens.append(Token(TokenType.RBRACE, '}', self.line, start_col + len(sym) + 1))
                    continue
                else:
                    # 作为标识符的一部分
                    pass
            
            # 其他符号
            if ch in '}=:;+-*/[]()':
                self.advance()
                type_map = {
                    '}': TokenType.RBRACE,
                    '[': TokenType.LBRACKET,
                    ']': TokenType.RBRACKET,
                    '(': TokenType.LPAREN,
                    ')': TokenType.RPAREN,
                    '=': TokenType.EQUAL,
                    '+': TokenType.PLUS,
                    '-': TokenType.MINUS,
                    '*': TokenType.STAR,
                    '/': TokenType.SLASH,
                    ':': TokenType.COLON,
                    ';': TokenType.SEMICOLON,
                }
                tokens.append(Token(type_map[ch], ch, self.line, self.col - 1))
                continue
            
            # 字符串
            if ch == "'":
                self.advance()
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos] != "'":
                    self.pos += 1
                value = self.source[start:self.pos]
                if self.pos < len(self.source):
                    self.advance()
                tokens.append(Token(TokenType.STRING, value, self.line, self.col - 1))
                continue
            
            # 数字
            if ch.isdigit():
                start = self.pos
                while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] in 'abcdefxABCDEF'):
                    self.pos += 1
                value = self.source[start:self.pos]
                tokens.append(Token(TokenType.NUMBER, value, self.line, self.col - 1))
                continue
            
            # 标识符/关键字（全部作为IDENT返回）
            if ch.isalpha() or '\u4e00' <= ch <= '\u9fff' or ch == '_':
                start = self.pos
                while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] in '_' or '\u4e00' <= self.source[self.pos] <= '\u9fff'):
                    self.pos += 1
                value = self.source[start:self.pos]
                # 全部作为IDENT返回
                tokens.append(Token(TokenType.IDENT, value, self.line, self.col - 1))
                continue
            
            # 跳过未知字符
            self.advance()
        
        tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return tokens


class Parser:
    """语法解析器"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.ast = {
            'defines': {},      # 定义: {名称: 内容}
            'types': {},        # 类型: [名称列表]
            'asserts': {},      # 断言: {序号: 内容}
            'symbols': {},      # 符号形式: {符号: 定义}
        }
    
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]
    
    def advance(self):
        token = self.peek()
        self.pos += 1
        return token
    
    def expect(self, type_):
        token = self.peek()
        if token.type != type_ and token.value != type_:
            raise SyntaxError(f"期望 {type_}, 得到 {token}")
        return self.advance()
    
    def parse(self):
        """解析整个程序"""
        while self.peek().type != TokenType.EOF:
            t = self.peek()
            
            # 跳过注释和换行
            if t.type in (TokenType.COMMENT, TokenType.NEWLINE):
                self.advance()
                continue
            
            # 定义
            if t.value == '定义':
                self._parse_define()
            
            # 类型
            elif t.type == TokenType.TYPE or t.value == '类型':
                self._parse_type()
            
            # 断言
            elif t.value == '断言':
                self._parse_assert()
            
            # 符号形式 {符号}:定义;
            elif t.type == TokenType.LBRACE:
                self._parse_symbol()
            
            else:
                self.advance()
        
        return self.ast
    
    def _parse_define(self):
        """解析 定义 语句"""
        self.expect('定义')
        
        # 定义名称可以是任何非空白token
        token = self.advance()
        name = token.value
        
        # 检查是否有 写作
        if self.peek().value == '写作':
            self.advance()
            # 直接expect字符串
            value_token = self.expect(TokenType.STRING)
            self.ast['defines'][name] = value_token.value
        else:
            self.ast['defines'][name] = None
    
    def _parse_type(self):
        """解析 类型 语句"""
        if self.peek().value == '类型':
            self.advance()
        
        while self.peek().type == TokenType.IDENT:
            type_token = self.advance()
            type_name = type_token.value
            if type_name not in self.ast['types']:
                self.ast['types'][type_name] = type_name
    
    def _parse_assert(self):
        """解析 断言 语句"""
        self.expect('断言')
        
        # 可选序号
        num = None
        if self.peek().type == TokenType.IDENT and self.peek().value.startswith('断言'):
            # 断言1, 断言2...
            num = self.peek().value
            self.advance()
        elif self.peek().type == TokenType.NUMBER:
            num = '断言' + self.advance().value
        else:
            num = f'断言{len(self.ast["asserts"]) + 1}'
        
        # 断言内容可以是任意token序列直到换行或分号
        content = []
        while self.peek().type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.SEMICOLON):
            content.append(self.advance())
        
        if self.peek().type == TokenType.SEMICOLON:
            self.advance()
        
        self.ast['asserts'][num] = content
    
    def _parse_symbol(self):
        """解析 符号形式 {符号}:定义;"""
        # LBRACE的value就是符号内容
        lbrace_token = self.expect(TokenType.LBRACE)
        symbol = lbrace_token.value
        
        # 检查是否有 RBRACE
        if self.peek().type == TokenType.RBRACE:
            self.advance()
        
        self.expect(TokenType.COLON)
        
        # 定义内容
        definition = []
        while self.peek().type not in (TokenType.SEMICOLON, TokenType.EOF, TokenType.NEWLINE):
            definition.append(self.advance())
        
        if self.peek().type == TokenType.SEMICOLON:
            self.advance()
        
        self.ast['symbols'][symbol] = definition


def parse(source):
    """解析MathFSG源码"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
