#***********黄铭绚 8.31 Begin***********#
from pyhcl import *
import math

class popcount(Module):
    def __init__(self,i_width):
        self.INPUT_WIDTH=256
        self.POPCOUNT_WIDTH=math.log2(self.INPUT_WIDTH)+1

        self.io=IO(
            data_i=Input(U.w(self.INPUT_WIDTH)),
            popcount_o=Output(U.w(self.POPCOUNT_WIDTH))
        )
        PADDED_WIDTH=1<<math.log2(self.INPUT_WIDTH)
        padded_input=Wire(U.w(PADDED_WIDTH))
        left_child_result=Wire(U.w(self.POPCOUNT_WIDTH-1))
        right_child_result=Wire(U.w(self.POPCOUNT_WIDTH-1))

        padded_input<<=U(0)
        padded_input[self.INPUT_WIDTH-1:0]<<=self.io.data_i

        if(self.INPUT_WIDTH==1):
            left_child_result<<=U(0)
            right_child_result<<=padded_input[0]
        elif(self.INPUT_WIDTH==2):
            left_child_result<<=padded_input[1]
            right_child_result<<=padded_input[0]
        else:
            left_child=popcount(PADDED_WIDTH / 2)
#***********黄铭绚 8.31 End***********#            
