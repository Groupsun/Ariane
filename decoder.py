# 9.6:
# 由于有队友未提交代码以及未完成/未测试
# 只是简单地把小组代码复制到一起


# ********** 郑学钿 2020.8.27,28 Begin ********** #
import id_stage_8_31.header_for_id_stage

class logic_packed_1():
    NOIMM, IIMM, SIMM, SBIMM, UIMM, JIMM, RS3
    dtype = Wire(U.w(4))

class decoder(Module):
    io = IO(
        debug_req_i = Input(Bool),                                  # external debug request
        pc_i = Input(U.w(riscv.VLEN)),                              # PC from IF
        is_compressed_instr_i = Input(Bool),                        # is a compressed instruction
        compressed_instr_i = Input(16),                             # compressed form of instruction
        is_illegal_i = Input(Bool),                                 # illegal compressed instruction
        instruction_i = Input(U.w(32)),                             # instruction from IF
        branch_predict_i = Input(ariane_pkg.branchpredict_sbe_t),
        ex_i = Input(ariane_pkg.exception_t),                       # if an exception occured in if
        irq_i = Input(U.w(2)),                                      # external interrupt
        irq_ctrl_i = Input(ariane_pkg.irq_ctrl_i),                  # interrupt control and status information from CSRs
        # From CSR
        priv_lvl_i = Input(riscv.priv_lvl_t),                       # current privilege level
        debug_mode_i = Input(Bool),                                 # we are in debug mode
        fs_i = Input(riscv.xs_t),                                   # floating point extension status
        frm_i = Input(U.w(3)),                                      # floating-point dynamic rounding mode
        tvm_i = Input(Bool),                                        # trap virtual memory
        tw_i = Input(Bool),                                         # timeout wait
        tsr_i = Input(Bool),                                        # trap sret
        instruction_o = Output(ariane_pkg.scoreboard_entry_t),      # scoreboard entry to scoreboard
        is_control_flow_instr_o = Output(Bool)                      # this instruction will change the control flow
    )
    illegal_instr = Wire(Bool)
    # this instruction is an environment call (ecall), it is handled like an exception
    ecall = Wire(Bool)
    # this instruction is a software break-point
    ebreak = Wire(Bool)
    # this instruction needs floating-point rounding-mode verification
    check_fprm = Wire(Bool)
    instr = Wire(riscv.instruction_t)
    instr <<= instruction_i
    # --------------------
    # Immediate select
    # --------------------
    imm_select = logic_packed_1()

    imm_i_type = Wire(U.w(64))
    imm_s_type = Wire(U.w(64))
    imm_sb_type = Wire(U.w(64))
    imm_u_type = Wire(U.w(64))
    imm_uj_type = Wire(U.w(64))
    imm_bi_type = Wire(U.w(64))

# ********** 郑学钿 2020.8.27,28 End ********** #

