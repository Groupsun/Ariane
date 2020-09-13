from pyhcl import *
import math
from enum import Enum
# ********** 徐琬玮 9.3 Begin ********** #
NR_SB_ENTRIES = 8
TRANS_ID_BITS = math.log2(NR_SB_ENTRIES)
VLEN = 64
PLEN = 56

DCACHE_INDEX_WIDTH = 12
DCACHE_TAG_WIDTH = PLEN - DCACHE_INDEX_WIDTH


class priv_lvl_t:
    PRIV_LVL_M = U.w(2)(3)
    PRIV_LVL_S = U.w(2)(1)
    PRIV_LVL_U = U.w(2)(0)


class pmp_addr_mode_t:
    OFF = U.w(2)(0)
    TOR = U.w(2)(1)
    NA4 = U.w(2)(2)
    NAPOT = U.w(2)(3)


class pmpcfg_access_t:
    x = Reg(U.w(1))
    w = Reg(U.w(1))
    r = Reg(U.w(1))


class pmpcfg_t:
    locked = Reg(U.w(1))
    reserved = Reg(Vec(2, U.w(1)))
    addr_mode = Reg(pmp_addr_mode_t)
    access_type = Reg(pmpcfg_access_t)



class fu_t(Enum):
    NONE = 0,
    LOAD = 1,
    STORE = 2,
    ALU = 3,
    CTRL_FLOW = 4,
    MULT = 5,
    CSR = 6,
    FPU = 7,
    FPU_VEC = 8


