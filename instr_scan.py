from pyhcl import *
import ariane_pkg::*

# ******* 余宛书 8.31 Begin ******* #

class riscv:
    OpcodeBranch = U.w(7)(99)
    OpcodeJalr = U.w(7)(103)
    OpcodeJal = U.w(7)(111)
    OpcodeC1J = U.w(3)(5)
    OpcodeC1 = U.w(2)(1)
    OpcodeC2JalrMvAdd = U.w(3)(4)
    OpcodeC1Beqz = U.w(3)(6)
    OpcodeC1Bnez =U.w(3)(7)

class ariane_pkg:
    '''
    function automatic logic [riscv::VLEN-1:0] uj_imm (logic [31:0] instruction_i);
        return { {44+riscv::VLEN-64 {instruction_i[31]}}, instruction_i[19:12], instruction_i[20], instruction_i[30:21], 1'b0 };
    endfunction
    '''
    def uj_imm (instruction_i):
        temp = Wire(U.w(44))
        for i in range(44):
            temp[U(i)] = instruction_i[31]
        return CatBits(temp, instruction_i[19:12], instruction_i[20], instruction_i[30:21], U(0))

    '''
    function automatic logic [riscv::VLEN-1:0] sb_imm (logic [31:0] instruction_i);
        return { {51+riscv::VLEN-64 {instruction_i[31]}}, instruction_i[31], instruction_i[7], instruction_i[30:25], instruction_i[11:8], 1'b0 };
    endfunction
    '''
    def sb_imm (instruction_i):
        temp = Wire(U.w(52))
        for i in range(52):
            temp[U(i)] = instruction_i[31]
        return CatBits(temp, instruction_i[7], instruction_i[30:25], instruction_i[11:8], U(0))

# Instruction Scanner
class instr_scan (Module):
    io = IO(
    instr_i=Input(U.w(32)), # expect aligned instruction, compressed or not
    rvi_return_o=Output(Bool),
    rvi_call_o=Output(Bool),
    rvi_branch_o=Output(Bool),
    rvi_jalr_o=Output(Bool),
    rvi_jump_o=Output(Bool),
    rvi_imm_o=Output(U.w(64)),
    rvc_branch_o=Output(Bool),
    rvc_jump_o=Output(Bool),
    rvc_jr_o=Output(Bool),
    rvc_return_o=Output(Bool),
    rvc_jalr_o=Output(Bool),
    rvc_call_o=Output(Bool),
    rvc_imm_o=Output(U.w(64))
    )

    is_rvc = Wire(Bool) #logic is_rvc
    is_rvc <<= (io.instr_i[U(1)] != U.w(2)(3))
    
    # check that rs1 is either x1 or x5 and that rd is not rs1
    io.rvi_return_o <<= io.rvi_jalr_o & ((io.instr_i[19:15] == U(1)) | io.instr_i[19:15] == U(5)) #?5'd1和5'd5
                                     & (io.instr_i[19:15] != io.instr_i[11:7])
                                     
    # Opocde is JAL[R] and destination register is either x1 or x5
    io.rvi_call_o <<= (io.rvi_jalr_o | io.rvi_jump_o) & ((io.instr_i[11:7] == U(1)) | io.instr_i[11:7] == U(5)) #?5'd1和5'd5
    # differentiates between JAL and BRANCH opcode, JALR comes from BHT

    # io.rvi_imm_o    = (io.instr_i[3]) ? ariane_pkg::uj_imm(io.instr_i) : ariane_pkg::sb_imm(io.instr_i) 
    if io.instr_i[U(3)]:
        io.rvi_imm_o <<= ariane_pkg.uj_imm(io.instr_i)
    else:
        io.rvi_imm_o <<= ariane_pkg.sb_imm(io.instr_i)
        
    io.rvi_branch_o <<= (io.instr_i[6:0] == riscv.OpcodeBranch)
    io.rvi_jalr_o <<= (io.instr_i[6:0] == riscv.OpcodeJalr)
    io.rvi_jump_o <<= (io.instr_i[6:0] == riscv.OpcodeJal)
    
    # opcode JAL
    io.rvc_jump_o <<= (io.instr_i[15:13] == riscv.OpcodeC1J) & io.is_rvc & (io.instr_i[1:0] == riscv.OpcodeC1)
    # always links to register 0
    is_jal_r <<= Wire(Bool) #logic is_jal_r 
    is_jal_r <<= (instr_i[15:13] == riscv.OpcodeC2JalrMvAdd) & (io.instr_i[6:2] == U.w(5)(0)) & (io.instr_i[1:0] == riscv.OpcodeC2) & is_rvc
    io.rvc_jr_o <<= is_jal_r & ~io.instr_i[12]
    # always links to register 1 e.g.: it is a jump
    io.rvc_jalr_o <<= is_jal_r & io.instr_i[12]
    io.rvc_call_o <<= io.rvc_jalr_o

    io.rvc_branch_o <<= ((io.instr_i[15:13] == riscv.OpcodeC1Beqz) | (io.instr_i[15:13] == riscv.OpcodeC1Bnez)) & (io.instr_i[1:0] == riscv.OpcodeC1) & is_rvc
    # check that rs1 is x1 or x5
    io.rvc_return_o <<= ((io.instr_i[11:7] == U(1)) | (instr_i[11:7] == U(5)))  & io.rvc_jr_o #?5'd1和5'd5

    # differentiates between JAL and BRANCH opcode, JALR comes from BHT
    '''
    io.rvc_imm_o <<= (io.instr_i[14]) ? {{56+riscv::VLEN-64{io.instr_i[12]}}, io.instr_i[6:5], io.instr_i[2], io.instr_i[11:10], io.instr_i[4:3], U(0)}
                                       : {{53+riscv::VLEN-64{io.instr_i[12]}}, io.instr_i[8], io.instr_i[10:9], io.instr_i[6], io.instr_i[7], io.instr_i[2], io.instr_i[11], io.instr_i[5:3], U(0)}
    '''
    temp56 = Wire(U.w(56))
    temp53 = Wire(U.w(53))
    for i in range(56):
            temp56[U(i)] = io.instr_i[U(12)]
    for i in range(53):
            temp53[U(i)] = io.instr_i[U(12)]
    if io.instr_i[U(14)]:
        io.rvc_imm_o <<= CatBits(temp56, io.instr_i[6:5], io.instr_i[2], io.instr_i[11:10], io.instr_i[4:3], U(0))
    else:
        io.rvc_imm_o <<= CatBits(temp53, io.instr_i[8], io.instr_i[10:9], io.instr_i[6], io.instr_i[7], io.instr_i[2], io.instr_i[11], io.instr_i[5:3], U(0))

# ⽣成Verilog⽂件
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(instr_scan()), "instr_scan.fir"))


# ******* 余宛书 9.8 End ******* #
