from pyhcl import*
#import ariane_pkg
INSTR_PER_FETCH=0
FETCH_WIDTH=64
def get_per_fetch():
    with when(FETCH_WIDTH==64):
        INSTR_PER_FETCH=U(4)
    with elsewhen(FETCH_WIDTH==32):
        INSTR_PER_FETCH=U(2)

class riscv:
    VLEN = 64

get_per_fetch()
# ***********梁靖欣 8.31 Begin***********#
def Instr_realign(FETCH_WIDTH: int):
    class instr_realign(Module):
        io = IO(
        clk_i=Input(Bool),
        rst_ni=Input(Bool),
        flush_i=Input(Bool),
        valid_i=Input(Bool),
        serving_unaligned_o=Output(Bool),
        address_i=Input(U.w(riscv.VLEN)),
        data_i=Input(U.w(FETCH_WIDTH)),
        valid_o=Output(U.w(INSTR_PER_FETCH)),
        addr_o=Output(Vec(INSTR_PER_FETCH, riscv.VLEN)),
        instr_o=Output(Vec(INSTR_PER_FETCH, 32))
    )
        instr_is_compressed = Reg(U.w(4))
        for i in range(INSTR_PER_FETCH):
            pass
        # instr_is_compressed[i]=
        unaligned_instr_d = Reg(U.w(16))
        unaligned_instr_q = Reg(U.w(16))
        unaligned_d = Reg(U.w(1))
        unaligned_q = Reg(U.w(1))
        unaligned_address_d = Reg(U.w(riscv.VLEN))
        unaligned_address_q = Reg(U.w(riscv.VLEN))
        io.serving_unaligned_o <<= unaligned_q
        with when(FETCH_WIDTH == U(32)):
            unaligned_d = unaligned_q
            for i in range(riscv.VLEN-2):
                unaligned_address_d[i] = io.address_i[riscv.VLEN-1 - i]
            unaligned_address_d[riscv.VLEN-2] = U(1)
            unaligned_address_d[riscv.VLEN-1] = U(0)
            for i in range(16):
                unaligned_instr_d[i] = io.data_i[31-i]
            io.valid_o[0] <<= io.valid_i
            with when(unaligned_q == U(1)):
                for i in range(16):
                    io.instr_o[0][i] <<= io.data_i[15-i]
                for i in range(16):
                    io.instr_o[0][16 + i] <<= unaligned_instr_q[i]
                for i in range(64):
                    io.addr_o[0][i] <<= unaligned_address_q[i]
            with otherwise():
                for i in range(32):
                    io.instr_o[i] <<= io.data_i[31-i]
                    io.addr_o[0][i] <<= io.address_i[i]
            io.valid_o[1] <<= U(0)
            io.instr_o[1] <<= U(0)
            for i in range(riscv.VLEN-2):
                io.addr_o[1][i] = io.address_i[riscv.VLEN-1 - i]
            io.addr_o[1][riscv.VLEN-2] <<= U(1)
            io.addr_o[1][riscv.VLEN-1] <<= U(0)
            with when(instr_is_compressed[0] != U(0) or unaligned_q != U(0)):
                with when(instr_is_compressed[1] != U(0)):
                    unaligned_d = U(0)
                    io.valid_o[i] <<= io.valid_i
                    for i in range(16):
                        io.instr_o[1][i] <<= U(0)
                    for i in range(16):
                        io.instr_o[1][16+i] <<= io.data_i[31-i]
                with otherwise():
                    unaligned_d <<= U(1)
                    for i in range(16):
                        unaligned_instr_d[i] = io.data_i[31-i]
                    for i in range(riscv.VLEN-2):
                        unaligned_address_d[i] = io.address_i[riscv.VLEN-1 - i]
                    unaligned_address_d[riscv.VLEN-2] = U(1)
                    unaligned_address_d[riscv.VLEN-1] = U(0)
                with when(io.valid_i != U(0) and io.address_i[1] != U(0)):
                    with when(instr_is_compressed[0] == U(0)):
                        io.valid_o <<= U(0)
                        unaligned_d = U(1)
                        for i in range(riscv.VLEN-2):
                            unaligned_address_d = io.address_i[riscv.VLEN-1 - i]
                        unaligned_address_d[riscv.VLEN-2] = U(1)
                        unaligned_address_d[riscv.VLEN-1] = U(0)
                        for i in range(16):
                            unaligned_instr_d[i] = io.data_i[15-i]
                    with otherwise():
                        io.valid_o <<= U(1)
