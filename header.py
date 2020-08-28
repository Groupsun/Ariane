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

# ********** 蒋宇涛 2020.8.28 Begin ********** #

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
        read_pointer_n,read_pointer_q,write_pointer_n,write_pointer_q = [Reg(U.w(ADDR_DEPTH)) for i in range(4)]
        status_cnt_n = Reg(U.w(ADDR_DEPTH+1))
        status_cnt_q = Reg(U.w(ADDR_DEPTH+1))
        mem_n = Vector(FIFO_DEPTH, Reg(dtype))
        mem_q = Vector(FIFO_DEPTH, Reg(dtype))

        io.usage_o <<= status_cnt_q

        with when(DEPTH == 0):
            io.empty_o <<= ~io.push_i
            io.full_o <<= ~io.pop_i
        with otherwise():
            io.full_o <<= Mux(status_cnt_q==U(FIFO_DEPTH),U(1),U(0))
            io.empty_o <<= Mux(status_cnt_q==U(0),U(1),U(0)) & ~(FALL_THROUGH & io.push_i)

        read_pointer_n <<= read_pointer_q
        write_pointer_n <<= write_pointer_q
        status_cnt_n <<= status_cnt_q
        io.data_o <<= io.data_i if (DEPTH == 0) else mem_q[read_pointer_q]
        mem_n <<= mem_q
        gate_clock <<= U(1)
        
        with when(io.push_i & ~full_o):
            mem_n[write_pointer_q] <<= data_i
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
        
        with ((io.push_i & io.pop_i) & (~io.full_o & ~io.empty_o)):
            status_cnt_n <<= status_cnt_q
                
# ********** 蒋宇涛 2020.8.28 End ********** #




    return fifo