# ********** 郑学钿 2020.9.2 Begin ********** #
    # decoder

    imm_select <<= NOIMM
    is_control_flow_instr_o <<= U(0)
    illegal_instr <<= U(0)
    instruction_o.pc <<= pc_i
    instruction_o.trans_id <<= U(0)
    instruction_o.fu <<= NONE
    instruction_o.op <<= ariane_pkg.ADD
    instruction_o.rs1 <<= U(0)
    instruction_o.rs2 <<= U(0)
    instruction_o.rd <<= U(0)
    instruction_o.use_pc <<= U(0)
    instruction_o.trans_id <<= U(0)
    instruction_o.is_compressed <<= is_compressed_i
    instruction_o.use_zimm <<= U(0)
    instruction_o.bp <<= branch_predict_i;
    ecall <<= U(0)
    ebreak <<= U(0)
    check_fprm <<= U(0)

    with when(ex_i.valid == Bool(false)):
        with when(instr.rtype.opcode == riscv.OpcodeSystem):
            instrucion_o.fu <<= CSR
            instrucion_o.rs1 <<= instr.itype.rs1  # 后续看需不需要切片
            instruction_o.rd  <<= instr.itype.rd
            with when(instr.itype.funct3 == U.w(3)(0)):
                #check if the RD and and RS1 fields are zero, this may be reset for the SENCE.VMA instruction
                with when(instr.itype.rs1 != U(0) | instr.itype.rd != U(0)):
                    illegal_instr <<= U.w(1)(1)
                # decode the immiediate field

                # ECALL -> inject exception
                with when(instr.itype.imm == U.w(12)(0)):
                    ecall <<= U.w(1)(1)

                # EBREAK -> inject exception
                elsewhen(instr.itype.imm == U.w(12)(1)):
                    ebreak <<= U.w(1)(1)

                # SRET
                elsewhen(instr.itype.imm == U.w(12)(258)):
                    instruction_o.op = ariane_pkg.SRET
                    # check privilege level, SRET can only be executed in S and M mode
                    # we'll just decode an illegal instruction if we are in the wrong privilege level
                    with when(priv_lvl_i == riscv.PRIV_LVL_U):
                        illegal_instr <<= U.w(1)(1)
                        # do not change privilege level if this is an illegal instruction
                        instruction_o.op = ariane_pkg.ADD #<<=还是=

                    # if we are in S-Mode and Trap SRET (tsr) is set -> trap on illegal instruction
                    with when(priv_lvl_i == riscv.PRIV_LVL_S & tsr_i):
                        illegal_instr = U.w(1)(1)
                        # do not change privilege level if this is an illegal instruction
                        instruction_o.op = ariane_pkg.ADD #<<=还是=

                # MRET
                elsewhen(instr.itype.imm == U.w(12)(770)):
                    instruction_o.op = ariane_pkg.MRET;
                    # check privilege level, MRET can only be executed in M mode
                    # otherwise we decode an illegal instruction
                    with when(priv_lvl_i == riscv.PRIV_LVL_U | priv_lvl_i == riscv.PRIV_LVL_S):
                        illegal_instr = U.w(1)(1)

                # DRET
                elsewhen(instr.itype.imm == U.w(12)(1970)):
                    instruction_o.op = ariane_pkg.DRET;
                    # check that we are in debug mode when executing this instruction
                    illegal_instr = U.w(1)(1) if debug_mode_i == Bool(false) else U.w(1)(0)

                # WFI
                elsewhen(instr.itype.imm == U.w(12)(261)):
                    with when(ENABLE_WFI == Bool(true)):
                        instruction_o.op <<= ariane_pkg.WFI
                    # if timeout wait is set, trap on an illegal instruction in S Mode
                    # (after 0 cycles timeout)
                    with when(priv_lvl_i == riscv.PRIV_LVL_S & tw_i == Bool(true)):
                        illegal_instr <<= U.w(1)(1)
                        instruction_o.op <<= ariane_pkg.ADD
                    # we don't support U mode interrupts so WFI is illegal in this context
                    with when(priv_lvl_i == riscv.PRIV_LVL_U):
                        illegal_instr <<= U.w(1)(1)
                        instruction_o.op <<= ariane_pkg.ADD
                
                # SFENCE.VMA
                with otherwise():
                    with when(instr.instr[31:25] == U.w(7)(9)):
                    # check privilege level, SFENCE.VMA can only be executed in M/S mode
                    # otherwise decode an illegal instruction
                        illegal_instr <<= U.w(1)(0) if priv_lvl_i == riscv.PRIV_LVL_M | priv_lvl_i == riscv.PRIV_LVL_S else U.w(1)(1)
                        instruction_o.op <<= ariane_pkg.SFENCE_VMA
                        # check TVM flag and intercept SFENCE.VMA call if necessary
                        with when(priv_lvl_i == riscv.PRIV_LVL_S & tvm_i == Bool(true))
                            illegal_instr <<= U.w(1)(1)
            
            # atomically swaps values in the CSR and integer register
            # CSRRW
            elsewhen(instr.itype.funct3 == U.w(3)(1)):
                imm_select <<= IIMM
                instruction_o.op <<= ariane_pkg.CSR_WRITE

            # atomically set values in the CSR and write back to rd
            # CSRRS
            elsewhen(instr.itype.funct3 == U.w(3)(2)):
                imm_select <<= IIMM
                # this is just a read
                with when(instr.itype.rs1 == U.w(5)(0)):
                    instruction_o.op <<= ariane_pkg.CSR_READ
                with otherwise():
                    instruction_o.op <<= ariane_pkg.CSR_SET
            
            # atomically clear values in the CSR and write back to rd
            # CSRRC
            elsewhen(instr.itype.funct3 == U.w(3)(3)):
                imm_select <<= IIMM
                # this is just a read
                with when(instr.itype.rs1 == U.w(5)(0)):
                    instruction_o.op <<= ariane_pkg.CSR_READ
                with otherwise():
                    instruction_o.op <<= ariane_pkg.CSR_CLEAR

            # use zimm and iimm
            # CSRRWI
            elsewhen(instr.itype.funct3 == U.w(3)(5)):
                instruction_o.rs1[4:0] <<= instr.itype.rs1
                imm_select <<= IIMM
                instruction_o.use_zimm <<= U.w(1)(1)
                instruction_o.op <<= ariane_pkg.CSR_WRITE

            # CSRRSI
            elsewhen(instr.itype.funct3 == U.w(3)(6)):
                instruction_o.rs1[4:0] <<= instr.itype.rs1
                imm_select <<= IIMM
                instruction_o.use_zimm = U.w(1)(1)
                # this is just a read
                with when(instr.itype.rs1 == U.w(5)(0)):
                    instruction_o.op <<= ariane_pkg.CSR_READ
                with otherwise():
                    instruction_o.op <<= ariane_pkg.CSR_CLEAR
            with otherwise():
                illegal_instr <<= U.w(1)(1)
# ********** 郑学钿 2020.9.2 End ********** #

# **********  麦谟师 8.30 Begin ********** #

from pyhcl import *


