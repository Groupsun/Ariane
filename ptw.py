
from pyhcl import *
#************江熠玲 8.29 Begin************# 
class pte_t:
    reserved=Vec(10, U.w(1))
    ppn=Vec(56 - 12, U.w(1))
    rsw=Vec(2, U.w(1))
    d=U.w(1)
    a=U.w(1)
    g=U.w(1)
    u=U.w(1)
    x=U.w(1)
    w=U.w(1)
    r=U.w(1)
    v=U.w(1)
    
class tlb_update_t:
    valid=Reg(U.w(1))
    is_2M=U.w(1)
    is_1G=U.w(1)
    vpn=Vec(27,U.w(1))
    asid=Vec(1,U.w(1))
    content=pte_t  

#************江熠玲 8.29 End************# 

#************江熠玲 8.28,29 Begin************#       
class ptw(Module):
    io = IO(        
        flush_i=Input(U.w(1)),                # flush everything, we need to do this because
                                                            # actually everything we do is speculative at this stage
                                                           # e.g.: there could be a CSR instruction that changes everything
        ptw_active_o=Output(U.w(1)),
        walking_instr_o=Output(U.w(1)),        # set when walking for TLB
        ptw_error_o=Output(U.w(1)),            # set when an error occurred
        enable_translation_i=Input(U.w(1)),   # CSRs indicate to enable SV39
        en_ld_st_translation_i=Input(U.w(1)), # enable virtual memory translation for load/stores

        lsu_is_store_i=Input(U.w(1)),         # this translation was triggered by a store
        # PTW memory interface
        #input  dcache_req_o_t           req_port_i,
        req_port_i=Input(U.w(1)),
        #不会output dcache_req_i_t           req_port_o,


        # to TLBs, update logic
        itlb_update_o=Input(tlb_update_t)
        dtlb_update_o=Onput(tlb_update_t)

        #不会output logic [riscv::VLEN-1:0]  update_vaddr_o,

        #不会input  logic [ASID_WIDTH-1:0]   asid_i,
        # from TLBs
        # did we miss?
        itlb_access_i=Input(U.w(1)),
        itlb_hit_i=Input(U.w(1)),
        #不会input  logic [riscv::VLEN-1:0]  itlb_vaddr_i,

        dtlb_access_i=Input(U.w(1)),
        dtlb_hit_i=Input(U.w(1)),
        #不会input  logic [riscv::VLEN-1:0]  dtlb_vaddr_i,
        # from CSR file
        satp_ppn_i=Input(U.w(44)), # ppn from satp
        mxr_i=Input(U.w(1)),
        # Performance counters
        itlb_miss_o=Output(U.w(1)),
        dtlb_miss_o=Output(U.w(1))
    )
#************江熠玲 8.28,29 End************#


