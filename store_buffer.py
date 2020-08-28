from pyhcl import *
import math


DEPTH_SPEC=100
DEPTH_COMMIT=100
## ********** 刘敏琪 8.28 Begin ********** ##

class store_buffer(Module):
    io = IO(
        clk_i=Input(U.w(1)),
        rst_ni=Input(U.w(1)),
        flush_i=Input(U.w(1)),
        no_st_pending_o=Input(U.w(1)),
        store_buffer_empty_o=Input(U.w(1)),
        page_offset_i=Input(U.w(12)),
        page_offset_matches_o=Input(U.w(1)),
        commit_i=Input(U.w(1)),
        commit_ready_o=Output(U.w(1)),
        ready_o=Output(U.w(1)),
        valid_i=Input(U.w(1)),
        valid_without_flush_i=Input(U.w(1)),
       # paddr_i=Input(),
        data_i=Input(U.w(64)),
        be_i=Input(U.w(8)),
        data_size_i=Input(U.w(2))
       # req_port_i=Input(),
      #  req_port_o=Output()
    )
    #todo!!!
    packed=Bundle(
       # address=U.w(),
        data=U.w(64),
        be=U.w(8),
        data_size=U.w(2),
        valid=U.w(1)
    )
    speculative_queue_n=[packed for x in range(0,DEPTH_SPEC)]
    speculative_queue_q=[packed for x in range(0,DEPTH_SPEC)]
    commit_queue_n=[packed for x in range(0,DEPTH_COMMIT)]
    commit_queue_q=[packed for x in range(0,DEPTH_COMMIT)]
    speculative_status_cnt_n=U.w(math.log2(DEPTH_SPEC))
    commit_status_cnt_n=U.w(math.log2(DEPTH_COMMIT))
    commit_status_cnt_q = U.w(math.log2(DEPTH_COMMIT))
    speculative_read_pointer_n=U.w(math.log2(DEPTH_SPEC))
    speculative_read_pointer_q= U.w(math.log2(DEPTH_SPEC))
    speculative_write_pointer_n=U.w(math.log2(DEPTH_SPEC))
    speculative_write_pointer_q = U.w(math.log2(DEPTH_SPEC))
    commit_read_pointer_n=U.w(math.log2(DEPTH_COMMIT))
    commit_read_pointer_q=U.w(math.log2(DEPTH_COMMIT))
    commit_write_pointer_n = U.w(math.log2(DEPTH_COMMIT))
    commit_write_pointer_q = U.w(math.log2(DEPTH_COMMIT))
## ********** 刘敏琪 8.28 End ********** ##






