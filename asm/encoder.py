"""
x86-64 汇编器 - 指令编码器
"""

from dataclasses import dataclass
from .parser import Instruction, Operand


# 寄存器编码表
REG_ENCODING = {
    # 64位
    'rax': 0, 'rcx': 1, 'rdx': 2, 'rbx': 3,
    'rsp': 4, 'rbp': 5, 'rsi': 6, 'rdi': 7,
    'r8': 8, 'r9': 9, 'r10': 10, 'r11': 11,
    'r12': 12, 'r13': 13, 'r14': 14, 'r15': 15,
    # 32位
    'eax': 0, 'ecx': 1, 'edx': 2, 'ebx': 3,
    'esp': 4, 'ebp': 5, 'esi': 6, 'edi': 7,
    'r8d': 8, 'r9d': 9, 'r10d': 10, 'r11d': 11,
    'r12d': 12, 'r13d': 13, 'r14d': 14, 'r15d': 15,
    # 16位
    'ax': 0, 'cx': 1, 'dx': 2, 'bx': 3,
    'sp': 4, 'bp': 5, 'si': 6, 'di': 7,
    'r8w': 8, 'r9w': 9, 'r10w': 10, 'r11w': 11,
    'r12w': 12, 'r13w': 13, 'r14w': 14, 'r15w': 15,
    # 8位
    'al': 0, 'cl': 1, 'dl': 2, 'bl': 3,
    'sil': 6, 'dil': 7, 'bpl': 5, 'spl': 4,
    'r8b': 8, 'r9b': 9, 'r10b': 10, 'r11b': 11,
    'r12b': 12, 'r13b': 13, 'r14b': 14, 'r15b': 15,
    'ah': 4, 'ch': 5, 'dh': 6, 'bh': 7,
}

# ModR/M表
MODRM_MOD = {
    (0b00, 'reg'): 0b00,  # [reg]
    (0b01, 'reg'): 0b01,  # [reg+disp8]
    (0b10, 'reg'): 0b10,  # [reg+disp32]
    (0b11, 'reg'): 0b11,  # reg
}

# SIB表
SIB_INDEX = {
    'rax': 0, 'rcx': 1, 'rdx': 2, 'rbx': 3,
    'rsp': 4, 'rbp': 5, 'rsi': 6, 'rdi': 7,
    'r8': 8, 'r9': 9, 'r10': 10, 'r11': 11,
    'r12': 12, 'r13': 13, 'r14': 14, 'r15': 15,
}