#************江熠玲 8.31 Begin************# 
    data_rvalid_q = Wire(Bool)
    
    data_rdata_q = Reg(Vec(64, U.w(1)))
    
    #riscv::pte_t pte;
    #assign pte = riscv::pte_t'(data_rdata_q);

    enum logic[2:0] {
      IDLE,
      WAIT_GRANT,
      PTE_LOOKUP,
      WAIT_RVALID,
      PROPAGATE_ERROR
    } state_q, state_d;


    enum logic [1:0] {
        LVL1, LVL2, LVL3
    } ptw_lvl_q, ptw_lvl_n;


    is_instr_ptw_q = Wire(Bool)
    is_instr_ptw_n = Wire(Bool)
    global_mapping_q = Wire(Bool)
    global_mapping_n = Wire(Bool)
    tag_valid_n = Wire(Bool)
    tag_valid_q = Wire(Bool)


    tlb_update_asid_q = Reg(Vec(1, U.w(1)))
    tlb_update_asid_n = Reg(Vec(1, U.w(1)))
    
    #logic [riscv::VLEN-1:0] vaddr_q,   vaddr_n;
 
    ptw_pptr_q = Reg(Vec(56, U.w(1)))
    ptw_pptr_n = Reg(Vec(56, U.w(1)))
    
 
    io.update_vaddr_o  <<= vaddr_q

    io.ptw_active_o    <<= (state_q != IDLE)
    io.walking_instr_o <<= is_instr_ptw_q

    io.req_port_o.address_index <<= ptw_pptr_q[DCACHE_INDEX_WIDTH-1:0]
    io.req_port_o.address_tag   <<= ptw_pptr_q[DCACHE_INDEX_WIDTH+DCACHE_TAG_WIDTH-1:DCACHE_INDEX_WIDTH];

    io.req_port_o.kill_req      <<=Reg(U.w(0))

    io.req_port_o.data_wdata    <<=Reg(U.w(0))

    io.itlb_update_o.vpn <<= vaddr_q[38:12
    dtlb_update_o.vpn <<= vaddr_q[38:12]

    io.itlb_update_o.is_2M <<= (ptw_lvl_q == LVL2)
    io.itlb_update_o.is_1G <<= (ptw_lvl_q == LVL1)
    io.dtlb_update_o.is_2M <<= (ptw_lvl_q == LVL2)
    io.dtlb_update_o.is_1G <<= (ptw_lvl_q == LVL1)

    io.itlb_update_o.asid <<= tlb_update_asid_q
    io.dtlb_update_o.asid <<= tlb_update_asid_q

    io.itlb_update_o.content <<= pte | (global_mapping_q << 5)
    io.dtlb_update_o.content <<= pte | (global_mapping_q << 5)

    io.req_port_o.tag_valid <<= tag_valid_q
    
    

#************江熠玲 8.29 End************# 

    #always_comb begin : ptw

    tag_valid_n           <<= Reg(U.w(1)(0))
    req_port_o.data_req   <<= Reg(U.w(1)(0))
    req_port_o.data_be    <<= Reg(U.w(8)(255))
    req_port_o.data_size  <<= Reg(U.w(2)(3))
    req_port_o.data_we    <<= Reg(U.w(1)(0))
    ptw_error_o           <<= Reg(U.w(1)(0))
    itlb_update_o.valid   <<= Reg(U.w(1)(0))
    dtlb_update_o.valid   <<= Reg(U.w(1)(0))
    is_instr_ptw_n        <<= is_instr_ptw_q
    ptw_lvl_n             <<= ptw_lvl_q
    ptw_pptr_n            <<= ptw_pptr_q
    state_d               <<= state_q
    global_mapping_n      <<= global_mapping_q

    tlb_update_asid_n     <<= tlb_update_asid_q
    vaddr_n               <<= vaddr_q

    itlb_miss_o           <<= Reg(U.w(1)(0))
    dtlb_miss_o           <<= Reg(U.w(1)(0))
        

#************江熠玲 8.31 Begin************# 

    with when(state_q==IDLE):
        ptw_lvl_n        <<= LVL1
        global_mapping_n <<= Reg(U.w(1)(0))
        is_instr_ptw_n   <<= Reg(U.w(1)(0))
        with when(enable_translation_i & itlb_access_i & ~itlb_hit_i & ~dtlb_access_i):
            #ptw_pptr_n          = {satp_ppn_i, itlb_vaddr_i[38:30], 3'b0};
            is_instr_ptw_n      <<= Reg(U.w(1)(1))
            tlb_update_asid_n   <<= asid_i
            vaddr_n             <<= itlb_vaddr_i
            state_d             <<= WAIT_GRANT
            itlb_miss_o         <<= Reg(U.w(1)(1))
            
        #else if (en_ld_st_translation_i & dtlb_access_i & ~dtlb_hit_i) begin
              #ptw_pptr_n          = {satp_ppn_i, dtlb_vaddr_i[38:30], 3'b0};
                    #tlb_update_asid_n   = asid_i;
                    #vaddr_n             = dtlb_vaddr_i;
                    #state_d             = WAIT_GRANT;
                    #dtlb_miss_o         = 1'b1;
                #end
            #end
    with when(state_q==WAIT_GRANT):
        req_port_o.data_req <<=Reg(U.w(1)(1))
        with when(req_port_i.data_gnt):  
            tag_valid_n <<= Reg(U.w(1)(1))
            state_d     <<= PTE_LOOKUP
#################
#预留
################


    with when(flush_i):
        with when((state_q == PTE_LOOKUP && !data_rvalid_q) || ((state_q == WAIT_GRANT) && req_port_i.data_gnt)):
            state_d <<= WAIT_RVALID
        with otherwise():
            state_d <<= IDLE
    with when(~rst_ni):
        state_q            <= IDLE
        is_instr_ptw_q     <= Reg(U.w(1)(0))
        ptw_lvl_q          <= LVL1
        tag_valid_q        <= Reg(U.w(1)(0))
        tlb_update_asid_q  <= Reg(U(0))
        vaddr_q            <= Reg(U(0))
        ptw_pptr_q         <= Reg(U(0))
        global_mapping_q   <= Reg(U.w(1)(0))
        data_rdata_q       <= Reg(U(0))
        data_rvalid_q      <= Reg(U.w(1)(0))
    with otherwise():
        state_q            <= state_d;
        ptw_pptr_q         <= ptw_pptr_n;
        is_instr_ptw_q     <= is_instr_ptw_n;
        ptw_lvl_q          <= ptw_lvl_n;
        tag_valid_q        <= tag_valid_n;
        tlb_update_asid_q  <= tlb_update_asid_n;
        vaddr_q            <= vaddr_n;
        global_mapping_q   <= global_mapping_n;
        data_rdata_q       <= req_port_i.data_rdata;
        data_rvalid_q      <= req_port_i.data_rvalid;
#************江熠玲 8.31 End************# 