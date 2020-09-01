# **********  钟子阳 8.31 Begin ********** #
from pyhcl import *

class Adder(Module):
    io = IO(
        adder_operator=Input(U.w(3))/*有加减法等8种算法，定义000为加法，
        001为减法，010为等于，011为不等于，100为大于，101为小于，110为大于等于，
        111为小于等于*/
        alu_branch_res_o=Output(Bool),
        less=Input(Bool),
        less_o=Output(Bool),
        adder_operand_a = Input(U.w(64)),
        adder_operand_b=Input(U.w(64)),
        adder_result=Output(U.w(64)),
    )
    adder_z_flag=RegInit(U.w(1)(0))
    adder_in_a=RegInit(U.w(65)(0))
    adder_in_b=RegInit(U.w(65)(0))
    counter = RegInit(U.w(2)(0))
    counter<<=io.adder_operator
    with when(counter>U(0)):
        adder_z_flag<<=U(1);
    adder_in_a<<=CatBits(io.adder_operand_a,U(1))
    with when(adder_z_flag==U(0)):
        adder_in_b<<=CatBits(io.adder_operand_b,U(0))^U(0)
    with otherwise():
        adder_in_b<<=CatBits(io.adder_operand_b,U(0))^U(0xffffffffffffffff)
    io.adder_result=(adder_in_a+adder_in_b)/2
    adder_z_flag<<=io.adder_result[0]
    for i in range(63):
        adder_z_flag<<=~(io.adder_result[63-i]|adder_a_flag)
    io.alu_branch_res_o<<=LookUpTable(counter,{
        U(0):U(1),
        U(1):U(1),
        U(2):adder_z_flag,
        U(3):~adder_a_flag,
        U(4):io.less,
        U(5):io.less,
        U(6):~io.less,
        U(7):~io.less,
        ...:U(0)
        })

class Shifts(Module):
    io=IO(
        shift_operator=Input(U.w(2)),/* 00是SLL，01是SLLW，10是SRA，11是SRAW*/
        shift_amt=Input(U.w(64)),
        shift_op_a=Input(U.w(64)),
        shift_result=Output(U.w(64))
    )
    shift_op_a=RegInit(U.w(64)(0))
    shift_left=RegInit(Bool(True))
    shift_arithmetic=RegInit(Bool(True))
    shift_amount=RegInit(U.w(6)(0))
    shift_right_result=RegInit(U.w(65)(0))
    shift_left_result=RegInit(U.w(64)(0))
    shift_left<<=io.operator==U(0)|io.operator==U(1)
    shift_arithmetic<<=io.operator==U(2)|io.operator==U(3)
    shift_op_a<<=CatBits(shift_arithmetic&io.operator[63],io.operator)
    shift_amount<<=CatBits(io.shift_amt[58],io.shift_amt[59],io.shift_amt[60],
                           io.shift_amt[61],io.shift_amt[62],io.shift_amt[63])
    shift_right_result<<=shift_op_a>>>shift_amount
    with when(shift_left):
        for i in range(64):
            shift_left_result[i]=shift_right_result[63-i]
    io.shift_result<<=Mux(shift_left,shift_left_result,shift_right_result)

class Comparisons(Module):
    io=IO(
        operand_a=Input(U.w(64)),
        operand_b=Input(U.w(64)),
        operator=Input(U.w(2)),/*01代表SLTS，10代表LTS，11代表GES*/
        less=Output(Bool)
    )
    op_a=RegInit(U.w(65)(0))
    op_b=RegInit(U.w(65)(0))
    sgn=RegInit(U.w(1)(0))
    op_a<<=CatBits(sgn&io.operand_a[0])
    op_b<<=CatBits(sgn&io.operand_b[0])
    with when(op_a>op_b):
        less=false
    otherwise():
        less=true

    
class alu(Module):
    


# 生成Verilog文件
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(HalfAdder()),"HalfAdder.fir"))
    
# **********  钟子阳 8.31 End ********** #