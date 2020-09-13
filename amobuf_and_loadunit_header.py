from pyhcl import *
import math
from enum import Enum,auto
# ********** 蒋宇涛 2020.8.27 Begin ********** #
class riscv():
    PLEN = 56
    VLEN = 64

class ariane_pkg():

    NR_SB_ENTRIES = 8
    TRANS_ID_BITS = math.ceil(math.log2(NR_SB_ENTRIES))
    DCACHE_INDEX_WIDTH = 12
    DCACHE_TAG_WIDTH   = riscv.PLEN-DCACHE_INDEX_WIDTH
    NrMaxRules = 16

    class amo_t(Module):
        AMO_NONE = U(0)
        AMO_LR   = U(1)
        AMO_SC   = U(2)
        AMO_SWAP = U(3)
        AMO_ADD  = U(4)
        AMO_AND  = U(5)
        AMO_OR   = U(6)
        AMO_XOR  = U(7)
        AMO_MAX  = U(8)
        AMO_MAXU = U(9)
        AMO_MIN  = U(10)
        AMO_MINU = U(11)
        AMO_CAS1 = U(12)  # unused, not part of riscv spec, but provided in OpenPiton
        AMO_CAS2 = U(13)  # unused, not part of riscv spec, but provided in OpenPiton

        dtype=U.w(4)

    class fu_t(Module):
        dtype=U.w(4)

    class fu_op(Enum):
        # basic ALU op
        ADD=0
        SUB=auto()
        ADDW=auto()
        SUBW=auto()
        
        # logic operations
        XORL=auto()
        ORL=auto()
        ANDL=auto()
        
        # shifts
        SRA=auto()
        SRL=auto()
        SLL=auto()
        SRLW=auto()
        SLLW=auto()
        SRAW=auto()
       
        # comparisons
        LTS=auto()
        LTU=auto()
        GES=auto()
        GEU=auto()
        EQ=auto()
        NE=auto()
       
        # jumps
        JALR=auto()
        BRANCH=auto()
       
        # set lower than operations
        SLTS=auto()
        SLTU=auto()
       
        # CSR functions
        MRET=auto()
        SRET=auto()
        DRET=auto()
        ECALL=auto()
        WFI=auto()
        FENCE=auto()
        FENCE_I=auto()
        SFENCE_VMA=auto()
        CSR_WRITE=auto()
        CSR_READ=auto()
        CSR_SET=auto()
        CSR_CLEAR=auto()
       
        # LSU functions
        LD=auto()
        SD=auto()
        LW=auto()
        LWU=auto()
        SW=auto()
        LH=auto()
        LHU=auto()
        SH=auto()
        LB=auto()
        SB=auto()
        LBU=auto()
       
        # Atomic Memory Operations
        AMO_LRW=auto()
        AMO_LRD=auto()
        AMO_SCW=auto()
        AMO_SCD=auto()
       
        AMO_SWAPW=auto()
        AMO_ADDW=auto()
        AMO_ANDW=auto()
        AMO_ORW=auto()
        AMO_XORW=auto()
        AMO_MAXW=auto()
        AMO_MAXWU=auto()
        AMO_MINW=auto()
        AMO_MINWU=auto()
       
        AMO_SWAPD=auto()
        AMO_ADDD=auto()
        AMO_ANDD=auto()
        AMO_ORD=auto()
        AMO_XORD=auto()
        AMO_MAXD=auto()
        AMO_MAXDU=auto()
        AMO_MIND=auto()
        AMO_MINDU=auto()
       
        # Multiplications
        MUL=auto()
        MULH=auto()
        MULHU=auto()
        MULHSU=auto()
        MULW=auto()
       
        # Divisions
        DIV=auto()
        DIVU=auto()
        DIVW=auto()
        DIVUW=auto()
        REM=auto()
        REMU=auto()
        REMW=auto()
        REMUW=auto()
       
        # Floating-Point Load and Store Instructions
        FLD=auto()
        FLW=auto()
        FLH=auto()
        FLB=auto()
        FSD=auto()
        FSW=auto()
        FSH=auto()
        FSB=auto()
       
        # Floating-Point Computational Instructions
        FADD=auto()
        FSUB=auto()
        FMUL=auto()
        FDIV=auto()
        FMIN_MAX=auto()
        FSQRT=auto()
        FMADD=auto()
        FMSUB=auto()
        FNMSUB=auto()
        FNMADD=auto()
       
        # Floating-Point Conversion and Move Instructions
        FCVT_F2I=auto()
        FCVT_I2F=auto()
        FCVT_F2F=auto()
        FSGNJ=auto()
        FMV_F2X=auto()
        FMV_X2F=auto()
       
        # Floating-Point Compare Instructions
        FCMP=auto()
       
        # Floating-Point Classify Instruction
        FCLASS=auto()
       
        # Vectorial Floating-Point Instructions that don't directly map onto the scalar ones
        VFMIN=auto()
        VFMAX=auto()
        VFSGNJ=auto()
        VFSGNJN=auto()
        VFSGNJX=auto()
        VFEQ=auto()
        VFNE=auto()
        VFLT=auto()
        VFGE=auto()
        VFLE=auto()
        VFGT=auto()
        VFCPKAB_S=auto()
        VFCPKCD_S=auto()
        VFCPKAB_D=auto()
        VFCPKCD_D=auto()

        dtype=U.w(7)

    class ArianeDefaultConfig():
        RASDepth = 2
        BTBEntries = 32
        BHTEntries = 128

        NrNonIdempotentRules = 2
        NonIdempotentAddrBase = U.w(128)(0)
        NonIdempotentLength = U.w(128)(0)
        NrExecuteRegionRules = 3

        ExecuteRegionAddrBase = [U.w(64)(0x80000000),U.w(64)(0x10000),U.w(64)(0)]
        ExecuteRegionLength = [U.w(64)(0x40000000),U.w(64)(0x10000),U.w(64)(0x1000)]

        NrCachedRegionRules = 1
        CachedRegionAddrBase = U.w(64)(0x80000000)
        CachedRegionLength = U.w(64)(0x40000000)

        Axi64BitCompliant = U.w(1)(1)
        SwapEndianess = U.w(1)(0)
        DmBaseAddress = U.w(64)(0)

    @classmethod
    def range_check(cls,base,lens,addr):
        return ((addr>=base)&(addr<(base+lens)))

    @classmethod
    def is_inside_cacheable_regions(cls,cfg,address):
        pas=Wire(U.w(ariane_pkg.NrMaxRules))
        pas <<= cls.range_check(cfg.CachedRegionAddrBase,cfg.CachedRegionLength,address)
        res = Wire(Bool)
        with when(pas==U(0)):
            res <<= U(0)
        with otherwise():
            res <<= U(1)
        return res
    
    @classmethod
    def is_inside_nonidempotent_regions(cls,cfg,address):
        tp = Wire(Bool)
        tp <<= U(0)
        for i in range(cfg.NrExecuteRegionRules):
            with when(cls.range_check(cfg.ExecuteRegionAddrBase[i],cfg.ExecuteRegionLength[i], address) != U(0)):
                tp <<= U(1)
        return tp

    @classmethod
    def extract_transfer_size(cls,op):
        res = Wire(U.w(2))
        res <<= U(3)
        r3 = [cls.fu_op.LD,cls.fu_op.SD,cls.fu_op.FLD,cls.fu_op.FSD,
            cls.fu_op.AMO_LRD,cls.fu_op.AMO_SCD,
            cls.fu_op.AMO_SWAPD,cls.fu_op.AMO_ADDD,
            cls.fu_op.AMO_ANDD,cls.fu_op.AMO_ORD,
            cls.fu_op.AMO_XORD,cls.fu_op.AMO_MAXD,
            cls.fu_op.AMO_MAXDU,cls.fu_op.AMO_MIND,
            cls.fu_op.AMO_MINDU ]
        r2 = [cls.fu_op.LW,cls.fu_op.LWU,cls.fu_op.SW,cls.fu_op.FLW,cls.fu_op.FSW,
            cls.fu_op.AMO_LRW,cls.fu_op.AMO_SCW,
            cls.fu_op.AMO_SWAPW,cls.fu_op.AMO_ADDW,
            cls.fu_op.AMO_ANDW,cls.fu_op.AMO_ORW,
            cls.fu_op.AMO_XORW,cls.fu_op.AMO_MAXW,
            cls.fu_op.AMO_MAXWU,cls.fu_op.AMO_MINW,
            cls.fu_op.AMO_MINWU]
        r1 = [cls.fu_op.LH,cls.fu_op.LHU,cls.fu_op.SH,cls.fu_op.FLH,cls.fu_op.FSH]
        r0 = [cls.fu_op.LB,cls.fu_op.LBU,cls.fu_op.SB,cls.fu_op.FLB,cls.fu_op.FSB]
        with when(Inside(op,list(map(lambda x:U(x.value),r3)))):
            res <<= U(3)
        with elsewhen(Inside(op,list(map(lambda x:U(x.value),r2)))):
            res <<= U(2)
        with elsewhen(Inside(op,list(map(lambda x:U(x.value),r1)))):
            res <<= U(1)
        with elsewhen(Inside(op,list(map(lambda x:U(x.value),r0)))):
            res <<= U(0)
        with otherwise():
            res <<= U(3)
        return res
        
    amo_req_t=Bundle(
        req=Bool,
        amo_op=amo_t.dtype,
        sizex=U.w(2),
        operand_a=U.w(64),
        operand_b=U.w(64)
    )
    
    amo_resp_t=Bundle(
        ack=Bool,
        result=U.w(64)
    )

    lsu_ctrl_t=Bundle(
        valid=Bool,
        vaddr=U.w(riscv.VLEN),
        oveflow=Bool,
        data=U.w(64),
        be=U.w(8),
        fu=fu_t.dtype,
        operator=fu_op.dtype.value,
        trans_id=U.w(TRANS_ID_BITS)
    )

    exception_t=Bundle(
        cause=U.w(64),
        tval=U.w(64),
        valid=Bool
    )

    dcache_req_o_t=Bundle(
        data_gnt=Bool,
        data_rvalid=Bool,
        data_rdata=U.w(64)
    )

    dcache_req_i_t=Bundle(
        address_index=U.w(DCACHE_INDEX_WIDTH),
        address_tag=U.w(DCACHE_TAG_WIDTH),
        data_wdata=U.w(64),
        data_req=Bool,
        data_we=Bool,
        data_be=U.w(8),
        data_size=U.w(2),
        kill_req=Bool,
        tag_valid=Bool
    )   
        

