"""
MathFSG 形式系统语言 - 解释器
"""

from .parser import parse


class MathFSG:
    """MathFSG 形式系统解释器"""
    
    def __init__(self):
        self.defines = {}      # 定义表
        self.types = set()     # 类型集合
        self.asserts = {}     # 断言
        self.symbols = {}      # 符号形式
        self.objects = {}      # 对象实例
        
        # 内置类型
        self._init_builtins()
    
    def _init_builtins(self):
        """初始化内置定义"""
        # 根基层
        self.defines['内容'] = None
        self.defines['单位零'] = '0'
        self.defines['单位一'] = '1'
        self.defines['间隙'] = '单位一 减 单位零'
        
        # 内置类型
        self.types.update(['符号', '自然数', '整数', '负数', '布尔'])
        
        # 内置对象
        self.objects['0'] = 0
        self.objects['1'] = 1
    
    def load(self, source):
        """加载并解析源码"""
        ast = parse(source)
        
        # 合并定义
        self.defines.update(ast['defines'])
        
        # 合并类型
        for t in ast['types']:
            self.types.add(t)
        
        # 合并断言
        self.asserts.update(ast['asserts'])
        
        # 合并符号形式
        self.symbols.update(ast['symbols'])
        
        return self
    
    def eval(self, expr):
        """求值表达式"""
        if isinstance(expr, list):
            # 操作序列
            result = None
            for item in expr:
                result = self.eval(item)
            return result
        elif isinstance(expr, str):
            # 检查是否是已定义的对象
            if expr in self.objects:
                return self.objects[expr]
            # 检查是否是定义
            if expr in self.defines:
                return self.defines[expr]
            # 尝试转为数字
            try:
                return int(expr)
            except:
                return expr
        else:
            return expr
    
    def info(self):
        """显示当前状态"""
        print("=== MathFSG 当前状态 ===")
        print()
        print("定义:")
        for k, v in self.defines.items():
            if v is not None:
                print(f"  {k} = {v}")
            else:
                print(f"  {k}")
        print()
        print("类型:")
        for t in sorted(self.types):
            print(f"  {t}")
        print()
        print("断言:")
        for k, v in self.asserts.items():
            tokens_str = ' '.join([str(t.value) for t in v]) if isinstance(v, list) else str(v)
            print(f"  {k}: {tokens_str}")
        print()
        print("符号形式:")
        for k, v in self.symbols.items():
            tokens_str = ' '.join([str(t.value) for t in v]) if isinstance(v, list) else str(v)
            print(f"  {{{k}}}: {tokens_str}")


def run(source):
    """运行MathFSG源码"""
    mfsg = MathFSG()
    mfsg.load(source)
    return mfsg