class fu_op(Enum):
    ADD = U.w(7)(0)
    SUB = U.w(7)(1)
    ADDW = U.w(7)(2)
    SUBW = U.w(7)(3)

    XORL = U.w(7)(4)
    ORL = U.w(7)(5)
    ANDL = U.w(7)(6)

    SRA = U.w(7)(7)
    SRL = U.w(7)(8)
    SLL = U.w(7)(9)
    SRLW = U.w(7)(10)
    SLLW = U.w(7)(11)
    SRAW = U.w(7)(12)

    # comparisons
    LTS = U.w(7)(13)
    LTU = U.w(7)(14)
    GES = U.w(7)(15)
    GEU = U.w(7)(16)
    EQ = U.w(7)(17)
    NE = U.w(7)(18)

    # jumps
    JALR = U.w(7)(19)
    BRANCH = U.w(7)(20)

    # set lower than operations
    SLTS = U.w(7)(21)
    SLTU = U.w(7)(22)

    # CSR functions
    MRET = U.w(7)(23)
    SRET = U.w(7)(24)
    DRET = U.w(7)(25)
    ECALL = U.w(7)(26)
    WFI = U.w(7)(27)
    FENCE = U.w(7)(28)
    FENCE_I = U.w(7)(29)
    SFENCE_VMA = U.w(7)(30)
    CSR_WRITE = U.w(7)(31)
    CSR_READ = U.w(7)(32)
    CSR_SET = U.w(7)(33)
    CSR_CLEAR = U.w(7)(34)

    # LSU functions
    LD = U.w(7)(35)
    SD = U.w(7)(36)
    LW = U.w(7)(37)
    LWU = U.w(7)(38)
    SW = U.w(7)(39)
    LH = U.w(7)(40)
    LHU = U.w(7)(41)
    SH = U.w(7)(42)
    LB = U.w(7)(43)
    SB = U.w(7)(44)
    LBU = U.w(7)(45)

    # Atomic Memory Operations
    AMO_LRW = U.w(7)(46)
    AMO_LRD = U.w(7)(47)
    AMO_SCW = U.w(7)(48)
    AMO_SCD = U.w(7)(49)
    AMO_SWAPW = U.w(7)(50)
    AMO_ADDW = U.w(7)(51)
    AMO_ANDW = U.w(7)(52)
    AMO_ORW = U.w(7)(53)
    AMO_XORW = U.w(7)(54)
    AMO_MAXW = U.w(7)(55)
    AMO_MAXWU = U.w(7)(56)
    AMO_MINW = U.w(7)(57)
    AMO_MINWU = U.w(7)(58)
    AMO_SWAPD = U.w(7)(59)
    AMO_ADDD = U.w(7)(60)
    AMO_ANDD = U.w(7)(61)
    AMO_ORD = U.w(7)(62)
    AMO_XORD = U.w(7)(63)
    AMO_MAXD = U.w(7)(64)
    AMO_MAXDU = U.w(7)(65)
    AMO_MIND = U.w(7)(66)
    AMO_MINDU = U.w(7)(67)

    # Multiplications
    MUL = U.w(7)(68)
    MULH = U.w(7)(69)
    MULHU = U.w(7)(70)
    MULHSU = U.w(7)(71)
    MULW = U.w(7)(72)

    # Divisions
    DIV = U.w(7)(73)
    DIVU = U.w(7)(74)
    DIVW = U.w(7)(75)
    DIVUW = U.w(7)(76)
    REM = U.w(7)(77)
    REMU = U.w(7)(78)
    REMW = U.w(7)(79)
    REMUW = U.w(7)(80)

    # Floating - Point Load and Store Instructions
    FLD = U.w(7)(81)
    FLW = U.w(7)(82)
    FLH = U.w(7)(83)
    FLB = U.w(7)(84)
    FSD = U.w(7)(85)
    FSW = U.w(7)(86)
    FSH = U.w(7)(87)
    FSB = U.w(7)(88)

    # Floating - Point Computational Instructions
    FADD = U.w(7)(89)
    FSUB = U.w(7)(90)
    FMUL = U.w(7)(91)
    FDIV = U.w(7)(92)
    FMIN_MAX = U.w(7)(93)
    FSQRT = U.w(7)(94)
    FMADD = U.w(7)(95)
    FMSUB = U.w(7)(96)
    FNMSUB = U.w(7)(97)
    FNMADD = U.w(7)(98)

    # Floating - Point Conversion and Move Instructions
    FCVT_F2I = U.w(7)(99)
    FCVT_I2F = U.w(7)(100)
    FCVT_F2F = U.w(7)(101)
    FSGNJ = U.w(7)(102)
    FMV_F2X = U.w(7)(103)
    FMV_X2F = U.w(7)(104)

    # Floating - Point Compare Instructions
    FCMP = U.w(7)(105)

    # Floating - Point Classify Instruction
    FCLASS = U.w(7)(106)

    # Vectorial Floating - Point Instructions that don't directly map onto the scalar ones
    VFMIN = U.w(7)(107)
    VFMAX = U.w(7)(108)
    VFSGNJ = U.w(7)(109)
    VFSGNJN = U.w(7)(110)
    VFSGNJX = U.w(7)(111)
    VFEQ = U.w(7)(112)
    VFNE = U.w(7)(113)
    VFLT = U.w(7)(114)
    VFGE = U.w(7)(115)
    VFLE = U.w(7)(116)
    VFGT = U.w(7)(117)
    VFCPKAB_S = U.w(7)(118)
    VFCPKCD_S = U.w(7)(119)
    VFCPKAB_D = U.w(7)(120)
    VFCPKCD_D = U.w(7)(121)


class amo_t(Enum):
    AMO_NONE = U.w(4)(0)
    AMO_LR = U.w(4)(1)
    AMO_SC = U.w(4)(2)
    AMO_SWAP = U.w(4)(3)
    AMO_ADD = U.w(4)(4)
    AMO_AND = U.w(4)(5)
    AMO_OR = U.w(4)(6)
    AMO_XOR = U.w(4)(7)
    AMO_MAX = U.w(4)(8)
    AMO_MAXU = U.w(4)(9)
    AMO_MIN = U.w(4)(10)
    AMO_MINU = U.w(4)(11)
    AMO_CAS1 = U.w(4)(12)
    AMO_CAS2 = U.w(4)(13)


class lsu_ctrl_t:
    valid = Reg(U.w(1))
    vaddr = Reg(Vec(VLEN, U.w(1)))
    overflow = Reg(U.w(1))
    data = Reg(Vec(64, U.w(1)))
    be = Reg(Vec(8, U.w(1)))
    # TODO: fu_t
    fu = Reg(fu_t)
    operator = Reg(fu_op)
    trans_id = Reg(Vec(TRANS_ID_BITS, U.w(1)))