class fu_op:
    # basic ALU op 4
    ADD, SUB, ADDW, SUBW = U(0), U(1), U(2), U(3)
    # logic operations 3
    XORL, ORL, ANDL = U(4), U(5), U(6)
    # shifts 6
    SRA, SRL, SLL, SRLW, SLLW, SRAW = U(7), U(8), U(9), U(10), U(11), U(12)
    # comparisons 6
    LTS, LTU, GES, GEU, EQ, NE = U(13), U(14), U(15), U(16), U(17), U(18)
    # jumps 2
    JALR, BRANCH = U(19), U(20)
    # set lower than operations 2
    SLTS, SLTU = U(21), U(22)
    # CSR functions 12
    MRET, SRET, DRET, ECALL, WFI, FENCE, FENCE_I, SFENCE_VMA, CSR_WRITE, CSR_READ, CSR_SET, CSR_CLEAR = U(23), U(24), U(
        25), U(26), U(27), U(28), U(29), U(30), U(31), U(32), U(33), U(34)
    # LSU functions 11
    LD, SD, LW, LWU, SW, LH, LHU, SH, LB, SB, LBU = U(35), U(36), U(37), U(38), U(39), U(40), U(41), U(42), U(43), U(
        44), U(45)
    # Atomic Memory Operations 4 9 9
    AMO_LRW, AMO_LRD, AMO_SCW, AMO_SCD = U(46), U(47), U(48), U(49)
    AMO_SWAPW, AMO_ADDW, AMO_ANDW, AMO_ORW, AMO_XORW, AMO_MAXW, AMO_MAXWU, AMO_MINW, AMO_MINWU = U(50), U(51), U(52), U(
        53), U(54), U(55), U(56), U(57), U(58)
    AMO_SWAPD, AMO_ADDD, AMO_ANDD, AMO_ORD, AMO_XORD, AMO_MAXD, AMO_MAXDU, AMO_MIND, AMO_MINDU = U(59), U(60), U(61), U(
        62), U(63), U(64), U(65), U(66), U(67)
    # Multiplications 5
    MUL, MULH, MULHU, MULHSU, MULW = U(68), U(69), U(70), U(71), U(72)
    # Divisions 8
    DIV, DIVU, DIVW, DIVUW, REM, REMU, REMW, REMUW = U(73), U(74), U(75), U(76), U(77), U(78), U(79), U(80)
    # Floating-Point Load and Store Instructions 8
    FLD, FLW, FLH, FLB, FSD, FSW, FSH, FSB = U(81), U(82), U(83), U(84), U(85), U(86), U(87), U(88)
    # Floating-Point Computational Instructions 10
    FADD, FSUB, FMUL, FDIV, FMIN_MAX, FSQRT, FMADD, FMSUB, FNMSUB, FNMADD = U(89), U(90), U(91), U(92), U(93), U(94), U(
        95), U(96), U(97), U(98)
    # Floating-Point Conversion and Move Instructions 6
    FCVT_F2I, FCVT_I2F, FCVT_F2F, FSGNJ, FMV_F2X, FMV_X2F = U(99), U(100), U(101), U(102), U(103), U(104)
    # Floating-Point Compare Instructions 1
    FCMP = U(105)
    # Floating-Point Classify Instruction 1
    FCLASS = U(106)
    # Vectorial Floating-Point Instructions that don't directly map onto the scalar ones 15
    VFMIN, VFMAX, VFSGNJ, VFSGNJN, VFSGNJX, VFEQ, VFNE, VFLT, VFGE, VFLE, VFGT, VFCPKAB_S, VFCPKCD_S, VFCPKAB_D, VFCPKCD_D = U(
        107), U(108), U(109), U(110), U(111), U(112), U(113), U(114), U(115), U(116), U(117), U(118), U(119), U(120), U(
        121)


class fu_t:
    NONE = U.w(4)(0)
    LOAD = U.w(4)(1)
    STROE = U.w(4)(2)
    ALU = U.w(4)(3)
    CTRL_FLOW = U.w(4)(4)
    MULT = U.w(4)(5)
    CSR = U.w(4)(6)
    FPU = U.w(4)(7)
    FPU_VEC = U.w(4)(8)


class irg_ctrl_t:
    mie = U.w(64)
    mip = U.w(64)
    mideleg = U.w(64)
    sie = U.w(1)
    global_enable = U.w(1)


atype_t = U.w(32)(0)


class atype_t:
    funct5 = atype_t[31:27]
    aq = atype_t[26]
    r1 = atype_t[25]
    rs2 = atype_t[24:20]
    rs1 = atype_t[19:15]
    funct3 = atype_t[14:12]
    rd = atype_t[11:7]
    pocode = atype_t[6:0]


utype_t = U.w(32)(0)


class utype_t:
    funct3 = utype_t[31:12]
    rd = utype_t[11:7]
    pocode = utype_t[6:0]


stype_t = U.w(32)(0)


class stype_t:
    imm = stype_t[31:25]
    rs2 = stype_t[24:20]
    rs1 = stype_t[19:15]
    funct3 = stype_t[14:12]
    imm0 = stype_t[11:7]
    pocode = stype_t[6:0]


itype_t = U.w(32)(0)


class itype_t:
    imm = itype_t[31:20]
    rs1 = itype_t[19:15]
    funct3 = itype_t[14:12]
    rd = itype_t[11:7]
    pocode = itype_t[6:0]


rvftype_t = U.w(32)(0)


class rvftype_t:
    funct2 = rvftype_t[31:30]
    vecfltop = rvftype_t[29:25]
    rs2 = rvftype_t[24:20]
    rs1 = rvftype_t[19:15]
    repl = rvftype_t[14]
    vmft = rvftype_t[13:12]
    rd = rvftype_t[11:7]
    pocode = rvftype_t[6:0]


rftype_t = U.w(32)(0)


class rftype_t:
    funct5 = rftype_t[31:27]
    fmt = rftype_t[26:25]
    rs2 = rftype_t[24:20]
    rs1 = rftype_t[19:15]
    rm = rftype_t[14:12]
    rd = rftype_t[11:7]
    pocode = rftype_t[6:0]


r4type_t = U.w(32)(0)


class r4type_t:
    rs3 = r4type_t[31:27]
    funct2 = r4type_t[26:25]
    rs2 = r4type_t[24:20]
    rs1 = r4type_t[19:15]
    funct3 = r4type_t[14:12]
    rd = r4type_t[11:7]
    pocode = r4type_t[6:0]


rtype_t = U.w(32)(0)