# ***********梁靖欣 8.31 End***********#
# ***********罗岚 8.31 Begin***********#
            with elsewhen(FETCH_WIDTH == U(64)):
                # initial?
                unaligned_d = unaligned_q
                unaligned_address_d = unaligned_address_q
                unaligned_instr_d = unaligned_instr_q
                io.valid_o <<= U(0)
                io.valid_o[0] <<= io.valid_i
                for i in range(32):
                    io.instr_o[0][i] <<= io.data_i[i]
                for i in range(64):
                    io.addr_o[0][i] <<= io.address_i[i]
                io.instr_o[1] <<= U(0)
                for i in range(61):
                    io.addr_o[1][i] <<= io.address_i[riscv.VLEN-1 - i]
                io.addr_o[1][61] <<= U(0)
                io.addr_o[1][62] <<= U(1)
                io.addr_o[1][63] <<= U(0)
                for i in range(16):
                    io.instr_o[2][i] <<= U(0)
                for i in range(16, 32):
                    io.instr_o[2][i] <<= io.data_i[63 - i]
                for i in range(61):
                    io.addr_o[2][i] <<= io.address_i[riscv.VLEN-1 - i]
                io.addr_o[2][61] <<= U(1)
                io.addr_o[2][62] <<= U(0)
                io.addr_o[2][63] <<= U(0)
                for i in range(16):
                    io.instr_o[3][i] <<= U(0)
                for i in range(16, 32):
                    io.instr_o[3][i] <<= io.data_i[79 - i]
                for i in range(61):
                    io.addr_o[3][i] <<= io.address_i[riscv.VLEN-1 - i]
                io.addr_o[3][61] <<= U(1)
                io.addr_o[3][62] <<= U(1)
                io.addr_o[3][63] <<= U(0)

                with when(unaligned_q == U(1)):
                    for i in range(16):
                        io.instr_o[0][i] <<= io.data_i[15 - i]
                    for i in range(16, 32):
                        io.instr_o[0][i] <<= unaligned_instr_q[i]
                    for i in range(64):
                        io.addr_o[0][i] <<= unaligned_address_q[i]
                    with when(instr_is_compressed[1] == U(1)):
                        for i in range(16):
                            io.instr_o[1][i] <<= U(0)
                        for i in range(16, 32):
                            io.instr_o[1][i] <<= io.data_i[47 - i]
                        io.valid_o[1] <<= io.valid_i
                        with when(instr_is_compressed[2] == U(1)):
                            with when(instr_is_compressed[3] == U(1)):
                                unaligned_d <<= U(0)
                                io.valid_o[3] <<= io.valid_i
                        with otherwise():
                            unaligned_d <<= U(0)
                            for i in range(32):
                                io.instr_o[2][i] <<= io.data_i[63 - i]
                            io.valid_o[2] <<= io.valid_i
                    with otherwise():
                        for i in range(32):
                            io.instr_o[1][i] <<= io.data_i[47 - i]
                        io.valid_o[1] <<= io.valid_i
                        for i in range(61):
                            io.addr_o[2][i] <<= io.address_i[riscv.VLEN-1 - i]
                        io.addr_o[2][61] <<= U(1)
                        io.addr_o[2][62] <<= U(1)
                        io.addr_o[2][63] <<= U(0)
                        with when(instr_is_compressed[2] == U(1)):
                            unaligned_d <<= U(0)
                            for i in range(16):
                                io.instr_o[2][i] <<= U(0)
                            for i in range(16, 32):
                                io.instr_o[2][i] <<= io.data_i[79 - i]
                            io.valid_o[2] <<= io.valid_i
                with elsewhen(instr_is_compressed[0] == U(1)):
                    with when(instr_is_compressed[1] == U(1)):
                        for i in range(16):
                            io.instr_o[1][i] <<= U(0)
                        for i in range(16, 32):
                            io.instr_o[1][i] <<= io.data_i[47 - i]
                        with when(instr_is_compressed[2] == U(1)):
                            io.valid_o[2] <<= io.valid_i
                            with when(instr_is_compressed[3] == U(1)):
                                io.valid_o[3] <<= io.valid_i
                            with otherwise():
                                unaligned_d <<= U(1)
                                for i in range(16):
                                    unaligned_instr_d[i] <<= io.data_i[63 - i]
                                for i in range(64):
                                    unaligned_address_d[i] <<= io.addr_o[3][i]
                        with otherwise():
                            for i in range(32):
                                io.instr_o[2][i] <<= io.data_i[63 - i]
                            io.valid_o[2] <<= io.valid_i
                    with otherwise():
                        for i in range(32):
                            io.instr_o[1][i] <<= io.data_i[47 - i]
                        io.valid_o[1] <<= io.valid_i
                        for i in range(61):
                            io.addr_o[2][i] <<= io.address_i[riscv.VLEN-1 - i]
                        io.addr_o[2][61] <<= U(1)
                        io.addr_o[2][62] <<= U(1)
                        io.addr_o[2][63] <<= U(0)
                        with when(instr_is_compressed[3] == U(1)):
                            for i in range(16):
                                io.instr_o[2][i] <<= io.data_i[63 - i]
                            io.valid_o[2] <<= io.valid_i
                        with otherwise():
                            unaligned_d <<= U(1)
                            for i in range(16):
                                unaligned_instr_d[i] <<= io.data_i[63 - i]
                            for i in range(64):
                                unaligned_address_d[i] <<= io.addr_o[2][i]
                with otherwise():
                    for i in range(61):
                        io.addr_o[1][i] <<= io.address_i[riscv.VLEN-1 - i]
                    io.addr_o[1][61] <<= U(1)
                    io.addr_o[1][62] <<= U(0)
                    io.addr_o[1][63] <<= U(0)
                with when(instr_is_compressed[2] == U(1)):
                    for i in range(16):
                        io.instr_o[1][i] <<= U(0)
                    for i in range(16, 32):
                        io.instr_o[1][i] <<= io.data_i[63 - i]
                    io.valid_o[1] <<= io.valid_i
                    for i in range(61):
                        io.addr_o[2][i] <<= io.address_i[riscv.VLEN-1 - i]
                    io.addr_o[2][61] <<= U(1)
                    io.addr_o[2][62] <<= U(1)
                    io.addr_o[2][63] <<= U(0)
                    with when(instr_is_compressed[3] == U(1)):
                        io.valid_o[2] <<= io.valid_i
                        for i in range(16):
                            io.addr_o[2][i] <<= U(0)
                        for i in range(16, 32):
                            io.addr_o[2][i] <<= io.data_i[79 - i]
                    with otherwise():
                        unaligned_d <<= U(1)
                        for i in range(16):
                            unaligned_instr_d[i] <<= io.data_i[63 - i]
                        for i in range(64):
                            unaligned_address_d[i] <<= io.addr_o[2][i]
                with otherwise():
                    for i in range(32):
                        io.instr_o[1][i] <<= io.data_i[63 - i]
                    io.valid_o[1] <<= io.valid_i