class exception_t:
    cause = Reg(Vec(64, U.w(1)))
    tval = Reg(Vec(64, U.w(1)))
    valid = Reg(U.w(1))


class icache_areq_o_t:
    fetch_req = Reg(U.w(1))
    fetch_vaddr = Reg(Vec(VLEN, U.w(1)))


class icache_areq_i_t:
    fetch_valid = Reg(U.w(1))
    fetch_paddr = Reg(Vec(PLEN, U.w(1)))
    fetch_exception = Reg(exception_t)


class dcache_req_o_t:
    data_gnt = Reg(U.w(1))
    data_rvalid = Reg(U.w(1))
    data_rdata = Reg(Vec(64, U.w(1)))


class dcache_req_i_t:
    address_index = Reg(Vec(DCACHE_INDEX_WIDTH, U.w(1)))
    address_tag = Reg(Vec(DCACHE_TAG_WIDTH, U.w(1)))
    data_wdata = Reg(Vec(64, U.w(1)))
    data_req = Reg(U.w(1))
    data_we = Reg(U.w(1))
    data_be = Reg(Vec(8, U.w(1)))
    data_size = Reg(Vec(2, U.w(1)))
    kill_req = Reg(U.w(1))
    tag_valid = Reg(U.w(1))


class amo_req_t:
    req = Reg(U.w(1))
    # TODO: enum type
    amo_op = amo_t
    size = Reg(Vec(2, U.w(1)))
    operand_a = Reg(Vec(64, U.w(1)))
    operand_b = Reg(Vec(64, U.w(1)))


class amo_resp_t:
    ack = Reg(U.w(1))
    result = Reg(Vec(64, U.w(1)))


class fu_data_t:
    fu = fu_t
    operator = fu_op
    operand_a = Reg(Vec(64, U.w(1)))
    operand_b = Reg(Vec(64, U.w(1)))
    imm = Reg(Vec(64, U.w(1)))
    trans_id = Reg(Vec(TRANS_ID_BITS, U.w(1)))