class rtype_t:
    funct7 = rtype_t[31:25]
    rs2 = rtype_t[24:20]
    rs1 = rtype_t[19:15]
    funct3 = rtype_t[14:12]
    rd = rtype_t[11:7]
    opcode = rtype_t[6:0]


class scoreboard_entry_t:
    fu = fu_t()
    op = fu_op()
    rs1 = RegInit(U.w(6)(0))
    rs2 = RegInit(U.w(6)(0))
    rd = RegInit(U.w(6)(0))
    op = fu_op()


class instruction_t:
    instr = U.w(32)
    rtype = rtype_t()
    r4type = r4type_t()
    rftype = rftype_t()
    rvftype = rvftype_t()
    itype = itype_t()
    stype = stype_t()
    utype = utype_t()
    atype = atype_t()


class xs_t:
    Off = U.w(2)(0)
    Initial = U.w(2)(1)
    Clean = U.w(2)(2)
    Dirty = U.w(2)(3)


class imm_select:
    NOIMM = U.w(3)(0)
    IIMM = U.w(3)(1)
    SIMM = U.w(3)(2)
    SBIMM = U.w(3)(3)
    UIMM = U.w(3)(4)


class decode(Module):
    io = IO(
        frm_i=Input(U.w(3)),
        fs_i=Input(xs_t()),
        irg_ctrl_i=Input(irg_ctrl_t()),
        instruction_o=Output(scoreboard_entry_t),
        is_control_flow_instr_o=Output(U.w(1)(0))
    )
    ALU = U.w(3)(3)
    CTRL_FLOW = U.w(3)(4)
    OpcodeOpFp = U.w(7)(83)
    OpcodeBranch = U.w(7)(99)
    OpcodeJalr = U.w(7)(103)
    OpcodeJal = U.w(7)(111)
    OpcodeAuipc = U.w(7)(23)
    OpcodeLui = U.w(7)(55)
    illegal_instr = U.w(1)
    check_fprm = U.w(1)
    instr = instruction_t()
    none = U.w(1)
    Off = U.w(2)(0)
    RVF = U.w(1)(1)
    RVD = U.w(1)(1)
    XF16 = U.w(1)(0)
    XF16ALT = U.w(1)(0)
    XF8 = U.w(1)(0)
    FP_PRESENT = U.w(1)(0)
    FP_PRESENT <<= RVF + RVD + XF16 + XF16ALT + XF8
    with when(instr.rtype.opcode == OpcodeOpFp):
        with when(FP_PRESENT and io.fs_i != Off):
            io.instruction_o.fu <<= fu_t.FPU
            io.instruction_o.rs1 <<= instr.rftype.rs1
            io.instruction_o.rs2 <<= instr.rftype.rs2
            io.instruction_o.rd <<= instr.rftype.rd
            check_fprm <<= U(1)
            with when(instr.rftype.funct5 == U(0)):
                io.instruction_o.op <<= fu_op.FADD
                io.nstruction_o.rs1 <<= U(0)
                io.instruction_o.rs2 <<= instr.rftype.rs1
                imm_select = imm_select.IIMM
            with elsewhen(instr.rftype.funct5 == U(1)):
                io.instruction_o.op <<= fu_op.FSUB
                io.instruction_o.rs1 <<= U(0)
                io.instruction_o.rs2 <<= instr.rftype.rs1
                imm_select = imm_select.IIMM
            with elsewhen(instr.rftype.funct5 == U(2)):
                io.insdtruction_o.op <<= fu_op.FMUL
            with elsewhen(instr.rftype.funct5 == U(3)):
                io.instruction_o.op <<= fu_op.FDIV
            with elsewhen(instr.rftype.funct5 == U(11)):
                io.instruction_o.op <<= fu_op.FSQRT
                with when(instr.rftype.rs2 != U(0)):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(5)):
                io.instruction_o.op <<= fu_op.FSGNJ
                check_fprm <<= U(1)
                with when(XF16ALT):
                    with when(instr.rftype.rm < U.w(3)(0) or (
                            U.w(3)(2) < instr.rftype.rm < U.w(3)(4)) or instr.rftype.rm > U.w(3)(6)):
                        illegal_instr <<= U(1)
                with otherwise():
                    none <<= U(0)
                with when(instr.rftype.rm < U.w(3)(0) or instr.rftype.rm < U.w(3)(2)):
                    illegal_instr <<= U(1)

            with elsewhen(instr.rftype.funct5 == U(5)):
                io.instruction_o.op <<= fu_op.FMIN_MAX
                check_fprm = U(1)
                with when(XF16ALT):
                    with when(instr.rftype.rm < U.w(3)(0) or (
                            U.w(3)(1) < instr.rftype.rm < U.w(3)(4)) or instr.rftype.rm > U.w(3)(5)):
                        illegal_instr <<= U(1)
                with otherwise():
                    with when(instr.rftype.rm < U.w(3)(0) or instr.rftype.rm < U.w(3)(1)):
                        illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(8)):
                io.instruction_o.op = fu_op.FCVT_F2F
                io.instrction_o.rs2 = instr.rftype.rs1
                imm_select = imm_select.IIMM
                with when(instr.rftype.rs2[24:23]):
                    illegal_instr <<= U(1)
                with when(instr.rftype.rs2[22:20] == U.w(3)(0)):
                    with when(~RVF):
                        illegal_instr <<= U(1)
                with elsewhen(instr.rftype.rs2[22:20] == U.w(3)(1)):
                    with when(~RVD):
                        illegal_instr <<= U(1)
                with elsewhen(instr.rftype.rs2[22:20] == U.w(3)(2)):
                    with when(~XF16):
                        illegal_instr <<= U(1)
                with elsewhen(instr.rftype.rs2[22:20] == U.w(3)(3)):
                    with when(~XF16ALT):
                        illegal_instr <<= U(1)
                with elsewhen(instr.rftype.rs2[22:20] == U.w(3)(6)):
                    with when(~XF8):
                        illegal_instr <<= U(1)
                with otherwise():
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(20)):
                io.instruction_o.op = fu_op.FCMP
                check_fprm <<= U(1)
                with when(XF16ALT):
                    with when(instr.rftype.rm < U.w(3)(0) or (
                            U.w(3)(2) < instr.rftype.rm < U.w(3)(4)) or instr.rftype.rm > U.w(3)(6)):
                        illegal_instr <<= U(1)
                with otherwise():
                    with when(instr.rftype.rm < U.w(3)(0) or instr.rftype.rm < U.w(3)(2)):
                        illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(24)):
                io.instruction_o.op <<= fu_op.FCVT_F2I
                imm_select = imm_select.IIMM
                with when(instr.rftype.rs2[24:22]):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(26)):
                io.instruction_o.rs2 <<= instr.rftype.rs1
                check_fprm = U(0)
                with when(instr.rftype.rm == U(0) or (XF16ALT and instr.rftype.rm == U(4))):
                    io.instruction_o.op <<= fu_op.FMV_F2X
                with elsewhen(instr.rftype.rm == U(1) or (XF16ALT and instr.rftype.rm == U(5))):
                    io.instruction_o.op <<= fu_op.FCLASS
                with otherwise():
                    illegal_instr <<= U(1)
                with when(instr.rftype.rs2 != U(0)):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.funct5 == U(30)):
                io.instruction_o.op <<= fu_op.FMV_X2F
                io.instruction_o.rs2 <<= instr.rftype.rs1
                check_fprm <<= U(1)
                with when(instr.rftype.rm == U(0) or (XF16ALT and instr.rftype.rm == U(4))):
                    io.instruction_o.op <<= fu_op.FMV_F2X
                with when(instr.rftype.rs2 != U(0)):
                    illegal_instr <<= U(1)
            with otherwise():
                illegal_instr <<= U(1)
            with when(instr.rftype.fmt == U.w(2)(0)):
                with when(~RVF):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.fmt == U.w(2)(1)):
                with when(~RVD):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.fmt == U.w(2)(2)):
                with when(~XF16 and ~XF16ALT):
                    illegal_instr <<= U(1)
            with elsewhen(instr.rftype.fmt == U.w(2)(3)):
                with when(~XF16ALT):
                    illegal_instr <<= U(1)
            with otherwise():
                illegal_instr <<= U(1)
            with when(check_fprm):
                with when(U(0) <= instr.rftype.rm <= U(4)):
                    none <<= U(0)
                with elsewhen(instr.rftype.rm == U(5)):
                    with when(~XF16ALT or instr.rftype.fmt != U(2)):
                        illegal_instr <<= U(1)
                    with when(U(0) <= io.frm_i <= U(4)):
                        none <<= U(0)
                    with otherwise():
                        illegal_instr <<= U(1)
                with elsewhen(instr.rftype.rm == U(7)):
                    with when(U(0) <= io.frm_i <= U(4)):
                        none <<= U(1)
                    with otherwise():
                        illegal_instr <<= U(1)
                with otherwise():
                    illegal_instr <<= U(1)
        with otherwise():
            illegal_instr <<= U(1)
    with when(instr.rtype.opcode == OpcodeBranch):
        imm_select = imm_select.SBIMM
        io.instruction_o.fu <<= CTRL_FLOW
        io.instruction_o.rs1 <<= instr.stype.rs1
        io.instruction_o.rs2 <<= instr.stype.rs2
        io.is_control_flow_instr_o <<= U(1)
        with when(instr.stype.funct3 == U(0)):
            io.instruction_o.op <<= fu_op.EQ
        with elsewhen(instr.stype.funct3 == U(1)):
            io.instruction_o.op <<= fu_op.NE
        with elsewhen(instr.stype.funct3 == U(4)):
            io.instruction_o.op <<= fu_op.LTS
        with elsewhen(instr.stype.funct3 == U(5)):
            io.instruction_o.op <<= fu_op.GES
        with elsewhen(instr.stype.funct3 == U(6)):
            io.instruction_o.op <<= fu_op.LTU
        with elsewhen(instr.stype.funct3 == U(7)):
            io.instruction_o.op <<= fu_op.GEU
        with otherwise():
            io.is_control_flow_instr_o <<= U(0)
    with elsewhen(instr.rtype.opcode == OpcodeJalr):
        io.instruction_o.fu <<= CTRL_FLOW
        io.instruction_o.op <<= fu_op.JALR
        io.instruction_o.rs1 <<= instr.stype.rs1
        imm_select = imm_select.IIMM
        io.instruction_o.rd <<= instr.itype.rd
        io.is_control_flow_instr_o <<= U(1)
        with when(instr.itype.funct3 != U(0)):
            illegal_instr <<= U(1)
        with elsewhen(instr.rtype.opcode == OpcodeJal):
            io.instruction_o.fu <<= ALU
            imm_select = imm_select.JIMM
            io.instruction_o.rd <<= instr.utype.rd
            io.is_control_flow_instr_o <<= U(1)
        with elsewhen(instr.rtype.opcode == OpcodeAuipc):
            io.instruction_o.fu <<= ALU
            imm_select = imm_select.UIMM
            io.instruction_o.use_pc <<= U(1)
        with elsewhen(instr.rtype.opcode == OpcodeJal):
            io.instruction_o.fu <<= ALU
            imm_select = imm_select.UIMM
            io.instruction_o.rd <<= instr.utype.rd
        with otherwise():
            illegal_instr <<= U(1)