# ********** 蒋宇涛 2020.8.27 End ********** #

def Inside(left,right):
    res = Wire(Bool)
    res <<= U(0)
    for it in right:
        with when(left == it):
            res <<= U(1)
    return res
        
# ********** 蒋宇涛 2020.8.30,31 Start ********** #

def VecSel(vector,sel_signal,dtype):   # 此函数firrtl编译时存在bug
    tp = Wire(dtype)
    for i in range(len(vector)):
        with when(sel_signal == U(i)):
            BundleLink(tp,vector[i],dtype)
    with otherwise():
        BundleLink(tp,U(0),dtype)
    return tp

def VecAllo(_input,allo_signal,vector,buntype = None):
    if(buntype is not None):
        for i in range(len(vector)):
            with when(allo_signal == U(i)):
                BundleLink(vector[i],_input,buntype)
    else:
        for i in range(len(vector)):
            with when(allo_signal == U(i)):
                vector[i] <<= _input

def VecLink(vecL,vecR,buntype=None):
    if(buntype is None):
        for i in range(len(vecL)):
            vecL[i] <<= vecR[i]
    else:
        for i in range(len(vecL)):
            BundleLink(vecL[i],vecR[i],buntype)
    
def BundleLink(bunL,bunR,buntype):
    try:
        for it in buntype._kv:
            exec("bunL.{} <<= bunR.{}".format(it,it))
    except:
        try:
            for it in buntype._kv:
                exec("bunL.{} <<= bunR".format(it))
        except:
            bunL <<= bunR 
        
