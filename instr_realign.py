from pyhcl import*

#***********梁靖欣 8.31 Begin***********#
class  instr_realign(Module):
    io=IO(
        clk_i=Input(Bool),
        rst_ni=Input(Bool),
        flush_i=Input(Bool),
        valid_i=Input(Bool),
        serving_unaligned_o=Output(Bool),
        address_i=Input(U.w(64)),
        data_i=Input(U.w(32)),
        valid_o=Output(U.w(2)),
        addr_o=Output(Vec(2,64)),
        instr_o=Output(Vec(2,32))
    )
    instr_is_compressed=Reg(U.w(4))
    for i in range(2):
        pass
       #instr_is_compressed[i]=
    unaligned_instr_d=Reg(U.w(16))
    unaligned_instr_q=Reg(U.w(16))
    unaligned_d=Reg(U.w(1))
    unaligned_q=Reg(U.w(1))
    unaligned_address_d=Reg(U.w(64))
    unaligned_address_q = Reg(U.w(64))
    io.serving_unaligned_o<<= unaligned_q
    with when (FETCH_WIDTH==U(32) ):
        unaligned_d=unaligned_q
        for i in range(62):
            unaligned_address_d[i]=io.address_i[63-i]
        unaligned_address_d[1]=U(1)
        unaligned_address_d[0]=U(0)
        for i in range(16):
            unaligned_instr_d[i]=io.data_i[16+i]
        io.valid_o[0]<<=io.valid_i
        with when (unaligned_q == U(1)):
            for i in range(16):
                io.instr_o[0][i]<<=unaligned_instr_q[i]
            for i in range(16):
                io.instr_o[0][16+i]<<=io.data_i[i]
            for i in range(64):
                io.addr_o[0][i]<<=unaligned_address_q[i]
        with otherwise():
            for i in range(32):
                io.instr_o[i]<<=io.data_i[i]
                io.addr_o[0][i] <<= io.address_i[i]
        io.valid_o[1]<<=U(0)
        io.instr_o[1]<<=U(0)
        for i in range(63):
            io.addr_o[1][i]=io.address_i[63-i]
        io.addr_o[1][1]<<=U(1)
        io.addr_o[1][0] <<=U(0)
        with when(instr_is_compressed[0]!=U(0) or unaligned_q!=U(0)):
            with when(instr_is_compressed[1]!=U(0)):
                unaligned_d=U(0)
                io.valid_o[i]<<=io.valid_i
                for i in range(16):
                    io.instr_o[1][i]<<=io.data_i[16+i]
                for i in range(16):
                    io.instr_o[1][16+i]<<=U(0)
            with otherwise():
                unaligned_d<<=U(1)
                for i in range(16):
                    unaligned_instr_d[i] = io.data_i[16 + i]
                for i in range(62):
                    unaligned_address_d =io.address_i[63-i]
                unaligned_address_d[1]=U(1)
                unaligned_address_d[0]=U(0)
            with when(io.valid_i!=U(0) and io.address_i[1]!=U(0)):
                with when(instr_is_compressed[0]==U(0)):
                    io.valid_o<<=U(0)
                    unaligned_d=U(1)
                    for i in range(62):
                        unaligned_address_d = io.address_i[63 - i]
                    unaligned_address_d[1] = U(1)
                    unaligned_address_d[0] = U(0)
                    for i in range(16):
                        unaligned_instr_d[i]=io.data_i[i]
                with otherwise():
                    io.valid_o<<=U(1)
