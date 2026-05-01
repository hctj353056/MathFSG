"""
MathFSG - 模型检查器
自动发现形式系统中的漏洞/矛盾
"""

from dataclasses import dataclass
from typing import Set, Dict, List, Optional
import itertools


@dataclass
class Vulnerability:
    """漏洞"""
    type: str          # 漏洞类型
    description: str   # 描述
    location: str      # 位置
    details: str      # 详细说明


class ModelChecker:
    """形式系统模型检查器"""
    
    def __init__(self, system):
        self.system = system
        self.vulnerabilities = []
    
    def check_all(self) -> List[Vulnerability]:
        """执行所有检查"""
        self.vulnerabilities = []
        
        self.check_undefined_refs()     # 检查未定义引用
        self.check_type_conflicts()     # 检查类型冲突
        self.check_circular_defines()  # 检查循环定义
        self.check_symbol_consistency() # 检查符号一致性
        self.check_closure()           # 检查运算封闭性
        
        return self.vulnerabilities
    
    def check_undefined_refs(self):
        """检查未定义的引用"""
        defines = set(self.system.defines.keys())
        objects = set(self.system.objects.keys())
        known = defines | objects
        
        # 检查定义中是否有未定义引用
        for name, value in self.system.defines.items():
            if isinstance(value, str):
                words = value.split()
                for word in words:
                    # 去掉标点
                    word = word.strip('(),;:')
                    if word and word not in known and word not in ('减', '加', '乘', '除'):
                        self.vulnerabilities.append(Vulnerability(
                            type="未定义引用",
                            description=f"'{name}' 引用了未定义的 '{word}'",
                            location=f"定义 {name}",
                            details=f"已知符号: {known}"
                        ))
        
        # 检查断言中是否有未定义引用
        for name, tokens in self.system.asserts.items():
            for token in tokens:
                if hasattr(token, 'value'):
                    word = token.value.strip('(),;:')
                    if word and word not in known and word not in ('存在', '且', '或', '写作'):
                        self.vulnerabilities.append(Vulnerability(
                            type="未定义引用",
                            description=f"断言 '{name}' 引用了未定义的 '{word}'",
                            location=f"断言 {name}",
                            details=f"已知符号: {known}"
                        ))
    
    def check_type_conflicts(self):
        """检查类型冲突"""
        types = self.system.types
        
        # 检查是否有冲突的类型定义
        type_keywords = {'自然数', '整数', '负数', '符号', '布尔'}
        defined_types = {k for k in self.system.defines.keys() if k in type_keywords}
        
        # 检查符号形式中的类型匹配
        for symbol, definition in self.system.symbols.items():
            # 这里可以检查如 {+} 的定义是否与类型一致
            # 目前是占位，后续可扩展
            pass
    
    def check_circular_defines(self):
        """检查循环定义"""
        defines = self.system.defines
        
        # 找出所有循环
        def find_cycles(start_node):
            visited = set()
            path = []
            
            def dfs(node):
                if node in path:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    # 排除自引用循环
                    if len(cycle) > 1:
                        return [cycle]
                    return []
                
                if node in visited:
                    return []
                
                path.append(node)
                visited.add(node)
                
                # 获取依赖
                deps = set()
                value = defines.get(node, '')
                if isinstance(value, str):
                    for word in value.split():
                        word = word.strip('(),;:')
                        if word in defines:
                            deps.add(word)
                
                cycles = []
                for dep in deps:
                    cycles.extend(dfs(dep))
                
                path.pop()
                return cycles
            
            return dfs(start_node)
        
        all_cycles = []
        for name in defines:
            all_cycles.extend(find_cycles(name))
        
        for cycle in all_cycles:
            self.vulnerabilities.append(Vulnerability(
                type="循环定义",
                description=f"发现循环依赖: {' → '.join(cycle[:-1])}",
                location=f"循环: {' → '.join(cycle)}",
                details="循环定义可能导致系统无法求值"
            ))
    
    def check_symbol_consistency(self):
        """检查符号一致性"""
        # 检查同一符号是否有多个定义
        symbol_defs = {}
        for symbol, definition in self.system.symbols.items():
            # 处理Token对象或字符串
            if isinstance(definition, list):
                key = tuple(str(getattr(t, 'value', t)) for t in definition)
            else:
                key = str(definition)
            
            if symbol in symbol_defs:
                self.vulnerabilities.append(Vulnerability(
                    type="符号重复定义",
                    description=f"符号 '{symbol}' 被定义了多次",
                    location=f"符号 {symbol}",
                    details=f"定义1: {symbol_defs[symbol]}\n定义2: {definition}"
                ))
            symbol_defs[symbol] = key
    
    def check_closure(self):
        """检查运算封闭性"""
        # 对于 {+} 等运算，检查结果是否在定义域内
        defines = self.system.defines
        
        # 如果定义了自然数和加法，检查封闭性
        if '自然数' in self.system.types or '自然数' in defines:
            # 这里检查运算结果是否可能超出类型范围
            # 目前是占位，复杂封闭性检查需要数值解释器
            pass
        
        # 检查减法是否可能产生负数
        minus_def = self.system.symbols.get('-', [])
        if minus_def:
            # 如果定义了减法但没有负数类型，可能不封闭
            has_negative = '负数' in self.system.types or '负数' in defines
            if not has_negative:
                self.vulnerabilities.append(Vulnerability(
                    type="运算不封闭",
                    description="定义了减法但没有负数类型",
                    location="符号 -",
                    details="减法结果可能超出自然数范围，导致运算不封闭"
                ))
    
    def report(self):
        """生成报告"""
        if not self.vulnerabilities:
            print("✓ 未发现漏洞")
            return
        
        print(f"✗ 发现 {len(self.vulnerabilities)} 个潜在漏洞:\n")
        
        # 按类型分组
        by_type = {}
        for v in self.vulnerabilities:
            if v.type not in by_type:
                by_type[v.type] = []
            by_type[v.type].append(v)
        
        for vtype, vulns in by_type.items():
            print(f"【{vtype}】({len(vulns)}个)")
            for v in vulns:
                print(f"  • {v.description}")
                print(f"    位置: {v.location}")
            print()


def check_system(system) -> List[Vulnerability]:
    """检查形式系统的便捷函数"""
    checker = ModelChecker(system)
    return checker.check_all()