# ********** 麦谟师 9.3 End    ********** #

# **********  麦谟师 9.3 Begin ********** #
class irg_ctrl_t:
    mie=U.w(64)
    mip=U.w(64)
    mideleg=U.w(64)
    sie=U.w(1)
    global_enable=U.w(1)



class scoreboard_entry_t:
    rs1 = RegInit(U.w(6)(0))
    rs2 = RegInit(U.w(6)(0))
    rd = RegInit(U.w(6)(0))
    op = fu_op()
    valid=U.w(1)



class xs_t:
    Off = U.w(2)(0)
    Initial = U.w(2)(1)
    Clean = U.w(2)(2)
    Dirty = U.w(2)(3)


class imm_select:
    NOIMM = U.w(3)(0)
    IIMM = U.w(3)(1)
    SIMM = U.w(3)(2)
    SBIMM = U.w(3)(3)
    UIMM = U.w(3)(4)



class exception_t:
    cause=U.w(64)
    tval=U.w(64)
    valid=U.w(1)

class priv_lvl_t:
    PRIV_LVL_M=U.w(2)(3)
    PRIV_LVL_S=U.w(2)(1)
    PRIV_LVL_U=U.w(2)(0)


class decode(Module):
    io = IO(
        compressed_instr_i=Input(U.w(16)),
        is_compressed_i=Input(U.w(1)),
        is_illegal_i=Input(U.w(1)),
        frm_i=Input(U.w(3)),
        fs_i=Input(xs_t()),
        irg_ctrl_i=Input(irg_ctrl_t()),
        priv_lvl_i=Input(U.w(2)),
        instruction_o=Output(scoreboard_entry_t()),
        is_control_flow_instr_o=Output(U.w(1))
    )
    ecall=U.w(1)(0)
    ebreak=U.w(1)(0)
    ex_i=exception_t()
    ALU = U.w(3)(3)
    CTRL_FLOW = U.w(3)(4)
    OpcodeOpFp = U.w(7)(83)
    OpcodeBranch = U.w(7)(99)
    OpcodeJalr = U.w(7)(103)
    OpcodeJal = U.w(7)(111)
    OpcodeAuipc = U.w(7)(23)
    OpcodeLui = U.w(7)(55)
    illegal_instr = U.w(1)
    check_fprm = U.w(1)
    none = U.w(1)
    Off = U.w(2)(0)
    RVF = U.w(1)(1)
    RVD = U.w(1)(1)
    XF16 = U.w(1)(0)
    XF16ALT = U.w(1)(0)
    XF8 = U.w(1)(0)
    FP_PRESENT = U.w(1)
    FP_PRESENT <<= RVF | RVD | XF16 | XF16ALT | XF8
    imm_select <<= U(0)
    interrupt_cause=Reg(Vec(64,U.w(32)))
    io.instruction_o.valid<<=io.instruction_o.ex.valid
    interrupt_cause<<=U(0)
    io.instruction_o.ex<<=ex_i
    with when(~ex_i.valid):
    with when(io.is_compressed_i):
        io.instruction_o.ex.valid<<={U(0),io.compressed_instr_i}
    with otherwise():
        io.instruction_o.ex.valid <<= {U(0), io.instruction_i}
    with when(illegal_instr or io.is_illegal_i):
        io.instruction_o.ex.valid<<=U(1)
        io.instruction_o.ex.cause=fu_op.ILLEGAL_INSTR
    with elsewhen(ecall):
        io.instruction_o.ex.valid<<=U(1)
        io.instruction_o.ex.cause<<=LookUpTable(io.priv_lvl_i,{
            U(3):fu_op.ENV_CALL_MMODE,
            U(1): fu_op.ENV_CALL_SMODE,
            U(0): fu_op.ENV_CALL_UMODE,
            ...:
        })
    with elsewhen(ebreak):
        io.instruction_o.ex.valid<<=U(1)
        io.instruction_o.ex.cause<<=fu_op.BREAKPOINT
    #?????

