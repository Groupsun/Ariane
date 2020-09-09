#***********黄铭绚 8.31 Begin***********#

from pyhcl import *
import math

def popcountAdder(INPUT_WIDTH:int):
    class popcount(Module): 
        k=math.log2(INPUT_WIDTH)       
        POPCOUNT_WIDTH=int(k)+1
        io=IO(
            data_i=Input(U.w(INPUT_WIDTH)),
            popcount_o=Output(U.w(POPCOUNT_WIDTH))
        )
        PADDED_WIDTH=U(1)<<int(math.log2(INPUT_WIDTH))
        padded_input=Wire(U.w(PADDED_WIDTH))
        left_child_result=Wire(U.w(POPCOUNT_WIDTH-1))
        right_child_result=Wire(U.w(POPCOUNT_WIDTH-1))

        padded_input<<=U(0)
        padded_input[INPUT_WIDTH-1:0]<<=io.data_i

        with when(INPUT_WIDTH==1):
            left_child_result<<=U(0)
            right_child_result<<=padded_input[0]
        with elsewhen(INPUT_WIDTH==2):
            left_child_result<<=padded_input[1]
            right_child_result<<=padded_input[0]
        with otherwise():
            left_child=popcountAdder(PADDED_WIDTH / 2)
            right_child=popcountAdder(PADDED_WIDTH / 2)
        
        popcount_o<<=left_child_result + right_child_result
    
    return popcount()

#***********黄铭绚 8.31 End***********#            

     
                
