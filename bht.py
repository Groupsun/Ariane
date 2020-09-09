#**************<莫文仪><9.1>Begin************************#

from pyhcl import *
import numpy as np


class riscv:
    VLEN = 64


class ariane_pkg:
    FETCH_WIDTH = 32
    INSTR_PER_FETCH = 2



def bht(NR_ENTRIES: int):
    class Bht(Module):
        io = IO(
            clk_i=Input(Bool),
            rst_ni=Input(Bool),
            flush_i=Input(Bool),
            debug_mode_i=Input(Bool),

            vpc_i=Input(U.w(riscv.VLEN)),
            bht_update_i=Input(
                Bundle(valid=Bool, pc=U.w(riscv.VLEN), taken=Bool)),
            # we potentially need INSTR_PER_FETCH predictions/cycle
            bht_prediction_o_valid=Output(
                Vec(ariane_pkg.INSTR_PER_FETCH, Bool)),
            bht_prediction_o_taken=Output(
                Vec(ariane_pkg.INSTR_PER_FETCH, Bool))
        )
        # the last bit is always zero, we don't need it for indexing
        OFFSET = 1
        # re-shape the branch history table
        NR_ROWS = int(NR_ENTRIES / ariane_pkg.INSTR_PER_FETCH)
        # number of bits needed to index the row
        ROW_ADDR_BITS = int(np.log2(ariane_pkg.INSTR_PER_FETCH))
        # number of bits we should use for prediction
        PREDICTION_BITS = int(np.log2(NR_ROWS) + OFFSET + ROW_ADDR_BITS)
        # we are not interested in all bits of the address
        '''
        unread i_unread (.d_i( | vpc_i))
        '''
        bht_d_valid = Reg(Vec(NR_ROWS, Vec(ariane_pkg.INSTR_PER_FETCH, Bool)))
        bht_d_saturation_counter = Reg(
            Vec(NR_ROWS, Vec(ariane_pkg.INSTR_PER_FETCH, U.w(2))))
        bht_q_valid = bht_d_valid
        bht_q_saturation_counter = bht_d_saturation_counter

        index = Wire(U.w(int(np.log2(NR_ROWS))))
        update_pc = Wire(U.w(int(np.log2(NR_ROWS))))

        update_row_index = Wire(U.w(ROW_ADDR_BITS))

        saturation_counter = Wire(U.w(2))

        index <<= io.vpc_i

        update_pc <<= io.bht_update_i.pc

        update_row_index <<= io.bht_update_i.pc

    # prediction assignment
        for i in range(ariane_pkg.INSTR_PER_FETCH):

            io.bht_prediction_o_valid[U(i)] <<= bht_q_valid[index][U(i)]

            io.bht_prediction_o_taken[U(i)] <<= (
                bht_q_saturation_counter[index][U(i)] == Bool(True))

        btb_d_valid = bht_q_valid
        btb_d_saturation_counter = bht_q_saturation_counter
        saturation_counter = bht_q_saturation_counter[update_pc][update_row_index]

        with when(io.bht_update_i.valid & ~io.debug_mode_i):

            bht_d_valid[update_pc][update_row_index] <<= Bool(True)

            with when(saturation_counter == U.w(2)(3)):

                # we can safely decrease it
                with when(~io.bht_update_i.taken):
                    bht_d_saturation_counter[update_pc][update_row_index] <<= saturation_counter - U(1)

           # then check if it saturated in the negative regime e.g.: branch not taken
            with elsewhen(saturation_counter == U.w(2)(0)):
               # we can safely increase it
                with when(io.bht_update_i.taken):
                    bht_d_saturation_counter[update_pc][update_row_index] <<= saturation_counter + U(1)
            with otherwise():  # otherwise we are not in any boundaries and can decrease or increase it
                with when(io.bht_update_i.taken):
                    bht_d_saturation_counter[update_pc][update_row_index] <<= saturation_counter + U(1)
                with otherwise():
                    bht_d_saturation_counter[update_pc][update_row_index] <<= saturation_counter - U(1)

   # evict all entries
        with when(io.flush_i):
            for i in range(NR_ROWS):
                for j in range(ariane_pkg.INSTR_PER_FETCH):
                    bht_q_valid[U(i)][U(j)] <<= U(0)
                    bht_q_saturation_counter[U(i)][(j)] <<= U.w(2)(2)
        with otherwise():
            bht_q_valid <<= bht_d_valid
            bht_q_saturation_counter <<= bht_d_saturation_counter

    return Bht()


def main():
    f = Emitter.dump(Emitter.emit(bht(1024)), "bht.fir")
    Emitter.dumpVerilog(f)


if __name__ == '__main__':
    main()
    
#**************<莫文仪><9.1>End************************#