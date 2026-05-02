"""
MathFSG demo - 一键运行形式系统语言示例

运行方法：
    python demo.py
"""

import sys
sys.path.insert(0, '.')

from lang import MathFSG, run

source = """
定义 内容
定义 写作 '内容'
定义 类型 写作 '类型 内容'
定义 断言{序号} 写作 '断言{序号} 内容'

类型 符号
类型 自然数
类型 整数
类型 负数

断言 存在 单位零 写作 '0'
断言 存在 单位一 写作 '1'

{=}:内容=内容;
{+}:自然数+自然数=自然数;
{-}:自然数-自然数=负数;
"""

if __name__ == "__main__":
    print("=" * 60)
    print("MathFSG 形式系统语言 Demo")
    print("=" * 60)
    print()

    mfsg = run(source)
    mfsg.info()

    print("=" * 60)
    print("运行模型检查...")
    print("=" * 60)
    mfsg.report_vulnerabilities()
