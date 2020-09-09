#**************<莫文仪><9.1>Brgin************************#
from pyhcl import *
import numpy as np



class riscv:
    VLEN = 64


class ariane_pkg:
    FETCH_WIDTH = 32
    INSTR_PER_FETCH = 2


def btb(NR_ENTRIES: int):
    class Btb(Module):
        io = IO(
            clk_i=Input(Bool),
            rst_ni=Input(Bool),
            flush_i=Input(Bool),
            debug_mode_i=Input(Bool),

            vpc_i=Input(U.w(riscv.VLEN)),
            btb_update_i=Input(Bundle(valid=Bool, pc=U.w(riscv.VLEN), target_address=U.w(riscv.VLEN))),
            btb_prediction_o_valid=Output(U.w(ariane_pkg.INSTR_PER_FETCH)),
            btb_prediction_o_target_address=Output(Vec(ariane_pkg.INSTR_PER_FETCH, U.w(riscv.VLEN))),
        )
        # the last bit is always zero, we don't need it for indexing
        OFFSET = 1
        # re-shape the branch history table
        NR_ROWS = int(NR_ENTRIES / ariane_pkg.INSTR_PER_FETCH)
        # number of bits needed to index the row
        ROW_ADDR_BITS = int(np.log2(ariane_pkg.INSTR_PER_FETCH))
        # number of bits we should use for prediction
        PREDICTION_BITS = int(np.log2(NR_ROWS) + OFFSET + ROW_ADDR_BITS)
        # prevent aliasing to degrade performance
        ANTIALIAS_BITS = 8
        # we are not interested in all bits of the address
        '''
         unread i_unread (.d_i( | vpc_i))
        '''
        # typedef for all branch target entries
        # we may want to try to put a tag field that fills the rest of the PC in-order to mitigate aliasing effects

        btb_d_valid = Reg(Vec(NR_ROWS, Vec(ariane_pkg.INSTR_PER_FETCH, Bool)))
        btb_q_valid = btb_d_valid
        btb_d_target_address = Reg(Vec(NR_ROWS, Vec(ariane_pkg.INSTR_PER_FETCH, U.w(riscv.VLEN))))
        btb_q_target_address = btb_d_target_address

        index = Wire(U.w(int(np.log2(NR_ROWS))))
        update_pc = Wire(U.w(int(np.log2(NR_ROWS))))
        update_row_index = Wire(U.w(ROW_ADDR_BITS))

        index <<= io.vpc_i
        update_pc <<= io.btb_update_i.pc
        update_row_index <<= io.btb_update_i.pc

        # output matching prediction
        for i in range(ariane_pkg.INSTR_PER_FETCH):
            io.btb_prediction_o_valid <<= btb_q_valid[index][U(i)]  # workaround
            io.btb_prediction_o_target_address[U(i)] <<= btb_d_target_address[index][U(i)]

        # -------------------------
        # Update Branch Prediction
        # -------------------------
        # update on a mis-predict

        btb_d_valid = btb_q_valid
        btb_d_target_address = btb_q_target_address

        with when(io.btb_update_i.valid & ~io.debug_mode_i):
            btb_d_valid[update_pc][update_row_index] <<= Bool(True)
            # the target address is simply updated
            btb_d_target_address[update_pc][update_row_index] <<= io.btb_update_i.target_address

        # evict all entries
        with when(io.flush_i):
            for i in range(NR_ROWS):
                for j in range(ariane_pkg.INSTR_PER_FETCH):
                    btb_q_valid[i][j] <<= Bool(False)

        with otherwise():
            btb_q_valid <<= btb_d_valid
            btb_q_target_address <<= btb_d_target_address

    return Btb()


def main():
    f = Emitter.dump(Emitter.emit(btb(8)), "btb.fir")
    Emitter.dumpVerilog(f)


if __name__ == '__main__':
    main()
#**************<莫文仪><9.1>End************************#