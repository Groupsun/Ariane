from pyhcl import *
import math
# ********** 蒋宇涛 2020.8.27 Begin ********** #

class ariane_pkg():

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
            
class riscv():
    PLEN = 56
    VLEN = 64

# ********** 蒋宇涛 2020.8.27 End ********** #

# ********** 蒋宇涛 2020.8.30,31 Start ********** #

def VecSel(vector,sel_signal):   # 此函数firrtl编译时存在bug
    dic = {}
    for i in range(len(vector)):
        dic[U(i)] = vector[i]
    dic[...] = U(0)
    return LookUpTable(sel_signal,dic)

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
        for it in buntype._kv:
            exec("bunL.{} <<= bunR".format(it))
        
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
        BundleLink(io.data_o,io.data_i if (DEPTH == 0) else VecSel(mem_q,read_pointer_q),dtype) 
        VecLink(mem_n,mem_q,dtype)
        gate_clock <<= U(1)
        
        with when(io.push_i & ~io.full_o):
            temp = VecSel(mem_n,write_pointer_q)   
            BundleLink(temp,io.data_i,dtype)
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