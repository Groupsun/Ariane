#***********莫文仪 8.31 Begin***********#            

# Copyright (C) 2018 to present,
# Copyright and related rights are licensed under the Solderpad Hardware
# License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License.  You may obtain a copy of the License at
# http://solderpad.org/licenses/SHL-2.0. Unless required by applicable law
# or agreed to in writing, software, hardware and materials distributed under
# this License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# Author: Florian Zaruba, ETH Zurich
# Date: 08.02.2018
# Migrated: Luis Vitorio Cargnini, IEEE
# Date: 09.06.2018

# return address stack

from pyhcl import *

# branchpredict scoreboard entry
# this is the struct which we will inject into the pipeline to guide the various
# units towards the correct branch decision and resolve
'''
ras_tdef struct packed {
    logic                   valid;
    logic [riscv::VLEN-1:0] ra;
} ras_t;
'''

DEPTH = 2  # parameter


class riscv:
    VLEN = 64


class ariane_pkg:
    class ras_t:
        valid = Reg(Vec(DEPTH, U.w(1)))
        ra = Reg(Vec(DEPTH, U.w(riscv.VLEN)))


def ras(DEPTH: int):
    class Ras(Module):
        io = IO(
            clk_i=Input(Bool),
            rst_ni=Input(Bool),
            flush_i=Input(Bool),
            push_i=Input(Bool),
            pop_i=Input(Bool),
            data_i=Input(U.w(riscv.VLEN)),
            # output ariane_pkg::ras_t data_o
            data_o_valid=Output(U.w(1)),
            data_o_ra=Output(U.w(riscv.VLEN))
        )

        # stack_d = ariane_pkg.ras_t()
        stack_q = ariane_pkg.ras_t()

        io.data_o_valid <<= stack_q.valid[U(0)]
        io.data_o_ra <<= stack_q.ra[U(0)]

        stack_d = stack_q

        # push on the stack
        with when(io.push_i):
            stack_d.ra[U(0)] <<= io.data_i
            # mark the new return address as valid
            stack_d.valid[U(0)] = U.w(1)(1)

            stack_d.valid[U(DEPTH-1)] <<= stack_q.valid[U(DEPTH-2)]
            stack_d.ra[U(DEPTH-1)] <<= stack_q.ra[U(DEPTH-2)]

        with when(io.pop_i):
            stack_d.valid[U(DEPTH-2)] <<= stack_q.valid[U(DEPTH-1)]
            stack_d.ra[U(DEPTH-2)] <<= stack_q.ra[U(DEPTH-1)]
            # we popped the value so invalidate the end of the stack
            stack_d.valid[U(DEPTH-1)] = U.w(1)(0)
            stack_d.ra[U(DEPTH-1)] = U.w(riscv.VLEN)(0)

        with when(io.pop_i & io.push_i):
            stack_d = stack_q
            stack_d.ra[U(0)] <<= io.data_i
            stack_d.valid[U(0)] = U.w(1)(1)

        with when(io.flush_i):
            stack_d.ra[U(0)] <<= U.w(1)(0)
            stack_d.ra[U(1)] <<= U.w(1)(0)
            stack_d.valid[U(0)] <<= U.w(riscv.VLEN)(0)
            stack_d.valid[U(1)] <<= U.w(riscv.VLEN)(0)

        stack_q.ra[U(0)] <= stack_d.ra[U(0)]
        stack_q.ra[U(1)] <= stack_d.ra[U(1)]
        stack_q.valid[U(0)] <= stack_d.valid[U(0)]
        stack_q.valid[U(1)] <= stack_d.valid[U(1)]
        
    return Ras()

def main():
    f = Emitter.dump(Emitter.emit(ras(2)), "ras.fir")
    Emitter.dumpVerilog(f)


if __name__ == '__main__':
    main()

#***********莫文仪 8.31 End***********#            
