# **************<莫文仪><9.1>Brgin************************#
from pyhcl import *
import numpy as np

DEPTH = 8

def fifo_v3(FALL_THROUGH: int = 0, DATA_WIDTH: int = 32, DEPTH: int = 8,
            ADDR_DEPTH: int = np.log2(DEPTH) if (DEPTH > 1) else 1):
    class Fifo_v3(Module):
        io = IO(
            clk_i=Input(Bool),
            rst_ni=Input(Bool),
            flush_i=Input(Bool),
            testmode_i=Input(Bool),

            full_o=Output(Bool),
            empty_o=Output(Bool),
            usage_o=Output(U.w(ADDR_DEPTH)),


            data_i=Input(U.w(DATA_WIDTH)),
            push_i=Input(Bool),

            data_o=Output(U.w(DATA_WIDTH)),
            pop_i=Input(Bool),
        )
        FIFO_DEPTH = DEPTH if (DEPTH > 0) else 1

        gate_clock = RegInit(U.w(1)(0))

        read_pointer_n = Reg(U.w(ADDR_DEPTH))
        read_pointer_q = Reg(U.w(ADDR_DEPTH))

        write_pointer_n = Wire(U.w(ADDR_DEPTH))
        write_pointer_q = Wire(U.w(ADDR_DEPTH))
        write_pointer_q <<= U(1)

        status_cnt_n = Reg(U.w(ADDR_DEPTH))
        status_cnt_q = Reg(U.w(ADDR_DEPTH))

        mem_q = Reg(Vec(FIFO_DEPTH, U.w(DATA_WIDTH)))
        mem_n = mem_q

        io.usage_o <<= status_cnt_q

        if (DEPTH == 0):
            io.empty_o <<= ~io.push_i
            io.full_o <<= ~io.pop_i

        else:
            io.full_o <<= (status_cnt_q == U(FIFO_DEPTH))
            io.empty_o <<= ((status_cnt_q == U(0)) & ~(U(FALL_THROUGH) & io.push_i))

        read_pointer_n <<= read_pointer_q

        write_pointer_n <<= write_pointer_q

        status_cnt_n <<= status_cnt_q

        io.data_o <<= io.data_i if (DEPTH == 0) else mem_q[read_pointer_q]
        mem_n <<= mem_q
        gate_clock <<= U(1)

        with when(io.push_i & ~io.full_o):
            mem_n[write_pointer_q] <<= io.data_i
            gate_clock <<= U(0)

            with when(write_pointer_q == U(FIFO_DEPTH-1)):
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

        with when(io.push_i & io.pop_i & ~io.full_o & ~io.empty_o):
            status_cnt_n <<= status_cnt_q

        with when(U(FALL_THROUGH) & (status_cnt_q == U(0)) & io.push_i):
            io.data_o <<= io.data_i
            with when(io.pop_i):
                status_cnt_n <<= status_cnt_q
                read_pointer_n <<= read_pointer_q
                write_pointer_n <<= write_pointer_q

        with when(io.rst_ni & ~io.flush_i):
            read_pointer_q <<= read_pointer_n
            write_pointer_q = write_pointer_n
            status_cnt_q <<= status_cnt_n

        with when(io.rst_ni & ~gate_clock):
            mem_q <<= mem_n


    return Fifo_v3()


def main():
    f = Emitter.dump(Emitter.emit(fifo_v3(0,32,8,3)), "fifo_v3.fir")
    Emitter.dumpVerilog(f)


if __name__ == '__main__':
    main()
# **************<莫文仪><9.1>End************************#