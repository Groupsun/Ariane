#************江熠玲 8.28 Begin************#
from pyhcl import *

class ptw(Module):
    io = IO(
        a=Input(U.w(1)),
        b=Input(U.w(1)),
        s=Output(U.w(1)),
        cout=Output(U.w(1))
        
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
        #不会output tlb_update_t             itlb_update_o,
        #不会output tlb_update_t             dtlb_update_o,

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
#************江熠玲 8.28 End************#