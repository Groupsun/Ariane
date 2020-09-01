#***********黄铭绚 8.31 Begin***********#
from pyhcl import *
import math 

def OR(a,length):
    for i in range(length):
        if(a[i]==True):
            return True
    return False

def LZC(WIDTH:int,MODE:bool):
    class lzc(Module):
        CNT_WIDTH=0        
        if(WIDTH==1):
            CNT_WIDTH=1
        else:
            CNT_WIDTH=int(math.log2(WIDTH))
    
        #assert WIDTH>=0 ,'input must be at least one bit wide'        
        io=IO(
            in_i=Input(U.w(WIDTH)),
            cnt_o=Output(U.w(CNT_WIDTH)),
            empty_o=Output(U.w(1))
        )
        
        #self.io.in_i<<=in_i
        if(WIDTH==1):
            io.cnt_o[0]<<=~io.in_i[0]
            io.empty_o<<=~io.in_i[0]
        else:
            NUM_LEVELS=int(math.log2(WIDTH))
            index_lut=Wire(Vec(WIDTH,NUM_LEVELS))
            sel_nodes=Wire(U.w(2**NUM_LEVELS))
            index_nodes=Wire(Vec(2**NUM_LEVELS,NUM_LEVELS))
            in_tmp=Wire(U.w(WIDTH))

            for i in range(WIDTH):           
                in_tmp[i]=Mux(MODE, io.in_i[WIDTH-1-i],io.in_i[i])
            
            for j in range(WIDTH):
                index_lut[i]=U.w(NUM_LEVELS)(j)
            
            for level in range(NUM_LEVELS):
                if(level==NUM_LEVELS-1):
                    for k in range(2**level):
                        if(k*2<WIDTH-1):
                            sel_nodes[2**level-1+k]=in_tmp[k*2] | in_tmp[k*2+1]
                        #     if(in_tmp[k*2] ==U.w(1)(1)):
                        #         index_nodes[2**level-1+k]=index_lut[k*2]
                        #     else:
                        #         index_nodes[2**level-1+k]=index_lut[k*2+1]
                            index_nodes[2**level-1+k]=Mux((in_tmp[k*2] ==U.w(1)(1)),index_lut[k*2],index_lut[k*2+1])
                        elif(k*2==WIDTH-1):
                            sel_nodes[2**level-1+k]=in_tmp[k*2]
                            index_nodes[2**level-1+k]=index_lut[k*2]
                        else:
                            sel_nodes[2**level-1+k]=U.w(1)(0)
                            index_nodes[2**level-1+k]=U(0)
                else:
                    
                    for l in range(2**level):
                        sel_nodes[2**level-1+l]=sel_nodes[2**(level+1)-1+l*2] | sel_nodes[2**(level+1)-1+l*2+1]
                        index_nodes[2**level-1+l]=Mux(sel_nodes[2**(level+1)-1+l*2] == U.w(1)(1),index_nodes[2**(level+1)-1+l*2],index_nodes[2**(level+1)-1+l*2+1])
            if(NUM_LEVELS >0):
                io.cnt_o<<=index_nodes[0]
                io.empty_o<<=~sel_nodes[0]
            else:
                io.cnt_o<<=U.w(NUM_LEVELS)(0)
                io.empty_o<<=~OR(io.in_i,WIDTH)

            
            # io.cnt_o<<=Mux(NUM_LEVELS >0,index_nodes[0],U.w(NUM_LEVELS)(0))
            # io.empty_o<<=Mux(NUM_LEVELS >0,~sel_nodes[0],~OR(io.in_i,WIDTH))
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(lzc()),"lzc.fir"))
               


if __name__ == "__main__":
    LZC(2,False)
    
#***********黄铭绚 8.31 End***********#            

    
    