# ********** 蒋宇涛 2020.8.30,31 End ********** #

# ********** 蒋宇涛 2020.8.28,30 Begin ********** #

def fifo_v3(FALL_THROUGH=0,DATAWIDTH=32,DEPTH=8,dtype=None,ADDR_DEPTH=None):
    if dtype is None:
        dtype = U.w(DATAWIDTH)
    if ADDR_DEPTH is None:
        ADDR_DEPTH = math.ceil(math.log(DEPTH,2)) if DEPTH>1 else 1

    class fifo(Module):
        io=IO(
            flush_i=Input(Bool),
            testmode_i=Input(Bool),

            full_o=Output(Bool),
            empty_o=Output(Bool),
            usage_o=Output(U.w(ADDR_DEPTH)),

            data_i=Input(dtype),
            push_i=Input(Bool),

            data_o=Output(dtype),
            pop_i=Input(Bool)
        )

        FIFO_DEPTH = DEPTH if DEPTH>0 else 1
        gate_clock = Wire(Bool)
        [read_pointer_n,read_pointer_q,write_pointer_n,write_pointer_q] = [Reg(U.w(ADDR_DEPTH)) for i in range(4)]
        status_cnt_n = Reg(U.w(ADDR_DEPTH+1))
        status_cnt_q = Reg(U.w(ADDR_DEPTH+1))
        mem_n = [Reg(dtype) for i in range(FIFO_DEPTH)]
        mem_q = [Reg(dtype) for i in range(FIFO_DEPTH)]
        
        io.usage_o <<= status_cnt_q

        if (DEPTH == 0):
            io.empty_o <<= ~io.push_i
            io.full_o <<= ~io.pop_i
        else:
            io.full_o <<= Mux(status_cnt_q==U(FIFO_DEPTH),U(1),U(0))
            io.empty_o <<= Mux(status_cnt_q==U(0),U(1),U(0)) & ~(U(FALL_THROUGH) & io.push_i)

        read_pointer_n <<= read_pointer_q
        write_pointer_n <<= write_pointer_q
        status_cnt_n <<= status_cnt_q
        BundleLink(io.data_o,io.data_i if (DEPTH == 0) else VecSel(mem_q,read_pointer_q,dtype),dtype) 
        
        VecLink(mem_n,mem_q,dtype)
        gate_clock <<= U(1)
        
        with when(io.push_i & ~io.full_o):
            VecAllo(io.data_i,write_pointer_q,mem_n,dtype)
            
            gate_clock <<= U(0)
            with when (write_pointer_q == U(FIFO_DEPTH - 1)):
                write_pointer_n <<= U(0)
            with otherwise():
                write_pointer_n <<= write_pointer_q + U(1)
            status_cnt_n <<= status_cnt_q + U(1)
        
        with when(io.pop_i & ~io.empty_o):
            with when(read_pointer_n == U(FIFO_DEPTH - 1)):
                read_pointer_n <<= U(0)
            with otherwise():
                read_pointer_n <<= read_pointer_q + U(1)
            status_cnt_n <<= status_cnt_q - U(1)
        
        with when((io.push_i & io.pop_i) & (~io.full_o & ~io.empty_o)):
            status_cnt_n <<= status_cnt_q
        # ********** 蒋宇涛 2020.8.28,30 End ********** #
        # ********** 蒋宇涛 2020.8.30,31 Start ********** #
        with when((U(FALL_THROUGH) & io.push_i) & (status_cnt_q == U(0))):
            BundleLink(io.data_o,io.data_i,dtype)
            with when(io.pop_i == U(1)):
                status_cnt_n <<= status_cnt_q
                read_pointer_n <<= read_pointer_q
                write_pointer_n <<= write_pointer_q
        
        with when((Module.reset == U(0)) | (io.flush_i == U(1))):
            read_pointer_q <<= U(0)
            write_pointer_q <<= U(0)
            status_cnt_q <<= U(0)
        with otherwise():
            read_pointer_q <<= read_pointer_n
            write_pointer_q <<= write_pointer_n
            status_cnt_q <<= status_cnt_n
        
        with when(Module.reset == U(0)):
            for i in mem_q:
                BundleLink(i,U(0),dtype)
        with elsewhen(gate_clock == U(0)):
            VecLink(mem_q,mem_n,dtype)
        
    return fifo()

# ********** 蒋宇涛 2020.8.30,31 End ********** #