def load_store_unit(ASID_WIDTH: int = 1, ArianeCfg: ariane_cfg_t = ArianeDefaultConfig)


    class load_store_unit(Module):
        io = IO(
            clk_i=Input(U.w(1)),
            rst_ni=Input(U.w(1)),
            flush_i=Input(U.w(1)),
            no_st_pending_o=Output(U.w(1)),
            amo_valid_commit_i=Input(U.w(1)),

            fu_data_i=Input(fu_data_t),
            lsu_ready_o=Output(U.w(1)),
            lsu_valid_i=Input(U.w(1)),

            load_trans_id_o=Output(Vec(TRANS_ID_BITS, U.w(1))),
            load_result_o=Output(Vec(64, U.w(1))),
            load_valid_o=Output(U.w(1)),
            load_exception_o=Output(exception_t),

            store_trans_id_o=Output(Vec(TRANS_ID_BITS, U.w(1))),
            store_result_o=Output(Vec(64, U.w(1))),
            store_valid_o=Output(U.w(1)),
            store_exception_o=Output(exception_t),

            commit_i=Input(U.w(1)),
            commit_ready_o=Output(U.w(1)),
            commit_tran_id_i=Input(Vec(TRANS_ID_BITS, U.w(1))),

            enable_translation_i=Input(U.w(1)),
            en_ld_st_translation_i=Input(U.w(1)),

            icache_areq_i=Input(icache_areq_o_t),
            icache_areq_o=Output(icache_areq_i_t),

            priv_lvl_i=Input(priv_lvl_t),
            ld_st_priv_lvl_i=Input(priv_lvl_t),
            sum_i=Input(U.w(1)),
            mxr_i=Input(U.w(1)),
            satp_ppn_i=Input(Vec(44, U.w(1))),
            asid_i=Input(Vec(ASID_WIDTH, U.w(1))),
            flush_tlb_i=Input(U.w(1)),

            itlb_miss_o=Output(U.w(1)),
            dtlb_miss_o=Output(U.w(1)),

            dcache_req_ports_i=Input(Vec(3, dcache_req_o_t)),
            dcache_req_ports_o=Output(Vec(3, dcache_req_i_t)),
            dcache_wbuffer_empty_i=Input(U.w(1)),
            dcache_wbuffer_not_ni_i=Input(U.w(1)),

            amo_req_o=Output(amo_req_t),
            amo_resp_i=Input(amo_resp_t),

            pmpcfg_i=Input(Vec(16, pmpcfg_t)),
            pmpaddr_i=Input(Vec(16, Vec(54, U.w(1))))
        )

        data_misaligned = Reg(U.w(1))
        lsu_ctrl = Reg(lsu_ctrl_t)
        pop_st = Reg(U.s(1))
        pop_ld = Reg(U.w(1))
        vaddr_i = Reg(Vec(VLEN, U.w(1)))
        vaddr64 = Reg(Vec(64, U.w(1)))
        overflow = Reg(U.w(1))
        be_i = Reg(Vec(8, U.w(1)))

        vaddr64 <<= ((io.fu_data_i.imm).to_sint() + (io.fu_data_i.operand_a).to_sint()).to_uint()
        # TODO: assign vaddr_i = vaddr64[riscv::VLEN-1:0];
        vaddr_i <<= vaddr64[0:VLEN - 1]
        # TODO: (&vaddr64[63:riscv::VLEN-1]) == 1'b1 || (|vaddr64[63:riscv::VLEN-1]) == 1'b0
        with when((& vaddr64[63:VLEN - 1]) == U(1) or (| vaddr64[63:VLEN - 1]) == U(0)):
            overflow <<= Bool(False)
        with otherwise():
            overflow <<= Bool(True)

        st_valid_i = Reg(U.w(1))
        ld_valid_i = Reg(U.w(1))
        ld_translation_req = Reg(U.w(1))
        st_translation_req = Reg(U.w(1))
        ld_vaddr = Reg(Vec(VLEN, U.w(1)))
        st_vaddr = Reg(Vec(VLEN, U.w(1)))
        translation_req = Reg(U.w(1))
        translation_valid = Reg(U.w(1))

        mmu_vaddr = Reg(Vec(VLEN, U.w(1)))
        mmu_paddr = Reg(Vec(PLEN, U.w(1)))
        mmu_exception = exception_t()
        dtlb_hit = Reg(U.w(1))
        dtlb_ppn = Reg(Vec(PLEN - 12, U.w(1)))

        ld_valid = Reg(U.w(1))
        ld_trans_id = Reg(Vec(TRANS_ID_BITS, U.w(1)))
        ld_result = Reg(Vec(64, U.w(1)))
        st_valid = Reg(U.w(1))
        st_trans_id = Reg(Vec(TRANS_ID_BITS, U.w(1)))
        st_result = Reg(Vec(64, U.w(1)))

        page_offset = Reg(Vec(12, U.w(1)))
        page_offset_matches = Reg(U.w(1))

        misaligned_exception = exception_t()
        ld_ex = exception_t
        st_ex = exception_t

        # mmu
        i_mmu = mmu(INSTR_TLB_ENTRIES=16, DATA_TLB_ENTRIES=16, ASID_WIDTH=ASID_WIDTH, ArianeCfg=ArianeCfg)
        mmu_io = i_mmu.io
        mmu_io.misaligned_ex_i <<= misaligned_exception
        mmu_io.lsu_is_store_i <<= st_translation_req
        mmu_io.lsu_req_i <<= translation_req
        mmu_io.lsu_vaddr_i <<= mmu_vaddr
        translation_valid <<= mmu_io.lsu_valid_o
        mmu_paddr <<= mmu_io.lsu_paddr_o
        mmu_exception <<= mmu_io.lsu_exception_o
        dtlb_hit <<= mmu_io.lsu_dtlb_hit_o
        dtlb_ppn <<= mmu_io.lsu_dtlb_ppn_o
        mmu_io.req_port_i <<= io.dcache_req_ports_i[0]
        io.dcache_req_ports_o[0] <<= mmu_io.req_port_o
        mmu_io.icache_areq_i <<= io.icache_areq_i
        io.icache_areq_o <<= mmu_io.icache_areq_o

        # store_unit
        store_buffer_empty = Reg(U.w(1))

        i_store_unit = store_unit()
        store_unit_io = i_store_unit.io
        store_buffer_empty <<= store_unit_io.store_buffer_empty_o

        store_unit_io.valid_i <<= st_valid_i
        store_unit_io.lsu_ctrl_i <<= lsu_ctrl
        pop_st <<= store_unit_io.pop_st_o

        st_valid <<= store_unit_io.valid_o
        st_trans_id <<= store_unit_io.trans_id_o
        st_result <<= store_unit_io.result_o
        st_ex <<= store_unit_io.ex_o

        st_translation_req <<= store_unit_io.translation_req_o
        st_vaddr <<= store_unit_io.vaddr_o
        store_unit_io.paddr_i <<= mmu_paddr
        store_unit_io.ex_i <<= mmu_exception
        store_unit_io.dtlb_hit_i <<= dtlb_hit

        store_unit_io.page_offset_i <<= page_offset
        page_offset_matches <<= store_unit_io.page_offset_matches_o

        store_unit_io.req_port_i <<= io.dcache_req_ports_i[2]
        io.dcache_req_ports_o[2] <<= store_unit_io.req_port_o

        # load unit
        i_load_unit = load_unit(ArianeCfg=ArianeCfg)
        load_unit_io = i_store_unit.io

        load_unit_io.valid_ <<= ld_valid_i
        load_unit_io.lsu_ctrl_ <<= lsu_ctrl
        pop_ld <<= load_unit_io.pop_ld_o

        ld_valid <<= load_unit_io.valid_o
        ld_trans_id <<= load_unit_io.trans_id_o
        ld_result <<= load_unit_io.result_o
        ld_ex <<= load_unit_io.ex_o

        ld_translation_req <<= load_unit_io.translation_req_o
        ld_vaddr <<= load_unit_io.vaddr_o
        load_unit_io.paddr_ <<= mmu_paddr
        load_unit_io.ex_ <<= mmu_exception
        load_unit_io.dtlb_hit_ <<= dtlb_hit
        load_unit_io.dtlb_ppn_ <<= dtlb_ppn

        page_offset <<= load_unit_io.page_offset_o
        load_unit_io.page_offset_matches_ <<= page_offset_matches
        load_unit_io.store_buffer_empty_ <<= store_buffer_empty

        load_unit_io.req_port_ <<= io.dcache_req_ports_i[1]
        io.dcache_req_ports_o[1] <<= load_unit_io.req_port_o

        # output pipeline register, shift_reg
        # TODO: dtype: logic[$bits(ld_valid) + $bits(ld_trans_id) + $bits(ld_result) + $bits(ld_ex) - 1: 0]
        # TODO: NR_LOAD_PIPE_REGS
        i_pipe_reg_load = shift_reg(dtype(Vec(ld_valid + ld_trans_id + ld_result + ld_ex, U.w(1))),
                                    Depth=NR_LOAD_PIPE_REGS)
        i_pipe_reg_load_io = i_pipe_reg_load.io

        # TODO: {...}
        i_pipe_reg_load_io.d_i <<= {ld_valid, ld_trans_id, ld_result, ld_ex}
        io.load_valid_o, io.load_trans_id_o, io.load_result_o, io.load_exception_o <<= i_pipe_reg_load_io.d_o

        # TODO: logic[$bits(st_valid) + $bits(st_trans_id) + $bits(st_result) + $bits(st_ex) - 1: 0]
        # TODO: NR_STORE_PIPE_REGS
        i_pipe_reg_store = shift_reg(dtype=(Vec(st_valid + st_trans_id + st_result + st_ex, U.w(1))),
                                     Depth=NR_STORE_PIPE_REGS)
        i_pipe_reg_store_io = i_pipe_reg_store.io

        i_pipe_reg_store_io.d_i <<= {st_valid, st_trans_id, st_result, st_ex}
        {store_valid_o, store_trans_id_o, store_result_o, store_exception_o} <<= i_pipe_reg_store_io.d_o

        ld_valid_i = U.w(1)(0)
        st_valid_i = U.w(1)(1)

        translation_req = U.w(1)(0)
        mmu_vaddr = {riscv::VLEN{U.w(1)(0)}};


        be_i = be_gen(vaddr_i[2:0], extract_transfer_size(io.fu_data_i.operator))


        misaligned_exception = {U.w(64)(0), U.w(64)(0), U.w(1)(0)}
        data_misaligned <<= U.w(1)(0)


        with when(lsu_ctrl.valid==U(1)):
            with when(
                    lsu_ctrl.operator == fu_op.LD or lsu_ctrl.operator == fu_op.SD or lsu_ctrl.operator == fu_op.FLD or lsu_ctrl.operator == fu_op.FSD or lsu_ctrl.operator == fu_op.AMO_LRD or lsu_ctrl.operator == fu_op.AMO_SCD or lsu_ctrl.operator == AMO_SWAPD or lsu_ctrl.operator == fu_op.AMO_ADDD or lsu_ctrl.operator == fu_op.AMO_ANDD or lsu_ctrl.operator == fu_op.AMO_ORD or lsu_ctrl.operator == fu_op.AMO_XORD or lsu_ctrl.operator == fu_op.AMO_MAXD or lsu_ctrl.operator == fu_op.AMO_MAXDU or lsu_ctrl.operator == fu_op.AMO_MIND or lsu_ctrl.operator == fu_op.AMO_MINDU):
                # TODO: lsu_ctrl.vaddr[2:0]
                with when(lsu_ctrl.vaddr[0:2] != U(0)):
                    data_misaligned <<= U.w(1)(1)
            with elsewhen(
                    lsu_ctrl.operator == fu_op.LW or lsu_ctrl.operator == fu_op.LWU or lsu_ctrl.operator == fu_op.SW or lsu_ctrl.operator == fu_op.FLW or lsu_ctrl.operator == fu_op.FSW or lsu_ctrl.operator == fu_op.AMO_LRW or lsu_ctrl.operator == fu_op.AMO_SCW or lsu_ctrl.operator == fu_op.AMO_SWAPW or lsu_ctrl.operator == fu_op.AMO_ADDW or lsu_ctrl.operator == fu_op.AMO_ANDW or lsu_ctrl.operator == fu_op.AMO_ORW or lsu_ctrl.operator == fu_op.AMO_XORW or lsu_ctrl.operator == fu_op.AMO_MAXW or lsu_ctrl.operator == fu_op.AMO_MAXWU or lsu_ctrl.operator == fu_op.AMO_MINW or lsu_ctrl.operator == fu_op.AMO_MINWU):
                # TODO: lsu_ctrl.vaddr[1:0]
                with when(lsu_ctrl.vaddr[0:1] != U(0)):
                    data_misaligned <<= U.w(1)(1)
            with elsewhen(
                    lsu_ctrl.operator == fu_op.LH or lsu_ctrl.operator == fu_op.LHU or lsu_ctrl.operator == fu_op.SH or lsu_ctrl.operator == fu_op.FLH or lsu_ctrl.operator == fu_op.FSH):
                with when(lsu_ctrl.vaddr[0] != U(0)):
                    data_misaligned <<= U.w(1)(1)

        with when(data_misaligned):
            with when(lsu_ctrl.fu == fu_op.LOAD):
                misaligned_exception <<= riscv::LD_ADDR_MISALIGNED, {{64 - riscv:: VLEN{U.w(1)(0)}},lsu_ctrl.vaddr},U.w(1)(1)
            with elsewhen(lsu_ctrl.fu == fu_op.STORE):
                misaligned_exception <<= riscv::ST_ADDR_MISALIGNED, {{64-riscv::VLEN{U.w(1)(0)}},lsu_ctrl.vaddr}, U.w(1)(1)

        with when(io.en_ld_st_translation_i and lsu_ctrl.overflow):
            with when(lsu_ctrl.fu == fu_op.LOAD):
                misaligned_exception <<= {riscv::LD_ACCESS_FAULT, {{64-riscv::VLEN{U.w(1)(0)}},lsu_ctrl.vaddr}, U.w(1)(1)}
            with elsewhen(lsu_ctrl.fu == fu_op.STORE):
                misaligned_exception <<= {riscv::ST_ACCESS_FAULT, {{64-riscv::VLEN{U.w(1)(0)}},lsu_ctrl.vaddr}, U.w(1)(1)}

        # LSU Control
        lsu_req_i = lsu_ctrl_t()
        lsu_req_i.valid <<= io.lsu_valid_i
        lsu_req_i.vaddr <<= io.vaddr_i
        lsu_req_i.overflow <<= overflow
        lsu_req_i.data <<= io.fu_data_i.operand_b
        lsu_req_i.be <<= io.be_i
        lsu_req_i.fu <<= io.fu_data_i.fu
        lsu_req_i.operator <<= io.fu_data_i.operator
        lsu_req_i.trans_id <<= io.fu_data_i.trans_id

        # TODO: lsu_bypass
        lsu_bypass_i = lsu_bypass()
        lsu_bypass_io = lsu_req_i.io
        lsu_bypass_io.lsu_req_i <<= io.lsu_req_i
        lsu_bypass_io.lus_req_valid_i <<= io.lsu_valid_i
        lsu_bypass_io.pop_ld_i <<= pop_ld
        lsu_bypass_io.pop_st_i <<= pop_st

        lsu_ctrl <<= lsu_bypass_io.lsu_ctrl_o
        io.lsu_ready_o <<= lsu_bypass_io.ready_o

    class lsu_bypass(Module):
        io = IO(
            clk_i=Input(U.w(1)),
            rst_ni=Input(U.w(1)),
            flush_i=Input(U.w(1)),

            lsu_req_i=Input(lsu_ctrl_t),
            lus_req_valid_i=Input(U.w(1)),
            pop_ld_i=Input(U.w(1)),
            pop_st_i=Input(U.w(1)),

            lsu_ctrl_o=Output(lsu_ctrl_t),
            ready_o=Output(U.w(1))
        )

        mem_n = Reg(Vec(2, lsu_ctrl_t))
        mem_q = Reg(Vec(2, lsu_ctrl_t))

        read_pointer_n = Reg(U.w(1))
        read_pointer_q = Reg(U.w(1))
        write_pointer_n = Reg(U.w(1))
        write_pointer_q = Reg(U.w(1))
        status_cnt_n = Reg(Vec(2, U.w(1)))
        status_cnt_q = Reg(Vec(2, U.w(1)))

        empty = Reg(U.w(1))
        empty <<= Mux(status_cnt_q == 0, U(1), U(0))
        io.ready_o <<= empty

        status_cnt = Reg(Vec(2, U.w(1)))
        write_pointer = Reg(U.w(1))
        read_pointer = Reg(U.w(1))

        status_cnt <<= status_cnt_q
        write_pointer <<= write_pointer_q
        read_pointer <<= read_pointer_q

        mem_n <<= mem_q

        with when(io.lus_req_valid_i):
            mem_n[write_pointer_q] <<= io.lsu_req_i
            write_pointer <<= write_pointer + U(1)
            status_cnt <<= status_cnt + U(1)

        with when(io.pop_ld_i):
            mem_n[read_pointer_q].valid <<= U.w(1)(0)
            read_pointer <<= read_pointer + U(1)
            status_cnt <<= status_cnt - U(1)

        with when(io.pop_st_i):
            mem_n[read_pointer_q].valid <<= U.w(1)(0)
            read_pointer <<= read_pointer + U(1)
            status_cnt <<= status_cnt - U(1)

        # TODO: and
        with when(io.pop_st_i and io.pop_ld_i):
            mem_n <<= U(0)

        with when(io.flush_i):
            status_cnt <<= U(0)
            write_pointer <<= U(0)
            read_pointer <<= U(0)
            mem_n <<= U(0)

        read_pointer_n <<= read_pointer
        write_pointer_n <<= write_pointer
        status_cnt_n <<= status_cnt

        # output_assignment
        with when(empty):
            io.lsu_ctrl_o <<= io.lsu_req_i
        with otherwise():
            io.lsu_ctrl_o <<= mem_q[read_pointer_q]

        # registers
        with when(~io.rst_ni):
            mem_q <<= U(0)
            status_cnt_q <<= U(0)
            write_pointer_q <<= U(0)
            read_pointer_q <<= U(0)
        with otherwise():
            mem_q           <<= mem_n
            status_cnt_q    <<= status_cnt_n
            write_pointer_q <<= write_pointer_n
            read_pointer_q  <<= read_pointer_n

    return load_store_unit()
# ********** 徐琬玮 9.11 End ********** #
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(load_store_unit()), "load_store_unit.fir"))
