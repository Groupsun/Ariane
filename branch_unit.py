# **********  朱思成 8.31 Begin ********** #
from pyhcl import *

class Branch_unit(Module):
    io=IO(
        operator=Input(U.w(2)),
        branch_valid_i=Input(U.w(1)),
        branch_comp_res_i=Input(U.w(1)),
        branch_result_o= Output(U.w(64)(0))
        branch_exception_o.cause = Output(U.w(64)(0)),
        branch_exception_o.valid = Output(U.w(64)(0)),
        branch_exception_o.tval  = Output(U.w(64)(0)),
    )
    target_address=RegInit(U.w(64)(0))
    next_pc=RegInit(U.w(64)(0))
    jump_base=Mux(fu_data_i.operator == ariane_pkg::JALR,fu_data_i.operand_a[riscv::VLEN-1:0] : pc_i)
    resolve_branch_o=RegInit(U.w(1)(0))
    resolved_branch_o.target_address=RegInit(U.w(1)(0))
    resolved_branch_o.is_taken=RegInit(U.w(1)(0))
    resolved_branch_o.valid=RegInit(U.w(1)(0))
    resolved_branch_o.is_mispredict =RegInit(U.w(1)(0))
    resolved_branch_o.cf_type =RegInit(U.w(1)(0))
    resolved_branch_o.valid<<= branch_valid_i
    resolved_branch_o.cf_type<<= branch_predict_i.cf
    next_pc<<= pc_i + ((is_compressed_instr_i) ? {{riscv::VLEN-2{1'b0}}, 2'h2} : {{riscv::VLEN-3{1'b0}}, 3'h4})
    target_address<<=jump_base+fu_data_i.imm[riscv::VLEN-1:0])
    with when(u_data_i.operator == ariane_pkg::JALR):
        target_address[0]<<=U(0)
    branch_result_o<<=next_pc
    resolved_branch_o.pc<<=pc_i
    with when(branch_valid_i):
        resolved_branch_o.target_address<<=Mux(branch_comp_res_i, target_address,next_pc)
        resolved_branch_o.is_taken <<= branch_comp_res_i
        with when(ariane_pkg::is_branch(fu_data_i.operator) && branch_comp_res_i != (branch_predict_i.cf == ariane_pkg::Branch)):
            resolved_branch_o.is_mispredict<<=U(0)
            resolved_branch_o.cf_type <<= ariane_pkg::Branch
        with when(fu_data_i.operator == ariane_pkg::JALR&& (branch_predict_i.cf == ariane_pkg::NoCF || target_address != branch_predict_i.predict_address)):
            resolved_branch_o.is_mispredict<<=U(1)
            with when (branch_predict_i.cf != ariane_pkg::Return): resolved_branch_o.cf_type = ariane_pkg::JumpR
    branch_exception_o.cause = riscv::INSTR_ADDR_MISALIGNED
    branch_exception_o.valid = U(0)
    branch_exception_o.tval  = {{64-riscv::VLEN{pc_i[riscv::VLEN-1]}}, pc_i}

# 生成Verilog文件
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(Branch_unit()),"Branch_unit.fir"))
    
# **********  朱思成 8.31 End ********** #