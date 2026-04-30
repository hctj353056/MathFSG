from asm import assemble

code = '''
mov rax, 1
add rax, rbx
nop
'''

result = assemble(code)  # 返回 bytes
print(result)