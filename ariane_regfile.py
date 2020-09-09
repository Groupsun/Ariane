
from pyhcl import *
#********刘康杰 2020.9.2 Begin *******#
   #DATA_WIDTH     = 32
   #NR_READ_PORTS  = 2
   #NR_WRITE_PORTS = 2
   #ZERO_REG_ZERO  = 0

class cluster_clock_gating(Module):
    io = IO(
            
        clk_i=Input(U.w(1)),
        en_i=Input(U.w(1)),
        test_en_i=Input(U.w(1)),
        clk_o=Output(U.w(1))
    )
    clk_en= Reg(U.w(1))
    with when(io.clk_i==U.w(1)(0)):
        clk_en <<= io.en_i | io.test_en_i
    io.clk_o <<= io.clk_i & clk_en

def Ariane_regfile_lol(DATA_WIDTH:int,NR_READ_PORTS:int,NR_WRITE_PORTS:int,ZERO_REG_ZERO:bool):
 
    
  
    class ariane_regfile_lol(Module):
        io = IO(

            clk_i=Input(U.w(1)),

            rst_ni=Input(U.w(1)),
            
            test_en_i=Input(U.w(1)),
            
            raddr_i=Input(Vec(NR_READ_PORTS,U.w(5))),

            rdata_o=Output(Vec(NR_READ_PORTS,U.w(DATA_WIDTH))),

            waddr_i=Input(Vec(NR_WRITE_PORTS,U.w(5))),
            
            wdata_i=Input(Vec(NR_WRITE_PORTS,U.w(DATA_WIDTH))),
            
            we_i=Input(U.w(NR_WRITE_PORTS))
            

        )
        ADDR_WIDTH = 5
        NUM_WORDS  = 2**ADDR_WIDTH
        flag=RegInit(U.w(1)(1))
        



        clk_last= RegInit(U.w(1)(1))
        with when(flag==U(1)):
            clk_last<<=io.rst_ni
            flag<<=U(0)
            
        mem_clocks= Reg(U.w(NUM_WORDS-ZERO_REG_ZERO))
        mem=Reg(Vec(NUM_WORDS,U.w(DATA_WIDTH)))
        waddr_onehot=Reg(Vec(NR_WRITE_PORTS,U.w(NUM_WORDS)))
        waddr_onehot_q=Reg(Vec(NR_WRITE_PORTS,U.w(NUM_WORDS)))
        wdata_q=Reg(Vec(NR_WRITE_PORTS,U.w(DATA_WIDTH)))


        


        
       

            

        for i in range(NR_READ_PORTS):
            io.rdata_o[i]<<=mem[io.raddr_i[i][ADDR_WIDTH-1:0]]
        
        # always_ff
        
        with when(clk_last==U(0)&io.clk_i):
             clk_last <<= U(1)
             for i in range(NR_WRITE_PORTS):
                 wdata_q[i] <<= U(0)
        with when(clk_last==U(1)&~io.clk_i):
            for i in range(NR_WRITE_PORTS):
                with when(io.we_i[i]):
                    wdata_q[i]<<= io.wdata_i[i]
            waddr_onehot_q <<= waddr_onehot


    
        #always_comb
        for i in range (NR_WRITE_PORTS):
            for j in range(1,NUM_WORDS):
                with when(io.we_i[i]&(io.waddr_i[i] == U(j))):
                    waddr_onehot[i][j] <<= U.w(1)(1)
                with otherwise():
                    waddr_onehot[i][j] <<= U.w(1)(0)
    #
        for x in range (ZERO_REG_ZERO,NUM_WORDS):
            waddr_ored=Reg(U.w(NR_WRITE_PORTS))
            for i in range (NR_WRITE_PORTS):
                waddr_ored[i] <<= waddr_onehot[i][x]
                i_cg=cluster_clock_gating()
                i_cg.io.clk_i<<=io.clk_i
                with when(waddr_ored==U(0)):
                    i_cg.io.en_i<<=U(0)
                with otherwise():
                    i_cg.io.en_i<<=U(1)
                i_cg.io.test_en_i<<=io.test_en_i
                mem_clocks[x] <<=i_cg.io.clk_o



   

    #always_latch
        if(ZERO_REG_ZERO):#with when?
            mem[0] <<= U(0)

        for i in range (NR_WRITE_PORTS):
            for k in range (ZERO_REG_ZERO,NUM_WORDS):
                with when(mem_clocks[k] & waddr_onehot_q[i][k]):
                    mem[k] <<= wdata_q[i]

  

    return ariane_regfile_lol()
#********刘康杰 2020.9.2 End *******#


if __name__== '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(Ariane_regfile_lol(32, 2, 2, 0)), "Ariane_regfile_lol.fir"))
