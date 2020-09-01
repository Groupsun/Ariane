#************万云威 8.31 Begin************#
#  ???代表不会
from pyhcl import *
class scoreboard(Module):
    io=IO(
        clk_i=Input(U.w(1)),
        rst_ni=Input(U.w(1)),
        sb_full_o=Output(U.w(1)),
        flush_unissued_instr_i=Input(U.w(1)),
        flush_i=Input(U.w(1)),
        unresolved_branch_i=Input(U.w(1)),

          #list of clobbered registers to issue stage
        #rd_clobber_gpr_o=???
        #rd_clobber_fpr_o=???

          # regfile like interface to operand read stage
        #rs1_i=???
        rs1_o=Output(U.w(64)),
        rs1_valid_o=Output(U.w(1)),

        #rs2_i=???
        rs2_o=Output(U.w(64)),
        rs2_valid_o=Output(U.w(1)),

        #rs3_i=???
        #rs3_o=???
        rs3_valid_o=Output(U.w(1)),

          #advertise instruction to commit stage, if commit_ack_i is asserted advance the commit pointer
        #commit_instr_o=???
        #commit_ack_i=???

          # instruction to put on top of scoreboard e.g.: top pointer
          # we can always put this instruction to the top unless we signal with asserted full_o
        #decoded_instr_i=???
        decoded_instr_valid_i=Input(U.w(1)),
        decoded_instr_ack_o==Output(U.w(1)),

          # instruction to issue logic, if issue_instr_valid and issue_ready is asserted, advance the issue pointer
        #issue_instr_o=???
        issue_instr_valid_o=Output(U.w(1)),
        issue_ack_i=Input(U.w(1)),

          # write-back port
        #resolved_branch_i=???
        #trans_id_i=???  
        #wbdata_i=???
        #ex_i=???
        # wt_valid_i=???
        )
    
        # localparam int unsigned BITS_ENTRIES = $clog2(NR_ENTRIES);
        class packed {
            issued=U.w(1),
            is_rd_fpr_flag=U.w(1),
            #ariane_pkg::scoreboard_entry_t sbe;            
           } #mem_q [NR_ENTRIES-1:0], mem_n [NR_ENTRIES-1:0];

        issue_full=U.w(1),
        issue_en=U.w(1),
        #logic [BITS_ENTRIES-1:0] issue_cnt_n,      issue_cnt_q;
        #logic [BITS_ENTRIES-1:0] issue_pointer_n,  issue_pointer_q;
        #logic [NR_COMMIT_PORTS-1:0][BITS_ENTRIES-1:0] commit_pointer_n, commit_pointer_q;
        #logic [$clog2(NR_COMMIT_PORTS):0] num_commit;
        
          # the issue queue is full don't issue any new instructions
          #works since aligned to power of 2
          
        #assign issue_full = &issue_cnt_q;
        #assign sb_full_o = issue_full;


#************万云威 8.32 End************# 
