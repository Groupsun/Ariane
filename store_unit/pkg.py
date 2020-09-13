from pyhcl import *
from enum import Enum
import math

### ----------刘敏琪 Begin----------###
##todo
CONFIG_L1I_CACHELINE_WIDTH=U(128)
CONFIG_L1I_ASSOCIATIVITY=U(4)
CONFIG_L1I_SIZE=U(16*1024)
CONFIG_L1D_CACHELINE_WIDTH=U(128)
CONFIG_L1D_ASSOCIATIVITY=U(8)
CONFIG_L1D_SIZE=U(32*1024)
DCACHE_SET_ASSOC=CONFIG_L1D_ASSOCIATIVITY
##log2
DCACHE_INDEX_WIDTH=U(100)
DCACHE_TAG_WIDTH=U(100)
#riscv!!
VLEN=100
PLEN=100
NR_SB_ENTRIES = 8
TRANS_ID_BITS = math.log2(NR_SB_ENTRIES)
DEPTH_SPEC=100
DEPTH_COMMIT=100



dcache_req_i_t=Bundle(
    address_index=U.w(DCACHE_INDEX_WIDTH),
    address_tag=U.w(DCACHE_TAG_WIDTH),
    data_wdata=U.w(64),
    data_req=U.w(1),
    data_we=U.w(1),
    data_be=U.w(8),
    data_size=U.w(2),
    kill_req=U.w(1),
    tag_valid=U.w(1),
)
dcache_req_o_t=Bundle(
    data_gnt=U.w(1),
    data_rvalid=U.w(1),
    data_rdata=U.w(64)
    )
class fu_t:
    NONE=U(0)
    LOAD=U(1)
    STORE=U(2)
    ALU=U(3)
    CTRL_FLOW=U(4)
    MULT=U(5)
    CSR=U(6)
    FPU=U(7)
    FPU_VEC=U(8)
    dtype=U.w(4)

class fu_op:
    ADD=U(0)
    LD=U(35)
    SD =U(36)
    LW =U(37)
    LWU=U(38)
    SW=U(39)
    LH=U(40)
    LHU=U(41)
    SH=U(42)
    LB=U(43)
    SB=U(44)
    LBU=U(45)
    AMO_LRW=U(46)
    AMO_LRD=U(47)
    AMO_SCW=U(48)
    AMO_SCD=U(49)
    AMO_SWAPW=U(50)
    AMO_ADDW=U(51)
    AMO_ANDW=U(52)
    AMO_ORW=U(53)
    AMO_XORW =U(54)
    AMO_MAXW=U(55)
    AMO_MAXWU=U(56)
    AMO_MINW=U(57)
    AMO_MINWU=U(58)
    AMO_SWAPD=U(59)
    AMO_ADDD=U(60)
    AMO_ANDD=U(61)
    AMO_ORD=U(62)
    AMO_XORD=U(63)
    AMO_MAXD=U(64)
    AMO_MAXDU=U(65)
    AMO_MIND=U(66)
    AMO_MINDU=U(67)
    FLD=U(81)
    FLW=U(82)
    FLH=U(83)
    FLB=U(84)
    FSD=U(85)
    FSW=U(86)
    FSH=U(87)
    FSB=U(88)
    dtype=U.w(7)

class amo_t:
    AMO_NONE = U(0)
    AMO_LR = U(1)
    AMO_SC = U(2)
    AMO_SWAP = U(3)
    AMO_ADD = U(4)
    AMO_AND = U(5)
    AMO_OR = U(6)
    AMO_XOR = U(7)
    AMO_MAX = U(8)
    AMO_MAXU = U(9)
    AMO_MIN = U(10)
    AMO_MINU = U(11)
    AMO_CAS1 = U(12)  # unused, not part of riscv spec, but provided in OpenPiton
    AMO_CAS2 = U(13)  # unused, not part of riscv spec, but provided in OpenPiton
    dtype = U.w(4)

lsu_ctrl_t=Bundle(
    valid=U.w(1),
    #riscv
    vaddr=U(VLEN),
    overflow=U.w(1),
    data=U.w(64),
    be=U.w(8),
    #enum fu_t ,fu_op
    #9
    fu=fu_t.dtype,
    #
    operator =fu_op.dtype,
    trans_id=U.w(TRANS_ID_BITS)
)
exception_t=Bundle(
    cause=U.w(64),
    tval=U.w(64),
    valid=U.w(1)
)


amo_req_t=Bundle(
    req=U.w(1),
    amo_op=amo_t.dtype,
    size=U.w(2),
    operand_a=U.w(64),
    operand_b=U.w(64)
)
amo_resq_t=Bundle(
    ack=U.w(1),
    result=U.w(64)
)
def is_amo(op):
    with when(op <= fu_op.AMO_MINDU & op>=fu_op.AMO_LRW):
        return U(1)
    with otherwise():
        return U(0)

def data_align(addr,data):
    with when(addr==U(0)):
        return data
    with elsewhen(addr==U(1)):
        return {data[55:0],data[63:56]}
    with elsewhen(addr == U(2)):
        return {data[47:0],data[63:48]}
    with elsewhen(addr == U(3)):
        return {data[39:0],data[63:40]}
    with elsewhen(addr == U(4)):
        return {data[31:0],data[63:32]}
    with elsewhen(addr == U(5)):
        return {data[23:0],data[63:24]}
    with elsewhen(addr == U(6)):
        return {data[15:0],data[63:16]}
    with elsewhen(addr == U(7)):
        return {data[7:0],data[63:8]}
    with otherwise():
        return data



def extract_transfer_size(op):
    #!!!!
    with when (op==fu_op.LD | op==fu_op.SD |op==fu_op.FLD| op==fu_op.FSD | op==fu_op.AMO_LRD | op==fu_op.AMO_SCD |
            op==fu_op.AMO_SWAPD | op==fu_op.AMO_ADDD |
            op==fu_op.AMO_ANDD |  op==fu_op.AMO_ORD |
            op==fu_op.AMO_XORD | op==fu_op.AMO_MAXD |
            op==fu_op.AMO_MAXDU | op==fu_op.AMO_MIND |
            op==fu_op.AMO_MINDU): return U(3)
    with elsewhen(op==fu_op.LW | op==fu_op. LWU | op==fu_op.SW | op==fu_op. FLW| op==fu_op. FSW| op==fu_op.AMO_LRW |
                  op==fu_op.AMO_SCW | op==fu_op.AMO_SWAPW| op==fu_op.AMO_ADDW| op==fu_op.AMO_ANDW| op==fu_op.AMO_ORW| op==fu_op.AMO_XORW|
                  op==fu_op.AMO_MAXW| op==fu_op.AMO_MAXWU| op==fu_op.AMO_MINW| op==fu_op.AMO_MINWU):return U(2)
    with elsewhen(op==fu_op.LH |op==fu_op.LHU|op==fu_op.SH|op==fu_op.FLH|op==fu_op.FSH):
        return U(1)
    with elsewhen(op==fu_op.LB |op==fu_op.LBU | op==fu_op.SB | op==fu_op.FLB | op==fu_op.FSB):
        return U(0)
    with otherwise():
        return U(3)
    #
    with otherwise():
        return U(3)


### ----------刘敏琪 End----------###