#***********梁靖欣 8.31 End***********#                   
#***********罗岚 8.31 Begin***********#
        with elsewhen(FETCH_WIDTH==U(64)):
            #initial?
            unaligned_d=unaligned_q
            unaligned_address_d=unaligned_address_q
            unaligned_instr_d=unaligned_instr_q
            io.valid_o<<=U(0)
            io.valid_o[0]<<=io.valid_i
            for i in range(32):
                io.instr_o[0][i]<<=io.data_i[i]
            for i in range(64):
                io.addr_o[0][i]<<=io.address_i[i]
            io.instr_o[1]<<=U(0)
            for i in range(61):
                io.addr_o[1][i]<<=io.address_i[63-i]
            io.addr_o[1][61]<<=U(0)
            io.addr_o[1][62]<<=U(1)
            io.addr_o[1][63]<<=U(0)
            for i in range(16):
                io.instr_o[2][i]<<=U(0)
            for i in range(16,32):
                io.instr_o[2][i]<<=io.data_i[63-i]
            for i in range(61):
                io.addr_o[2][i]<<=io.address_i[63-i]
            io.addr_o[2][61]<<=U(1)
            io.addr_o[2][62]<<=U(0)
            io.addr_o[2][63]<<=U(0)
            for i in range(16):
                io.instr_o[3][i]<<=U(0)
            for i in range(16,32):
                io.instr_o[3][i]<<=io.data_i[79-i]
            for i in range(61):
                io.addr_o[3][i]<<=io.address_i[63-i]
            io.addr_o[3][61]<<=U(1)
            io.addr_o[3][62]<<=U(1)
            io.addr_o[3][63]<<=U(0)

            with when(unaligned_q==U(1)):
                for i in range(16):
                    io.instr_o[0][i]<<=io.data_i[15-i]
                for i in range(16,32):
                    io.instr_o[0][i]<<=unaligned_instr_q[i]
                for i in range(64):
                    io.addr_o[0][i]<<=unaligned_address_q[i]
                with when(instr_is_compressed[1]==U(1)):
                    for i in range(16):
                        io.instr_o[1][i]<<=U(0)
                    for i in range(16,32):
                        io.instr_o[1][i]<<=io.data_i[47-i]
                    io.valid_o[1]<<=io.valid_i
                    with when(instr_is_compressed[2]==U(1)):
                        with when(instr_is_compressed[3]==U(1)):
                            unaligned_d<<=U(0)
                            io.valid_o[3]<<=io.valid_i
                    with otherwise():
                        unaligned_d<<=U(0)
                        for i in range(32):
                            io.instr_o[2][i]<<=io.data_i[63-i]
                        io.valid_o[2]<<=io.valid_i
                with otherwise():
                    for i in range(32):
                        io.instr_o[1][i]<<=io.data_i[47-i]
                    io.valid_o[1]<<=io.valid_i
                    for i in range(61):
                        io.addr_o[2][i]<<=io.address_i[63-i]
                    io.addr_o[2][61]<<=U(1)
                    io.addr_o[2][62]<<=U(1)
                    io.addr_o[2][63]<<=U(0)
                    with when(instr_is_compressed[2]==U(1)):
                        unaligned_d<<=U(0)
                        for i in range(16):
                            io.instr_o[2][i]<<=U(0)
                        for i in range(16,32):
                            io.instr_o[2][i]<<=io.data_i[79-i]
                        io.valid_o[2]<<=io.valid_i
            with elsewhen(instr_is_compressed[0]==U(1)):
                with when(instr_is_compressed[1]==U(1)):
                    for i in range(16):
                        io.instr_o[1][i]<<=U(0)
                    for i in range(16,32):
                        io.instr_o[1][i]<<=io.data_i[47-i]
                    with when(instr_is_compressed[2]==U(1)):
                        io.valid_o[2]<<=io.valid_i
                        with when(instr_is_compressed[3]==U(1)):
                            io.valid_o[3]<<=io.valid_i
                        with otherwise():
                            unaligned_d<<=U(1)
                            for i in range(16):
                                unaligned_instr_d[i]<<=io.data_i[63-i]
                            for i in range(64):
                                unaligned_address_d[i]<<=io.addr_o[3][i]
                    with otherwise():
                        for i in range(32):
                            io.instr_o[2][i]<<=io.data_i[63-i]
                        io.valid_o[2]<<=io.valid_i
                with otherwise():
                    for i in range(32):
                        io.instr_o[1][i]<<=io.data_i[47-i]
                    io.valid_o[1]<<=io.valid_i
                    for i in range(61):
                        io.addr_o[2][i]<<=io.address_i[63-i]
                    io.addr_o[2][61]<<=U(1)
                    io.addr_o[2][62]<<=U(1)
                    io.addr_o[2][63]<<=U(0)
                    with when(instr_is_compressed[3]==U(1)):
                        for i in range(16):
                            io.instr_o[2][i]<<=io.data_i[63-i]
                        io.valid_o[2]<<=io.valid_i
                    with otherwise():
                        unaligned_d<<=U(1)
                        for i in range(16):
                            unaligned_instr_d[i]<<=io.data_i[63-i]
                        for i in range(64):
                            unaligned_address_d[i]<<=io.addr_o[2][i]
            with otherwise():
                for i in range(61):
                        io.addr_o[1][i]<<=io.address_i[63-i]
                    io.addr_o[1][61]<<=U(1)
                    io.addr_o[1][62]<<=U(0)
                    io.addr_o[1][63]<<=U(0)
                with when(instr_is_compressed[2]==U(1)):
                    for i in range(16):
                        io.instr_o[1][i]<<=U(0)
                    for i in range(16,32):
                        io.instr_o[1][i]<<=io.data_i[63-i]
                    io.valid_o[1]<<=io.valid_i
                    for i in range(61):
                        io.addr_o[2][i]<<=io.address_i[63-i]
                    io.addr_o[2][61]<<=U(1)
                    io.addr_o[2][62]<<=U(1)
                    io.addr_o[2][63]<<=U(0)
                    with when(instr_is_compressed[3]==U(1)):
                        io.valid_o[2]<<=io.valid_i
                        for i in range(16):
                            io.addr_o[2][i]<<=U(0)
                        for i in range(16,32):
                            io.addr_o[2][i]<<=io.data_i[79-i]
                    with otherwise():
                        unaligned_d<<=U(1)
                        for i in range(16):
                            unaligned_instr_d[i]<<=io.data_i[63-i]
                        for i in range(64):
                            unaligned_address_d[i]<<=io.addr_o[2][i]
                with otherwise():
                    for i in range(32):
                        io.instr_o[1][i]<<=io.data_i[63-i]
                    io.valid_o[1]<<=io.valid_i
            #case...tbc...
#***********罗岚 8.31 End***********#
            
                    




                    
