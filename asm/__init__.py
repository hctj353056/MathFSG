"""
x86-64 汇编器 - 入口文件
"""

from .tokenizer import Tokenizer
from .parser import Parser
from .encoder import Encoder


def assemble(source: str) -> bytes:
    """
    汇编源码 → 机器码
    
    Args:
        source: 汇编源代码字符串
    
    Returns:
        机器码字节串
    """
    # 词法分析
    tokens = Tokenizer.tokenize(source)
    
    # 语法解析
    instructions = Parser.parse(tokens)
    
    # 指令编码
    machine_code = Encoder.encode(instructions)
    
    return machine_code


def assemble_file(input_path: str, output_path: str = None) -> bytes:
    """
    汇编文件
    
    Args:
        input_path: 输入汇编文件路径
        output_path: 输出机器码文件路径，若为None则返回字节串
    
    Returns:
        机器码字节串
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    code = assemble(source)
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(code)
    
    return code
