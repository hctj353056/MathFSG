"""
MathFSG - 形式系统定义语言
"""

from .parser import parse
from .interpreter import MathFSG, run


__all__ = ['parse', 'MathFSG', 'run']