# **********  麦谟师 9.4 End ********** #

#**********<黄斯隆><8.29>Begin**********#
from pyhcl import *

// 32bit Reg-Reg Operations
class lregreg(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rs2=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct7=Input(U.w(7)),
        funct3=Input(U.w(3)),
        op=Output(U.w(4)),
        fu=Output(U.w(4)))
    rs1 = RegInit(U.w(32)(0))
    rs2 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    rs1 <<= io.rs1
    rs2 <<= io.rs2
    rd <<= io.rd
    with when(io.funct7 == U(0b000_0001):
        io.fu <<= MULT
    with otherwise():
        io.fu <<= ALU
    io.op <<= LookUpTable({io.funct7, io.funct3}, {
    {U(0b0000000), U(0b000)}: ariane_pkg::ADDW,
    {U(0b0100000), U(0b000)}: ariane_pkg::SUBW,
    {U(0b0000000), U(0b001)}: ariane_pkg::SLLW,
    {U(0b0000000), U(0b101)}: ariane_pkg::SRLW,
    {U(0b0100000), U(0b101)}: ariane_pkg::SRAW,
    {U(0b0000001), U(0b000)}: ariane_pkg::MULW,
    {U(0b0000001), U(0b100)}: ariane_pkg::DIVW,
    {U(0b0000001), U(0b101)}: ariane_pkg::DIVUW,
    {U(0b0000001), U(0b110)}: ariane_pkg::REMW,
    {U(0b0000001), U(0b111)}: ariane_pkg::REMUW,
    ...: U(0b1)})

// Reg-Immediate Operations 
class regimm(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct3=Input(U.w(7)),
        instr=Input(U.w(6)),
        op=Output(U.w(4)),
        imm_select=Output(U.w(4)),
        fu=Output(U.w(4)),
        illegal_instr=Output(U.w(1)))
    rs1 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    rs1 <<= io.rs1
    rd <<= io.rd
    io.fu <<= ALU
    io.imm_select <<= IIMM;
    io.op <<= LookUpTable({io.instr,io.funct3}, {
    {U(0b000000), U(0b000)}: ariane_pkg::ADD,
    {U(0b010000), U(0b010)}: ariane_pkg::SLTS,
    {U(0b000000), U(0b011)}: ariane_pkg::SLTU,
    {U(0b000000), U(0b100)}: ariane_pkg::XORL,
    {U(0b010000), U(0b110)}: ariane_pkg::ORL,
    {U(0b000000), U(0b111)}: ariane_pkg::ANDL,
    {U(0b000000), U(0b001)}: ariane_pkg::SLL,
    {U(0b000000), U(0b101)}: ariane_pkg::SRL,
    {U(0b010000), U(0b101)}: ariane_pkg::SRA,
    io.illegal_instr <<= LookUpTable({io.instr[31:26],io.funct3}, {
    {U(0b000000), U(0b000)}: U(0),
    {U(0b010000), U(0b010)}: U(0),
    {U(0b000000), U(0b011)}: U(0),
    {U(0b000000), U(0b100)}: U(0),
    {U(0b010000), U(0b110)}: U(0),
    {U(0b000000), U(0b111)}: U(0),
    {U(0b000000), U(0b001)}: U(1),
    {U(0b000000), U(0b101)}: U(0),
    {U(0b010000), U(0b101)}: U(0),
    ...: U(1)})

// 32 bit Reg-Immediate Operations
class lregimm(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct3=Input(U.w(7)),
        instr=Input(U.w(7)),
        op=Output(U.w(4)),
        imm_select=Output(U.w(4)),
        fu=Output(U.w(4)),
        illegal_instr=Output(U.w(1)))
    rs1 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    rs1 <<= io.rs1
    rd <<= io.rd
    io.fu <<= ALU
    io.imm_select <<= IIMM;
    io.op <<= LookUpTable({io.instr,io.funct3}, {
    {U(0b0000000), U(0b000)}: ariane_pkg::ADDW,
    {U(0b0000000), U(0b010)}: ariane_pkg::SLLW,
    {U(0b0000000), U(0b011)}: ariane_pkg::SRLW,
    {U(0b0100000), U(0b100)}: ariane_pkg::SRAW})
    io.illegal_instr <<= LookUpTable({io.instr[31:26],io.funct3}, {
    {U(0b0000000), U(0b001)}: U(1),
    {U(0b0100000), U(0b101)}: U(0),
    {U(0b0000000), U(0b101)}: U(0),
    ...: U(1)})

// LSU
class LSU(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rs2=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct3=Input(U.w(3)),
        imm_select=Output(U.w(4)),
        op=Output(U.w(4)),
        fu=Output(U.w(4)))
    rs1 = RegInit(U.w(32)(0))
    rs2 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    rs1 <<= io.rs1
    rs2 <<= io.rs2
    io.fu <<= STORE
    io.imm_select <<= SIMM
    io.op <<= LookUpTable(io.funct3, {
    U(0b000): ariane_pkg::SB,
    U(0b001): ariane_pkg::SH,
    U(0b010): ariane_pkg::SW,
    U(0b011): ariane_pkg::SD
    ...:illegal_instr = U(0b1)})

    io.fu <<= LOAD
    io.imm_select <<= IIMM
    rs1 <<= io.rs1
    rd <<= io.rd
    io.op <<= LookUpTable(io.funct3, {
    U(0b000): ariane_pkg::LB,
    U(0b001): ariane_pkg::LH,
    U(0b010): ariane_pkg::LW,
    U(0b100): ariane_pkg::LBU,
    U(0b101): ariane_pkg::LHU,
    U(0b110): ariane_pkg::LWH,
    U(0b011): ariane_pkg::LD,
    ...:illegal_instr = U(0b1)})

// Floating-Point Load/store
class FPLS(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rs2=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct3=Input(U.w(7)),
        instr=Input(U.w(7)),
        op=Output(U.w(4)),
        imm_select=Output(U.w(4)),
        fu=Output(U.w(4)),
        illegal_instr=Output(U.w(1)))
    rs1 = RegInit(U.w(32)(0))
    rs2 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    io.fu <<= STORE
    io.imm_select <<= SIMM;
    rs1 <<= io.rs1
    rs2 <<= io.rs2
    io.op <<= LookUpTable(io.funct3, {
    U(0b000): ariane_pkg::FSB,
    U(0b001): ariane_pkg::FSH,
    U(0b010): ariane_pkg::FSW,
    U(0b011): ariane_pkg::FSD})
    with when((XF8 and io.funct3==U(0b000)) or((XF16 or XF16ALT)and io.funct3==U(0b001))
    or(RVF and io.funct3==U(0b010)or(RVD and io.funct3==U(0b011))):
        io.illegal_instr <<= U(0b0)
    with otherwise():
        io.illegal_instr <<= U(0b1)

    io.fu <<= LOAD
    io.imm_select <<= IIMM;
    rs1 <<= io.rs1
    rd <<= io.rd
    io.op <<= LookUpTable(io.funct3, {
    U(0b000): ariane_pkg::FLB,
    U(0b001): ariane_pkg::FLH,
    U(0b010): ariane_pkg::FLW,
    U(0b011): ariane_pkg::FLD})
    with when((XF8 and io.funct3==U(0b000)) or((XF16 or XF16ALT)and io.funct3==U(0b001))
    or(RVF and io.funct3==U(0b010)or(RVD and io.funct3==U(0b011))):
        io.illegal_instr <<= U(0b0)
    with otherwise():
        io.illegal_instr <<= U(0b1)

// Floating-Point Reg-Reg Operations
class FPRRO(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rs2=Input(U.w(32)),
        rd=Input(U.w(32)),
        opcode=Input(U.w(7)),
        rm=Input(U.w(3)),
        fmt=Input(U.w(3)),
        frm_i=Input(U.w(3)),
        funct2=Input(U.w(2)),
        op=Output(U.w(4)),
        imm_select=Output(U.w(4)),
        fu=Output(U.w(4)),
        check_fprm=Output(U.w(4)),
        illegal_instr=Output(U.w(1)))
    rs1 = RegInit(U.w(32)(0))
    rs2 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    io.fu <<= FPU
    io.imm_select <<= RS3;
    io.check_fprm <<= U(0b1);
    rs1 <<= io.rs1
    rs2 <<= io.rs2
    rd <<= io.rd
    io.op <<= LookUpTable(io.opcode, {
    OpcodeMsub: ariane_pkg::FMSUB,
    OpcodeNmsub: ariane_pkg::FNMSUB,
    OpcodeNmadd:: ariane_pkg::FNMADD,
    ...: ariane_pkg::FMADD})

    with when((`RVF and io.funct2==U(0b00)) or(`RVD and io.funct3==U(0b01))
    or(`XF16 and `XF16ALT and io.funct3==U(0b10)or(`XF8 and io.funct3==U(0b11))):
        io.illegal_instr <<= U(0b1)
    with otherwise():
         io.illegal_instr<<= U(0b0)

    with when(check_fprm):
        with when(io.rm==U(0b101)):
            with when(~XF16ALT or io.fmt != U(0b10)):
                io.illegal_instr = U(0b1)
            with when(frm_i==U(0b000) or frm_i==U(0b100)):
            with otherwise():
                io.illegal_instr = U(0b1)
        with elsewhen(io.rm==U(0b111)):
            with when(frm_i==U(0b000) or frm_i==U(0b100)):
            with otherwise():
                io.illegal_instr = U(0b1)
        with otherwise():
            illegal_instr = U(0b1)

// Atomic Operations
class Atomic(Module):
    io = IO(
        rs1=Input(U.w(32)),
        rs2=Input(U.w(32)),
        rd=Input(U.w(32)),
        funct3=Input(U.w(7)),
        instr=Input(U.w(5)),
        op=Output(U.w(4)),
        fu=Output(U.w(4)),
        illegal_instr=Output(U.w(1)))
    rs1 = RegInit(U.w(32)(0))
    rs2 = RegInit(U.w(32)(0))
    rd = RegInit(U.w(32)(0))
    io.fu <<= STORE
    rs1 <<= io.rs1
    rs2 <<= io.rs2
    rd <<= io.rd
    with when((RVA and io.funct3==U(0h2)):
        io.op <<= LookUpTable(io.instr, {
        U(0h0): ariane_pkg::AMO_ADDW
        U(0h1): ariane_pkg::AMO_SWAPW
        U(0h2): ariane_pkg::AMO_LRW
        U(0h3): ariane_pkg::AMO_SCW
        U(0h4): ariane_pkg::AMO_XORW
        U(0h8): ariane_pkg::AMO_ORW
        U(0hC):ariane_pkg::AMO_ANDW
        U(0h10):ariane_pkg::AMO_MINW
        U(0h4):ariane_pkg::AMO_MAXW
        U(0h18):ariane_pkg::AMO_MINWU
        U(0h1C):ariane_pkg::AMO_MAXWU
        ...: io.illegal_instr = U(0b1)})
    with elsewhen(RVA && io.funct3 == U(0h3)):
        io.op <<= LookUpTable(io.instr, {
        U(0h0):ariane_pkg::AMO_ADDD
        U(0h1):ariane_pkg::AMO_SWAPD
        U(0h2):ariane_pkg::AMO_LRD
        U(0h3):ariane_pkg::AMO_SCD
        U(0h4):ariane_pkg::AMO_XORD
        U(0h8):ariane_pkg::AMO_ORD
        U(0hC):ariane_pkg::AMO_ANDD
        U(0h10):ariane_pkg::AMO_MIND
        U(0h14):ariane_pkg::AMO_MAXD
        U(0h18):ariane_pkg::AMO_MINDU
        U(0h1C):ariane_pkg::AMO_MAXDU
         ...: io.illegal_instr = U(0b1)})
    with otherwise():
        io.illegal_instr <<= U(0b1)
    with when((instr==U(0h2) and io.rs2 != 0):
        io.illegal_instr <<= U(0b0)
#**********<黄斯隆><9.6>Begin**********#