#********刘康杰 戴熠华 2020.9.3 Begin *******#
from pyhcl import *
from re_name import *
from scoreboard import *
from issue_read_operands import *

#parameter int unsigned NR_ENTRIES = 8,
#parameter int unsigned NR_WB_PORTS = 4,
#parameter int unsigned NR_COMMIT_PORTS = 2

def issue_stage(NR_ENTRIES:int,NR_WB_PORTS:int,NR_COMMIT_PORTS:int):
    class Issue_stage(Module):
        io = IO(
            clk_i=Input(U.w(1)),
            rst_ni=Input(U.w(1)),#时钟信号要定义吗？

            sb_full_o=Output(U.w(1)),            
            flush_unissued_instr_i=Input(U.w(1)),
            flush_i=Input(U.w(1)),
            
            decoded_instr_i= Input(scoreboard_entry_t()),#####
            
            decoded_instr_valid_i=Input(U.w(1)),
            is_ctrl_flow_i=Input(U.w(1)),
            decoded_instr_ack_o=Output(U.w(1)),
            
            fu_data_o=Output(fu_data_t()),#####
            pc_o=Output(U.w(64)),
            is_compressed_instr_o=Output(U.w(1)),
            flu_ready_i=Input(U.w(1)),
            alu_valid_o=Output(U.w(1)),

            
            #ex just resolved our predicted branch, we are ready to accept new requests
            resolve_branch_i=Input(U.w(1)),
            
            lsu_ready_i=Input(U.w(1)),
            lsu_valid_o=Output(U.w(1)),

            
            branch_valid_o=Output(U.w(1)),
            
            branch_predict_o=Input(branchpredict_sbe_t()),#####

            mult_valid_o=Output(U.w(1)),
            
            fpu_ready_i=Input(U.w(1)),
            fpu_valid_o=Output(U.w(1)),
            fpu_fmt_o=Output(U.w(2)),
            fpu_rm_o=Output(U.w(3)),

            
            csr_valid_o=Output(U.w(1)),
            
            trans_id_i=Input(Vec(NR_WB_PORTS,U.w(3))),
            
            resolved_branch_i=Input(bp_resolve_t),#####
            wbdata_i=Input(Vec(NR_WB_PORTS,U.w(64))),
            ex_ex_i=Input(Vec(NR_WB_PORTS,exception_t())),#####
            wt_valid_i=Input(U.w(NR_WB_PORTS)),

            waddr_i=Input(Vec(NR_COMMIT_PORTS,U.w(5))),
            wdata_i=Input(Vec(NR_COMMIT_PORTS,U.w(64))),
            we_gpr_i=Input(U.w(NR_COMMIT_PORTS)),
            we_fpr_i=Input(U.w(NR_COMMIT_PORTS)),

            commit_instr_o=Output(Vec(NR_COMMIT_PORTS,scoreboard_entry_t())),#####
            commit_ack_i=Input(U.w(NR_COMMIT_PORTS))


        )
        
        rd_clobber_gpr_sb_iro=Reg(Vec(64,U.w(4)))
        rd_clobber_fpr_sb_iro=Reg(Vec(64,U.w(4)))
        rs1_iro_sb=Reg(U.w(6))
        rs1_valid_sb_iro=Reg(U.w(1))


        rs2_iro_sb=Reg(U.w(6))
        rs2_sb_iro=Reg(U.w(64))
        rs2_valid_iro_sb=Reg(U.w(1))


        rs3_iro_sb=Reg(U.w(6))
        #logic [FLEN-1:0]           rs3_sb_iro;
        rs3_valid_iro_sb=Reg(U.w(1))

        issue_instr_rename_sb=Wire(scoreboard_entry_t())#####
        issue_instr_valid_rename_sb=Reg(U.w(1))
        issue_ack_sb_rename=Reg(U.w(1))



        issue_instr_sb_iro=Wire(scoreboard_entry_t())#####
        issue_instr_valid_sb_iro=Reg(U.w(1))
        issue_ack_iro_sb=Reg(U.w(1))


        i_re_name=re_name()
        i_re_name.io.clk_i<<=io.clk_i
        i_re_name.io.rst_ni<<=io.rst_ni
        i_re_name.io.flush_i<<=io.flush_i
        i_re_name.io.flush_unissied_instr_i<<=io.flush_unissued_instr_i
        i_re_name.io.issue_instr_i <<=io.decoded_instr_i 
        i_re_name.io.issue_instr_valid_i<<=io.decoded_instr_valid_i
        io.decoded_instr_ack_o<<=i_re_name.io.issue_ack_o
        issue_instr_rename_sb<<=i_re_name.io.issue_instr_o
        issue_instr_valid_rename_sb<<=i_re_name.io.issue_instr_valid_o
        i_re_name.io.issue_ack_i <<=issue_ack_sb_rename


        i_scoreboard=scoreboard(NR_ENTRIES,NR_WB_PORTS,NR_COMMIT_PORTS)
        io.sb_full_o<<=i_scoreboard.io.sb_full_o
        i_scoreboard.io.unresolved_branch_i<<=U(0)
        rd_clobber_gpr_sb_iro<<=i_scoreboard.io.rd_clobber_gpr_o
        rd_clobber_fpr_sb_iro<<=i_scoreboard.io.rd_clobber_fpr_o 
        i_scoreboard.io.rs1_i<<=rs1_iro_sb
        rs1_sb_iro<<=i_scoreboard.io.rs1_o
        rs1_valid_sb_iro <<=i_scoreboard.io.rs1_valid_o
        i_scoreboard.io.rs2_i<<=rs2_iro_sb
        rs2_sb_iro<<=i_scoreboard.io.rs2_o
        rs2_valid_iro_sb<<=i_scoreboard.io.rs2_valid_o 
        i_scoreboard.io.rs3_i<<=rs3_iro_sb
        rs3_sb_iro<<=i_scoreboard.io.rs3_o
        rs3_valid_iro_sb<<=i_scoreboard.io.rs3_valid_o
        
        i_scoreboard.io.decoded_instr_i<<=issue_instr_rename_sb
        i_scoreboard.io.decoded_instr_valid_i<<=issue_instr_valid_rename_sb
        issue_ack_sb_rename<<= i_scoreboard.io.decoded_instr_ack_o
        issue_instr_sb_iro<<= i_scoreboard.io.issue_instr_o
        issue_instr_valid_sb_iro<<=i_scoreboard.io.issue_instr_valid_o 
        i_scoreboard.io.issue_ack_i<<=issue_ack_iro_sb

        i_scoreboard.io.resolved_branch_i<<=io.resolved_branch_i
        i_scoreboard.io.trans_id_i<<=io.trans_id_i
        i_scoreboard.io.wbdata_i<<=io.wbdata_i
        i_scoreboard.io.ex_i<<=io.ex_ex_i
        
        

        i_issue_read_operands=issue_read_operands(NR_COMMIT_PORTS)
        i_issue_read_operands.io.flush_i<<=io.flush_unissued_instr_i
        i_issue_read_operands.io.issue_instr_i<<=io.issue_instr_sb_iro
        i_issue_read_operands.io.issue_instr_valid_i<<=issue_instr_valid_sb_iro

        issue_ack_iro_sb<<=i_issue_read_operands.io.issue_ack_o
        io.fu_data_o<<=i_issue_read_operands.io.fu_data_o
        i_issue_read_operands.io.flu_ready_i<<=io.flu_ready_i
        rs1_o<<=i_issue_read_operands.io.rs1_o
        i_issue_read_operands.io.rs1_i<<=io.rs1_sb_iro
        i_issue_read_operands.io.rs1_valid_i<<=io.rs1_valid_sb_iro
        rs2_iro_sb<<=i_issue_read_operands.io.rs2_o
        i_issue_read_operands.io.rs2_i<<=rs2_sb_iro
        i_issue_read_operands.io.rs2_valid_i<<= rs2_valid_iro_sb        
        rs3_iro_sb<<=i_issue_read_operands.io.rs3_o
        i_issue_read_operands.io.rs3_i<<=io.rs3_sb_iro
        i_issue_read_operands.io.rs3_valid_i<<=rs3_valid_iro_sb
        i_issue_read_operands.io.rd_clobber_gpr_i<<=rd_clobber_gpr_sb_iro
        i_issue_read_operands.io.rd_clobber_fpr_i<<=io.rd_clobber_fpr_sb_iro
        alu_valid_o<<=i_issue_read_operands.io.alu_valid_o
        branch_valid_o<<=i_issue_read_operands.io.branch_valid_o
        csr_valid_o<<=i_issue_read_operands.io.csr_valid_o
        mult_valid_o<<=i_issue_read_operands.io.mult_valid_o
    return  Issue_stage()  



#******** 刘康杰 戴熠华  2020.9.3 End *******#


if __name__== '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(issue_stage(8,4,2)), "issue_stage.fir"))
