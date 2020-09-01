# ********** 郑学钿 2020.8.30 Begin ********** #
from pyhcl import *
from math import *

class riscv():
    PLEN = 56
    VLEN = 64


    class priv_lvl_t(Module):
        PRIV_LVL_M = U(3)
        PRIV_LVL_S = U(1)
        PRIV_LVL_U = U(0)

        dtype = U.w(2)


    class xs_t(Module):
        Off = U(0)
        Initial = U(1)
        Clean = U(2)
        Dirty = U(3)

        dtype = U.w(2)


class ariane_pkg():
    risc = riscv()
    REG_ADDR_SIZE = 6,

    class cf_t(Module):
        NoCF
        Branch
        Jump
        JumpR
        Return

        dtype = U.w(3)


    class branchpredict_sbe_t():
        cf = cft()
        predict_address = U.w(risc.VLEN)


    class exception_t():
        cause = U.w(64)
        tval = U.w(64)
        valid = Bool


    class fetch_entry_t():
        address = U.w(risc.VLEN)
        instruction = U.w(32)
        branch_predict = branchpredict_sbe_t()
        ex = exception_t()

# ********** 郑学钿 2020.8.30 End ********** #

# ********** 郑学钿 2020.8.31 Begin ********** #

    class fu_t(Module):
        NONE = U(0)
        LOAD = U(1)
        STORE = U(2)
        ALU = U(3)
        CTRL_FLOW = U(4)
        MULT = U(5)
        CSR = U(6)
        FPU = U(7)
        FPU_VEC = U(8)

        dtype = U.w(4)


    class fu_op(Module):
        # 这里是否要赋值？
        # basic ALU op
        ADD, SUB, ADDW, SUBW,
        # logic operations
        XORL, ORL, ANDL,
        # shifts
        SRA, SRL, SLL, SRLW, SLLW, SRAW,
        # comparisons
        LTS, LTU, GES, GEU, EQ, NE,
        # jumps
        JALR, BRANCH,
        # set lower than operations
        SLTS, SLTU,
        # CSR functions
        MRET, SRET, DRET, ECALL, WFI, FENCE, FENCE_I, SFENCE_VMA, CSR_WRITE, CSR_READ, CSR_SET, CSR_CLEAR,
        # LSU functions
        LD, SD, LW, LWU, SW, LH, LHU, SH, LB, SB, LBU,
        # Atomic Memory Operations
        AMO_LRW, AMO_LRD, AMO_SCW, AMO_SCD,
        AMO_SWAPW, AMO_ADDW, AMO_ANDW, AMO_ORW, AMO_XORW, AMO_MAXW, AMO_MAXWU, AMO_MINW, AMO_MINWU,
        AMO_SWAPD, AMO_ADDD, AMO_ANDD, AMO_ORD, AMO_XORD, AMO_MAXD, AMO_MAXDU, AMO_MIND, AMO_MINDU,
        # Multiplications
        MUL, MULH, MULHU, MULHSU, MULW,
        # Divisions
        DIV, DIVU, DIVW, DIVUW, REM, REMU, REMW, REMUW,
        # Floating-Point Load and Store Instructions
        FLD, FLW, FLH, FLB, FSD, FSW, FSH, FSB,
        # Floating-Point Computational Instructions
        FADD, FSUB, FMUL, FDIV, FMIN_MAX, FSQRT, FMADD, FMSUB, FNMSUB, FNMADD,
        # Floating-Point Conversion and Move Instructions
        FCVT_F2I, FCVT_I2F, FCVT_F2F, FSGNJ, FMV_F2X, FMV_X2F,
        # Floating-Point Compare Instructions
        FCMP,
        # Floating-Point Classify Instruction
        FCLASS,
        # Vectorial Floating-Point Instructions that don't directly map onto the scalar ones
        VFMIN, VFMAX, VFSGNJ, VFSGNJN, VFSGNJX, VFEQ, VFNE, VFLT, VFGE, VFLE, VFGT, VFCPKAB_S, VFCPKCD_S, VFCPKAB_D, VFCPKCD_D

        dtype = U.w(4)


    class scoreboard_entry_t():
        pc = U.w(risc.VLEN),
        trans_id = U.w(TRAN_ID_BITS),      #暂时未实现
        fu = fu_t(),
        op = fu_op(),
        rs1 = U.w(REG_ADDR_SIZE),
        rs2 = U.w(REG_ADDR_SIZE),
        rd = U.w(REG_ADDR_SIZE),
        result = U.w(64),
        valid = Bool,
        use_imm = Bool,
        use_zimm = Bool,
        use_pc = Bool,
        ex = exception_t(),
        bp = branchpredict_sbe_t(),
        is_compressed = Bool


# ********** 郑学钿 2020.8.31 End ********** #