# ***********罗岚 8.31 End***********#
# ***********梁靖欣 9.7 Begin***********#
                with when(io.address_i[2]==U(0) and io.address_i[1]==U(1)):
                    io.addr_o[0][riscv.VLEN-3]<<=U(0)
                    io.addr_o[0][riscv.VLEN-2]<<=U(1)
                    io.addr_o[0][riscv.VLEN-1]<<=U(0)
                    for i in range(riscv.VLEN-3):
                        io.addr_o[0][i]<<=io.address_i[riscv.VLEN-1-i]
                    with when(instr_is_compressed[1]!=U(0)):
                        for i in range(16):
                            io.instr_o[0][i]<<=U(0)
                        for i in range(16):
                            io.instr_o[0][16+i]<<=io.data_i[31-i]
                        io.valid_o[0]<<=io.valid_i

                        with when(instr_is_compressed[2]!=U(0)):
                            io.valid_o[1]<<=io.valid_i
                            for i in range(16):
                                io.instr_o[0][i]<<=U(0)
                            for i in range(16):
                                io.instr_o[0][16+i]<<=io.data_i[47-i]
                            for i in range(riscv.VLEN-3):
                                io.addr_o[1][i]<<=io.address_i[riscv.VLEN-1-i]
                            io.addr_o[1][riscv.VLEN-3]<<=U(1)
                            io.addr_o[1][riscv.VLEN-2]<<=U(0)
                            io.addr_o[1][riscv.VLEN-1]<<=U(0)
                            with when(instr_is_compressed[3]!=U(0)):
                                for i in range(16):
                                    io.instr_o[2][i]<<=U(0)
                                for i in range(16):
                                    io.instr_o[2][16+i]<<=io.data_i[riscv.VLEN-1-i]
                                for i in range(riscv.VLEN-3):
                                    io.addr_o[2][i]<<=io.address_i[riscv.VLEN-1-i]
                                io.addr_o[2][riscv.VLEN-3]<<=U(1)
                                io.addr_o[2][riscv.VLEN-2]<<=U(1)
                                io.addr_o[2][riscv.VLEN-1]<<=U(0)
                                io.valid_o[2]<<=io.valid_i
                            with otherwise():
                                unaligned_d=U(1)
                                for i in range(16):
                                    unaligned_instr_d[i]=io.data_i[63-i]
                                unaligned_address_d=io.addr_o[3]
                        with otherwise():
                            for i in range(32):
                                io.instr_o[1][i]<<=io.data_i[63-i]
                            for i in range(riscv.VLEN-3):
                                io.addr_o[1][i] <<= io.address_i[riscv.VLEN-1 - i]
                            io.addr_o[1][riscv.VLEN-3] <<= U(1)
                            io.addr_o[1][riscv.VLEN-2] <<= U(0)
                            io.addr_o[1][riscv.VLEN-1] <<= U(0)
                            io.valid_o[1]<<io.valid_i
                    with otherwise():
                        for i in range(32):
                            io.instr_o[0][i]<<=io.data_i[47-i]
                        io.valid_o[0]<<=io.valid_i
                        for i in range(riscv.VLEN-3):
                            io.addr_o[1][i] <<= io.address_i[riscv.VLEN-1 - i]
                        io.addr_o[1][riscv.VLEN-3] <<= U(1)
                        io.addr_o[1][riscv.VLEN-2] <<= U(1)
                        io.addr_o[1][riscv.VLEN-1] <<= U(0)
                        with when(instr_is_compressed[3]!=U(0)):
                            for i in range(16):
                                io.instr_o[1][i]<<=io.data_i[63-i]
                            io.valid_o[1]<<=io.valid_i
                        with otherwise():
                            unaligned_d=U(1)
                            for i in range(16):
                                unaligned_instr_d=io.data_i[63-i]
                            unaligned_address_d=io.addr_o[1]
                with elsewhen(io.address_i[2]==U(1) and io.address_i[1]==U(0)):
                    io.valid_o<<=U(0)
                    with when(instr_is_compressed[2]!=U(0)):
                        io.valid_o[0]<<=io.valid_i
                        for i in range(16):
                            io.instr_o[0][i]<<=io.data_i[47-i]
                        with when(instr_is_compressed[3]!=U(0)):
                            io.valid_o[1]<<=io.valid_i
                            for i in range(16):
                                io.instr_o[1][i] <<= io.data_i[63-i]
                        with otherwise():
                            unaligned_d<<=U(1)
                            for i in range(riscv.VLEN-3):
                                unaligned_address_d = io.address_i[riscv.VLEN-1 - i]
                            unaligned_address_d[riscv.VLEN-3] <<= U(1)
                            unaligned_address_d[riscv.VLEN-2] <<= U(1)
                            unaligned_address_d[riscv.VLEN-1] <<= U(0)
                            for i in range(16):
                                unaligned_instr_d[i]=io.data_i[63-i]
                    with otherwise():
                        io.valid_o[0]<<=io.valid_i
                        for i in range(32):
                            io.instr_o[0][i]<<=io.data_i[63-i]
                        io.addr_o[0]<<=io.address_i
                with elsewhen(io.address_i[2]==U(1) and io.address_i[1]==U(1)):
                    io.valid_o<<=U(0)
                    with when(instr_is_compressed[3]==U(0)):
                        unaligned_d=U(1)
                        for i in range(riscv.VLEN-3):
                            unaligned_address_d = io.address_i[riscv.VLEN-1 - i]
                        unaligned_address_d[riscv.VLEN-3] <<= U(1)
                        unaligned_address_d[riscv.VLEN-2] <<= U(1)
                        unaligned_address_d[riscv.VLEN-1] <<= U(0)
                        for i in range(16):
                            unaligned_instr_d=io.data_i[63-i]
                    with otherwise():
                        io.valid_o[3]<<=io.valid_i
                with otherwise():
                    pass
# ***********梁靖欣 9.7 End***********#
# ***********罗岚 9.7 Begin***********#
        a = Reg(U.w(2))
        with when(io.clk_i!=a[0] or io.rst_ni!=a[1]):
            with when(io.rst_ni==U(0)):
                unaligned_q<<=U(0)
                unaligned_address_q<<=U(0)
                unaligned_instr_q<<=U(0)
            with otherwise():
                with when(io.valid_i==U(1)):
                    unaligned_address_q<<=unaligned_address_d
                    unaligned_instr_q<<=unaligned_instr_d
                with when(io.flush_i==U(1)):
                    unaligned_q<<=U(0)
                with elsewhen(io.valid_i==U(1)):
                    unaligned_q<<=unaligned_d
            a[0]<<=io.clk_i
            a[1]<<=io.rst_ni
# ***********罗岚 9.7 End***********#