class Encoder:
    """指令编码器"""
    
    @classmethod
    def encode(cls, instructions: list[Instruction]) -> bytes:
        """
        编码指令序列
        
        Args:
            instructions: 指令列表
        
        Returns:
            机器码字节串
        """
        code = b''
        
        for instr in instructions:
            try:
                encoded = cls._encode_instruction(instr)
                code += encoded
            except Exception as e:
                raise EncodeError(f"编码失败 at line {instr.line}: {e}")
        
        return code
    
    @classmethod
    def _encode_instruction(cls, instr: Instruction) -> bytes:
        """编码单条指令"""
        mnemonic = instr.mnemonic
        ops = instr.operands
        
        # 无操作数指令
        if mnemonic == 'NOP':
            return b'\x90'
        elif mnemonic == 'HLT':
            return b'\xf4'
        elif mnemonic == 'RET':
            return b'\xc3'
        
        # 单操作数指令
        elif mnemonic == 'PUSH':
            return cls._encode_push(ops)
        elif mnemonic == 'POP':
            return cls._encode_pop(ops)
        elif mnemonic == 'NOT':
            return cls._encode_unary(instr, 0xf6, 0xf7)
        elif mnemonic == 'NEG':
            return cls._encode_unary(instr, 0xf6, 0xf7)
        elif mnemonic == 'INC':
            return cls._encode_inc_dec(instr, 0xfe, 0xff)
        elif mnemonic == 'DEC':
            return cls._encode_inc_dec(instr, 0xfe, 0xff)
        elif mnemonic == 'CALL':
            return cls._encode_call(ops)
        elif mnemonic == 'JMP':
            return cls._encode_jmp(ops)
        
        # 跳转指令
        elif mnemonic in ('JE', 'JZ'):
            return cls._encode_jcc(ops, 0x74)
        elif mnemonic in ('JNE', 'JNZ'):
            return cls._encode_jcc(ops, 0x75)
        elif mnemonic == 'JL':
            return cls._encode_jcc(ops, 0x7c)
        elif mnemonic == 'JLE':
            return cls._encode_jcc(ops, 0x7e)
        elif mnemonic == 'JG':
            return cls._encode_jcc(ops, 0x7f)
        elif mnemonic == 'JGE':
            return cls._encode_jcc(ops, 0x7d)
        
        # 两操作数指令
        elif mnemonic in ('MOV', 'MOVQ'):
            return cls._encode_mov(instr)
        elif mnemonic in ('ADD', 'ADDQ'):
            return cls._encode_arith(instr, 0x00, 0x01)
        elif mnemonic in ('SUB', 'SUBQ'):
            return cls._encode_arith(instr, 0x28, 0x29)
        elif mnemonic == 'CMP':
            return cls._encode_cmp(instr)
        elif mnemonic in ('AND', 'OR', 'XOR'):
            return cls._encode_logic(instr, mnemonic)
        elif mnemonic in ('TEST',):
            return cls._encode_test(instr)
        
        else:
            raise EncodeError(f"不支持的指令: {mnemonic}")
    
    @classmethod
    def _encode_mov(cls, instr: Instruction) -> bytes:
        """编码MOV指令"""
        mnemonic = instr.mnemonic
        dst, src = instr.operands
        
        # mov r64, imm64
        if dst.type == 'reg' and src.type == 'imm':
            size = dst.size
            reg_enc = REG_ENCODING.get(dst.value, 0)
            # ModR/M: mod=11, reg=000, r/m=reg
            modrm = 0xc0 | (reg_enc & 7)
            if size == 8:
                return bytes([0x48, 0xc7]) + bytes([modrm]) + cls._encode_imm(src.value, 4)
            elif size == 4:
                return bytes([0xc7]) + bytes([modrm]) + cls._encode_imm(src.value, 4)
        
        # mov r64, r64
        if dst.type == 'reg' and src.type == 'reg':
            reg1, reg2 = dst.value, src.value
            if 'r8' in reg1 or 'r9' in reg1 or 'r10' in reg1 or 'r11' in reg1 or 'r12' in reg1 or 'r13' in reg1 or 'r14' in reg1 or 'r15' in reg1 or 'rsp' in reg1 or 'rbp' in reg1 or 'rsi' in reg1 or 'rdi' in reg1 or 'rax' in reg1 or 'rbx' in reg1 or 'rcx' in reg1 or 'rdx' in reg1:
                # 需要REX前缀
                rex = 0x40 | (1 << 2) | (REG_ENCODING.get(reg1, 0) & 0x8) >> 3 | (REG_ENCODING.get(reg2, 0) & 0x8) >> 3
                if dst.size == 8:
                    rex |= 0x08
                return bytes([rex]) + bytes([0x89]) + cls._encode_modrm(0, reg1, reg2)
            return bytes([0x89]) + cls._encode_modrm(0, reg1, reg2)
        
        # mov r64, [mem]
        if dst.type == 'reg' and src.type == 'mem':
            mem = src.value
            return bytes([0x48]) + cls._encode_modrm(0, dst.value, 'rax') + cls._encode_mem(mem)
        
        # mov [mem], r64
        if dst.type == 'mem' and src.type == 'reg':
            mem = dst.value
            return bytes([0x48]) + cls._encode_modrm(0, src.value, 'rax') + cls._encode_mem(mem)
        
        raise EncodeError(f"MOV不支持的操作数: {dst}, {src}")
    
    @classmethod
    def _encode_push(cls, ops: list[Operand]) -> bytes:
        """编码PUSH指令"""
        if not ops:
            return b'\x54'  # push rsp
        op = ops[0]
        
        if op.type == 'reg':
            reg = op.value
            # push r64
            if reg in ('rsp', 'rbp', 'rsi', 'rdi', 'rax', 'rbx', 'rcx', 'rdx'):
                return bytes([0x50 | REG_ENCODING[reg]])
            elif reg in ('r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15'):
                return bytes([0x41, 0x50 | REG_ENCODING[reg]])
        
        elif op.type == 'imm':
            if -128 <= op.value < 128:
                return bytes([0x6a]) + cls._encode_imm(op.value, 1)
            else:
                return bytes([0x68]) + cls._encode_imm(op.value, 4)
        
        return b'\x54'
    
    @classmethod
    def _encode_pop(cls, ops: list[Operand]) -> bytes:
        """编码POP指令"""
        if not ops:
            return b'\x5c'  # pop rsp
        op = ops[0]
        
        if op.type == 'reg':
            reg = op.value
            if reg in ('rsp', 'rbp', 'rsi', 'rdi', 'rax', 'rbx', 'rcx', 'rdx'):
                return bytes([0x58 | REG_ENCODING[reg]])
            elif reg in ('r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15'):
                return bytes([0x41, 0x58 | REG_ENCODING[reg]])
        
        return b'\x5c'
    
    @classmethod
    def _encode_arith(cls, instr: Instruction, op8: int, op32: int) -> bytes:
        """编码算术指令 (ADD/SUB)"""
        dst, src = instr.operands
        
        # add r64, imm8/imm32
        if dst.type == 'reg' and src.type == 'imm':
            if -128 <= src.value < 128:
                return bytes([0x83]) + cls._encode_modrm(op32 & 0xf8, 0, dst) + cls._encode_imm(src.value, 1)
            else:
                return bytes([0x81]) + cls._encode_modrm(op32 & 0xf8, 0, dst) + cls._encode_imm(src.value, 4)
        
        # add r64, r64
        if dst.type == 'reg' and src.type == 'reg':
            rex = 0x40
            if dst.size == 8:
                rex |= 0x08
            return bytes([rex, op32]) + cls._encode_modrm(0, dst.value, src.value)
        
        raise EncodeError(f"算术指令不支持的操作数")
    
    @classmethod
    def _encode_cmp(cls, instr: Instruction) -> bytes:
        """编码CMP指令"""
        dst, src = instr.operands
        
        # cmp r64, imm
        if dst.type == 'reg' and src.type == 'imm':
            if -128 <= src.value < 128:
                return bytes([0x83]) + cls._encode_modrm(0x38, 0, dst) + cls._encode_imm(src.value, 1)
            else:
                return bytes([0x81]) + cls._encode_modrm(0x38, 0, dst) + cls._encode_imm(src.value, 4)
        
        # cmp r64, r64
        if dst.type == 'reg' and src.type == 'reg':
            return bytes([0x48, 0x39]) + cls._encode_modrm(0, dst.value, src.value)
        
        raise EncodeError(f"CMP不支持的操作数")
    
    @classmethod
    def _encode_logic(cls, instr: Instruction, mnemonic: str) -> bytes:
        """编码逻辑指令"""
        dst, src = instr.operands
        op_map = {'AND': 0x20, 'OR': 0x08, 'XOR': 0x30}
        op = op_map[mnemonic]
        
        # xor r64, r64
        if dst.type == 'reg' and src.type == 'reg':
            return bytes([0x48, op | 0x01]) + cls._encode_modrm(0, dst.value, src.value)
        
        raise EncodeError(f"{mnemonic}不支持的操作数")
    
    @classmethod
    def _encode_test(cls, instr: Instruction) -> bytes:
        """编码TEST指令"""
        dst, src = instr.operands
        
        if dst.type == 'reg' and src.type == 'reg':
            return bytes([0x48, 0x85]) + cls._encode_modrm(0, dst.value, src.value)
        
        raise EncodeError("TEST不支持的操作数")
    
    @classmethod
    def _encode_jcc(cls, ops: list[Operand], opcode: int) -> bytes:
        """编码条件跳转"""
        if not ops or ops[0].type != 'imm':
            raise EncodeError("跳转指令需要立即数偏移")
        offset = ops[0].value
        return bytes([opcode]) + cls._encode_imm(offset, 1)
    
    @classmethod
    def _encode_jmp(cls, ops: list[Operand]) -> bytes:
        """编码JMP指令"""
        if not ops:
            return b'\xeb\x00'
        op = ops[0]
        
        if op.type == 'imm':
            offset = op.value
            if -128 <= offset < 128:
                return bytes([0xeb]) + cls._encode_imm(offset, 1)
            else:
                return bytes([0xe9]) + cls._encode_imm(offset, 4)
        elif op.type == 'reg':
            # 间接跳转
            return bytes([0xff]) + cls._encode_modrm(0x20, 0, op.value)
        
        return b'\xeb\x00'
    
    @classmethod
    def _encode_call(cls, ops: list[Operand]) -> bytes:
        """编码CALL指令"""
        if not ops:
            return b'\xc3'
        op = ops[0]
        
        if op.type == 'imm':
            offset = op.value
            return bytes([0xe8]) + cls._encode_imm(offset, 4)
        elif op.type == 'reg':
            return bytes([0xff]) + cls._encode_modrm(0x10, 0, op.value)
        
        return b'\xc3'
    
    @classmethod
    def _encode_unary(cls, instr: Instruction, op8: int, op32: int) -> bytes:
        """编码单操作数指令"""
        op = instr.operands[0]
        if op.type == 'reg':
            return bytes([0x48, op32]) + cls._encode_modrm(0x10, 0, op.value)
        raise EncodeError("单操作数指令需要寄存器")
    
    @classmethod
    def _encode_inc_dec(cls, instr: Instruction, op8: int, op32: int) -> bytes:
        """编码INC/DEC指令"""
        op = instr.operands[0]
        if op.type == 'reg':
            return bytes([0x48, op32]) + cls._encode_modrm(0x10, 0, op.value)
        raise EncodeError("INC/DEC需要寄存器")
    
    @classmethod
    def _encode_modrm(cls, modrm_byte: int, reg: str, rm: str) -> bytes:
        """编码ModR/M字节"""
        reg_enc = REG_ENCODING.get(reg, reg)
        rm_enc = REG_ENCODING.get(rm, rm)
        
        modrm = ((modrm_byte & 0x38) & 0x38) | ((reg_enc & 7) << 3) | (rm_enc & 7)
        return bytes([modrm])
    
    @classmethod
    def _encode_mem(cls, mem: tuple) -> bytes:
        """编码内存操作数"""
        reg, disp, scale = mem
        sib = 0x04 | (scale << 6) | (REG_ENCODING.get('sp', 4) << 3) | REG_ENCODING.get(reg, 0)
        return bytes([sib]) + cls._encode_imm(disp, 4)
    
    @staticmethod
    def _encode_imm(value: int, size: int) -> bytes:
        """编码立即数"""
        value = value & ((1 << (size * 8)) - 1)
        return value.to_bytes(size, 'little', signed=(value >= 1 << (size * 8 - 1)))


class EncodeError(Exception):
    """编码错误"""
    pass
