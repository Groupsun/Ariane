#************ÍòÔÆÍþ ÀîÕ×Ì© 8.31 Begin************#
from pyhcl import *
import math
class scoreboard(Module):
    NR_ENTRIES      = 8
    NR_WB_PORTS     = 1
    NR_COMMIT_PORTS = 2
    REG_ADDR_SIZE = 6
    NR_WB_PORTS = 4
    class fu_t(Enum):
        NONE=U(0)      # 0
        LOAD=U(1)      # 1
        STORE=U(2)     # 2
        ALU=U(3)       # 3
        CTRL_FLOW=U(4) # 4
        MULT=U(5)      # 5
        CSR=U(6)       # 6
        FPU=U(7)       # 7
        FPU_VEC=U(8)   # 8
        
    io=IO(
        clk_i=Input(U.w(1)),
        rst_ni=Input(U.w(1)),
        sb_full_o=Output(U.w(1)),
        flush_unissued_instr_i=Input(U.w(1)),
        flush_i=Input(U.w(1)),
        unresolved_branch_i=Input(U.w(1)),

          

        #rd_clobber_gpr_o=Output(U.w(64)),
        #rd_clobber_fpr_o=Output(U.w(64)),

          
        rs1_i=Input(U.w(REG_ADDR_SIZE))
        rs1_o=Output(U.w(64)),
        rs1_valid_o=Output(U.w(1)),

        rs2_i=Input(U.w(REG_ADDR_SIZE))
        rs2_o=Output(U.w(64)),
        rs2_valid_o=Output(U.w(1)),

        rs3_i=Input(U.w(REG_ADDR_SIZE))
        #rs3_o=Output(U.w())
        rs3_valid_o=Output(U.w(1)),

          #advertise instruction to commit stage, if commit_ack_i is asserted advance the commit pointer
        #commit_instr_o=???
        commit_ack_i=U.w(2),

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
        wt_valid_i=U.w(1)
        )
    
        BITS_ENTRIES = int(math.log(NR_ENTRIES,2))
        packed=Bundle(
            issued=U.w(1),
            is_rd_fpr_flag=U.w(1),
            #ariane_pkg::scoreboard_entry_t sbe;            
           )
        mem_q=[packed for x in range(0,NR_ENTRIES)]
        mem_n=[packed for x in range(0,NR_ENTRIES)]

        issue_full=U.w(1)
        issue_en=U.w(1)
        issue_cnt_n=U.w(BITS_ENTRIES)
        issue_cnt_q=U.w(BITS_ENTRIES)
        issue_pointer_n=U.w(BITS_ENTRIES)
        issue_pointer_q=U.w(BITS_ENTRIES)
        #logic [NR_COMMIT_PORTS-1:0][BITS_ENTRIES-1:0] commit_pointer_n, commit_pointer_q;
        num_commit=U.w(int(math.log(NR_COMMIT_PORTS,2)))
        
          
        assign issue_full = &issue_cnt_q
        assign sb_full_o = issue_full
        
        for i in range(NR_COMMIT_PORTS):
            commit_instr_o[i] = mem_q[commit_pointer_q[i]].sbe
            commit_instr_o[i].trans_id = commit_pointer_q[i]
        issue_instr_o<<= decoded_instr_i
        issue_instr_o.trans_id<= issue_pointer_q
        issue_instr_valid_o = decoded_instr_valid_i & ~unresolved_branch_i & ~issue_full
        decoded_instr_ack_o = issue_ack_i & ~issue_full

        mem_n<<= mem_q
        issue_en=U.w(0)
        with when (decoded_instr_valid_i & decoded_instr_ack_o & !flush_unissued_instr_i):
            mem_n[issue_pointer_q] = {U.w(1),                                     
                                #ariane_pkg::is_rd_fpr(decoded_instr_i.op), 
                                decoded_instr_i                           
                                }
        for i in range(NR_ENTRIES):
            with when (mem_q[i].sbe.fu == ariane_pkg::NONE & mem_q[i].issued)
                mem_n[i].sbe.valid = U.w(1)
                
        for i in range (NR_WB_PORTS):
            with when(wt_valid_i[i] & mem_q[trans_id_i[i]].issued):
                mem_n[trans_id_i[i]].sbe.valid  = U(1)
                mem_n[trans_id_i[i]].sbe.result = wbdata_i[i]
                mem_n[trans_id_i[i]].sbe.bp.predict_address = resolved_branch_i.target_address
                with when (ex_i[i].valid):
                    mem_n[trans_id_i[i]].sbe.ex = ex_i[i]
        
                with otherwise():
                    with when (#mem_q[trans_id_i[i]].sbe.fu inside {ariane_pkg::FPU, ariane_pkg::FPU_VEC}):
                        mem_n[trans_id_i[i]].sbe.ex.cause = ex_i[i].cause

        for i in range ( NR_COMMIT_PORTS):
            with when (commit_ack_i[i]):
                mem_n[commit_pointer_q[i]].issued     = U(0)
                mem_n[commit_pointer_q[i]].sbe.valid  = U(0)
      

        with when(flush_i):
            for i in range(NR_ENTRIES):
                mem_n[i].issued       = U(0)
                mem_n[i].sbe.valid    = U(0)
                mem_n[i].sbe.ex.valid = U(0)
        
        
        #// FIFO counter updates
        #popcount #(
        #.INPUT_WIDTH(NR_COMMIT_PORTS)
        #) i_popcount (
        #.data_i(commit_ack_i),
        #.popcount_o(num_commit)
        #);
        with when(flush_i):
            issue_cnt_n         = U(0)
            commit_pointer_n[0] = U(0) 
            issue_pointer_n     = U(0)
        with otherwise():
            issue_cnt_n         =   issue_cnt_q- num_commit + issue_en
            commit_pointer_n[0] =  commit_pointer_q[0] + num_commit
            issue_pointer_n     =  issue_pointer_q+ issue_en

        for k in range  (NR_COMMIT_PORTS): 
            with when(flush_i):
                commit_pointer_n[k] = U(0)
            with otherwise():
                commit_pointer_n[k] = commit_pointer_n[0] + U(k)              
        #gpr_clobber_vld=
        #fpr_clobber_vld=
        #clobber_fu=

    
        gpr_clobber_vld  = U(0)
        fpr_clobber_vld  = U(0)             


		#ariane_pkg::NONE=???  ariane_pkg::REG_ADDR_SIZE=???#
		clobber_fu[NR_ENTRIES]=ariane_pkg::NONE
		for i in range(0,pow(2,ariane_pkg::REG_ADDR_SIZE)):
			 gpr_clobber_vld[i][NR_ENTRIES] = U(1)
			 fpr_clobber_vld[i][NR_ENTRIES] = U(1)

		for i in range(0,NR_ENTRIES):
			gpr_clobber_vld[mem_q[i].sbe.rd][i] = mem_q[i].issued & ~mem_q[i].is_rd_fpr_flag
			fpr_clobber_vld[mem_q[i].sbe.rd][i] = mem_q[i].issued & mem_q[i].is_rd_fpr_flag
			clobber_fu[i]= mem_q[i].sbe.fu

		gpr_clobber_vld[0] = U(0)

		for k in range(0,pow(2,ariane_pkg::REG_ADDR_SIZE)):
			rr_arb_tree.NumIn = NR_ENTRIES+1
			rr_arb_tree.DataType = (ariane_pkg::fu_t
			rr_arb_tree.ExtPrio = U(1)
			rr_arb_tree.AxiVldRdy = U(1)
			i_sel_gpr_clobbers.clk_i = clk_i
			i_sel_gpr_clobbers.rst_ni = rst_ni
			i_sel_gpr_clobbers.flush_i = U(0)
			i_sel_gpr_clobbers.rr_i = U(0)
			i_sel_gpr_clobbers.req_i = gpr_clobber_vld[k]
			#i_sel_gpr_clobbers.gnt_o = ???
			i_sel_gpr_clobbers.data_i =  clobber_fu
			i_sel_gpr_clobbers.gnt_i = U(1)
			#i_sel_gpr_clobbers.req_o = ???
			i_sel_gpr_clobbers.data_o =  rd_clobber_gpr_o[k]
			#i_sel_gpr_clobbers.idx_o = ???

		 #rs1_fwd_req=???  rs2_fwd_req=???  rs3_fwd_req=??? rs_data=???
		 #rs1_valid=???, rs2_valid=???
		for k in range(0,NR_WB_PORTS):
			rs1_fwd_req[k] = (1 if mem_q[trans_id_i[k]].sbe.rd == rs1_i else 0) & wt_valid_i[k] & (~ex_i[k].valid) & (1 if mem_q[trans_id_i[k]].is_rd_fpr_flag == ariane_pkg::is_rs1_fpr(issue_instr_o.op) else 0)
			rs2_fwd_req[k] = (1 if mem_q[trans_id_i[k]].sbe.rd == rs2_i else 0) & wt_valid_i[k] & (~ex_i[k].valid) & (1 if mem_q[trans_id_i[k]].is_rd_fpr_flag == ariane_pkg::is_rs2_fpr(issue_instr_o.op) else 0)
			rs3_fwd_req[k] = (1 if mem_q[trans_id_i[k]].sbe.rd == rs3_i else 0) & wt_valid_i[k] & (~ex_i[k].valid) & (1 if mem_q[trans_id_i[k]].is_rd_fpr_flag == ariane_pkg::is_imm_fpr(issue_instr_o.op) else 0)
			rs_data[k] = wbdata_i[k]

		for k in range(0,NR_ENTRIES):
			rs1_fwd_req[k+NR_WB_PORTS] = (1 if mem_q[k].sbe.rd == rs1_i else 0) & mem_q[k].issued & mem_q[k].sbe.valid & (1 if mem_q[k].is_rd_fpr_flag == ariane_pkg::is_rs1_fpr(issue_instr_o.op) else 0)
			rs2_fwd_req[k+NR_WB_PORTS] = (1 if mem_q[k].sbe.rd == rs2_i else 0) & mem_q[k].issued & mem_q[k].sbe.valid & (1 if mem_q[k].is_rd_fpr_flag == ariane_pkg::is_rs2_fpr(issue_instr_o.op) else 0)
			rs3_fwd_req[k+NR_WB_PORTS] = (1 if mem_q[k].sbe.rd == rs3_i else 0) & mem_q[k].issued & mem_q[k].sbe.valid & (1 if mem_q[k].is_rd_fpr_flag == ariane_pkg::is_imm_fpr(issue_instr_o.op) else 0)
			rs_data[k+NR_WB_PORTS] = mem_q[k].sbe.result

		 rs1_valid_o = rs1_valid & ((|rs1_i) | ariane_pkg::is_rs1_fpr(issue_instr_o.op))
		 rs2_valid_o = rs2_valid & ((|rs2_i) | ariane_pkg::is_rs2_fpr(issue_instr_o.op))

		rr_arb_tree.NumIn = NR_ENTRIES+NR_WB_PORTS
		rr_arb_tree.DataWidth = 64
		rr_arb_tree.ExtPrio = U(1)
		rr_arb_tree.AxiVldRdy = U(1)
		i_sel_rs1.clk_i = clk_i
		i_sel_rs1.rst_ni = rst_ni
		i_sel_rs1.flush_i = U(0)
		i_sel_rs1.rr_i = U(0)
		i_sel_rs1.req_i = rs1_fwd_req
		#i_sel_rs1.gnt_o = ???
		i_sel_rs1.data_i = rs_data
		i_sel_rs1.gnt_i = U(1)
		i_sel_rs1.req_o = rs1_valid
		i_sel_rs1.data_o = rs1_o
		#i_sel_rs1.idx_o = ???

		rr_arb_tree.NumIn = NR_ENTRIES+NR_WB_PORTS
		rr_arb_tree.DataWidth = 64
		rr_arb_tree.ExtPrio = U(1)
		rr_arb_tree.AxiVldRdy = U(1)
		i_sel_rs2.clk_i = clk_i
		i_sel_rs2.rst_ni = rst_ni
		i_sel_rs2.flush_i = U(0)
		i_sel_rs2.rr_i = U(0)
		i_sel_rs2.req_i = rs2_fwd_req
		#i_sel_rs2.gnt_o = ???
		i_sel_rs2.data_i = rs_data
		i_sel_rs2.gnt_i = U(1)
		i_sel_rs2.req_o = rs2_valid
		i_sel_rs2.data_o = rs2_o
		#i_sel_rs2.idx_o = ???

		#rs3=???

		rr_arb_tree.NumIn = NR_ENTRIES+NR_WB_PORTS
		rr_arb_tree.DataWidth = 64
		rr_arb_tree.ExtPrio = U(1)
		rr_arb_tree.AxiVldRdy = U(1)
		i_sel_rs3.clk_i = clk_i
		i_sel_rs3.rst_ni = rst_ni
		i_sel_rs3.flush_i = U(0)
		i_sel_rs3.rr_i = U(0)
		i_sel_rs3.req_i = rs3_fwd_req
		#i_sel_rs3.gnt_o = ???
		i_sel_rs3.data_i = rs_data
		i_sel_rs3.gnt_i = U(1)
		i_sel_rs3.req_o = rs3_valid 
		i_sel_rs3.data_o = rs3_o   
		#i_sel_rs3.idx_o = ???

		 rs3_o = rs3[ariane_pkg::FLEN-1:0]

		if(posedge clk_i):
			if(!rst_ni):
				if(rd_clobber_gpr_o[0] == ariane_pkg::NONE):
					return 1
		else: 
			print(1,"RD 0 should not bet set")
		if(posedge clk_i):
			if(!rst_ni):
				if(commit_ack_i[0]):
					if(commit_instr_o[0].valid):
						return 1
		else:
			print(1,"Commit acknowledged but instruction is not valid")
		if(posedge clk_i):
			if(!rst_ni):
				if(commit_ack_i[1]):
					if(commit_instr_o[1].valid):
						return 1
		else:
			print(1,"Commit acknowledged but instruction is not valid")
		if(posedge clk_i):
			if(!rst_ni):
				if(issue_ack_i):
					if(issue_instr_valid_o):
						return 1
		else:
			print(1,"Issue acknowledged but instruction is not valid")

		for i in range(0,NR_WB_PORTS):
			for j in range(0,NR_WB_PORTS):
				if(posedge clk_i):
					if(!rst_ni):
						if(wt_valid_i[i] && wt_valid_i[j] && (i != j) ):
							if(trans_id_i[i] != trans_id_i[j]):
								return 1
				else:
					print(1,"Two or more functional units are retiring instructions with the same transaction id!")
#************ÍòÔÆÍþ ÀîÕ×Ì© 9.8 End************# 
