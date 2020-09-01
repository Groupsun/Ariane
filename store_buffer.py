from pyhcl import *
import math

##todo
CONFIG_L1I_CACHELINE_WIDTH=U(128)
CONFIG_L1I_ASSOCIATIVITY=U(4)
CONFIG_L1I_SIZE=U(16*1024)
CONFIG_L1D_CACHELINE_WIDTH=U(128)
CONFIG_L1D_ASSOCIATIVITY=U(8)
CONFIG_L1D_SIZE=U(32*1024)
DCACHE_SET_ASSOC=CONFIG_L1D_ASSOCIATIVITY
##log2
DCACHE_INDEX_WIDTH=U(100)
DCACHE_TAG_WIDTH=U(100)

dcache_req_i_t=Bundle(
    address_index=U.w(DCACHE_INDEX_WIDTH),
    address_tag=U.w(DCACHE_TAG_WIDTH),
    data_wdata=U.w(64),
    data_req=U.w(1),
    data_we=U.w(1),
    data_be=U.w(8),
    data_size=U.w(2),
    kill_req=U.w(1),
    tag_valid=U.w(1),
)
dcache_req_o_t=Bundle(
    data_gnt=U.w(1),
    data_rvalid=U.w(1),
    data_rdata=U.w(64)
    )
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
        ##riscv::PLEN
        paddr_i=Input(U.w(100)),
        data_i=Input(U.w(64)),
        be_i=Input(U.w(8)),
        data_size_i=Input(U.w(2)),
        req_port_i=Input(dcache_req_o_t),
        req_port_o=Output(dcache_req_i_t)
    )
    #todo!!!
    class type1:
        address = Reg(Vec(DEPTH_SPEC, U.w(10)))
        data = Reg(Vec(DEPTH_SPEC, U.w(64)))
        be = Reg(Vec(DEPTH_SPEC, U.w(8)))
        data_size = Reg(Vec(DEPTH_SPEC, U.w(2)))
        valid = Reg(Vec(DEPTH_SPEC, U.w(1)))
    class type2:
        address = Reg(Vec(DEPTH_COMMIT, U.w(10)))
        data = Reg(Vec(DEPTH_COMMIT, U.w(64)))
        be = Reg(Vec(DEPTH_COMMIT, U.w(8)))
        data_size = Reg(Vec(DEPTH_COMMIT, U.w(2)))
        valid = Reg(Vec(DEPTH_COMMIT, U.w(1)))
    speculative_queue_n=type1()
    speculative_queue_q=type1()
    commit_queue_n=type2()
    commit_queue_q=type2()
    speculative_status_cnt_n=Reg(U.w(math.log2(DEPTH_SPEC)))
    speculative_status_cnt_q =Reg( U.w(math.log2(DEPTH_SPEC)))
    commit_status_cnt_n=Reg(U.w(math.log2(DEPTH_COMMIT)))
    commit_status_cnt_q =Reg( U.w(math.log2(DEPTH_COMMIT)))
    speculative_read_pointer_n=Reg(U.w(math.log2(DEPTH_SPEC)))
    speculative_read_pointer_q=Reg(U.w(math.log2(DEPTH_SPEC)))
    speculative_write_pointer_n=Reg(U.w(math.log2(DEPTH_SPEC)))
    speculative_write_pointer_q = Reg(U.w(math.log2(DEPTH_SPEC)))
    commit_read_pointer_n=Reg(U.w(math.log2(DEPTH_COMMIT)))
    commit_read_pointer_q=Reg(U.w(math.log2(DEPTH_COMMIT)))
    commit_write_pointer_n = Reg(U.w(math.log2(DEPTH_COMMIT)))
    commit_write_pointer_q = Reg(U.w(math.log2(DEPTH_COMMIT)))
## ********** 刘敏琪 8.28 End ********** ##

## ********** 刘敏琪 8.29 Begin ********** ##
    with when(speculative_status_cnt_q==0):
        io.store_buffer_empty_o <<= U(1)&io.no_st_pending_o
    with otherwise():
        io.store_buffer_empty_o <<= U(0)&io.no_st_pending_o
    speculative_status_cnt=U.w(DEPTH_SPEC)
    speculative_status_cnt=speculative_status_cnt_q
    io.ready_o <<= (speculative_status_cnt_q<U(DEPTH_SPEC-1)) or io.commit_i
    speculative_status_cnt_n=speculative_status_cnt_q
    speculative_read_pointer_n=speculative_read_pointer_q
    speculative_write_pointer_n=speculative_read_pointer_q
    speculative_queue_n=speculative_queue_q
    with when(io.valid_i==U(1)):
        #speculative_queue_n[speculative_write_pointer_q].address=paddr_i
        print(speculative_write_pointer_q)
        speculative_queue_n.data[speculative_write_pointer_q] <<=io.data_i
        speculative_queue_n.be[speculative_write_pointer_q] <<= io.be_i
        speculative_queue_n.data_size[speculative_write_pointer_q] <<= io.data_size_i;
        speculative_queue_n.valid[speculative_write_pointer_q] <<= U(1)
        speculative_write_pointer_n <<= speculative_write_pointer_q + U(1)
        speculative_status_cnt<<=speculative_status_cnt+ U(1)
    with when(io.commit_i==U(1)):
        speculative_queue_n.valid[speculative_read_pointer_q]<<=U(0)
        speculative_read_pointer_n <<= speculative_read_pointer_q + U(1)
        speculative_status_cnt <<=speculative_status_cnt-U(1)
    with when(io.flush_i==U(1)):
        for i in range(DEPTH_SPEC):
            speculative_queue_n.valid[i]<<=U(0)
        speculative_write_pointer_n <<=speculative_read_pointer_q
        speculative_status_cnt_n <<=U(0)
## ********** 刘敏琪 8.29 End ********** #


## ********** 刘敏琪 8.30 Begin ********** ##
    io.req_port_o.kill_req<<=U(0)
    io.req_port_o.data_we<<=U(1)
    io.req_port_o.tag_valid<<=U(0)
    io.req_port_o.address_index <<= commit_queue_q.address[commit_read_pointer_q][DCACHE_INDEX_WIDTH-U(1):0]
    io.req_port_o.address_tag   <<= commit_queue_q.address[commit_read_pointer_q][DCACHE_TAG_WIDTH+
                                                                                DCACHE_INDEX_WIDTH-1 :
                                                                               DCACHE_INDEX_WIDTH]
    io.req_port_o.data_wdata <<= commit_queue_q.data[commit_read_pointer_q]
    io.req_port_o.data_be    <<= commit_queue_q.be[commit_read_pointer_q]
    io.req_port_o.data_size  <<= commit_queue_q.data_size[commit_read_pointer_q]
    commit_status_cnt=U.w(DEPTH_COMMIT+1)
    commit_status_cnt=commit_status_cnt_q
    io.commit_ready_o <<=(commit_status_cnt_q<DEPTH_COMMIT)
    io.no_st_pending_o <<=(commit_status_cnt_q==U(0))
    commit_read_pointer_n <<=commit_read_pointer_q
    commit_write_pointer_n <<=commit_read_pointer_q
    commit_queue_n =commit_queue_q
    io.req_port_o.data_req <<= U(0)
    with when(commit_queue_q.valid[commit_read_pointer_q]!=U(0)):
        io.req_port_o.data_req <<= U(1)
        with when(io.req_port_i.data_gnt):
            commit_queue_n.valid[commit_read_pointer_q] <<=U(0)
            commit_read_pointer_n <<=commit_read_pointer_q+U(1)
            commit_status_cnt <<= commit_status_cnt + U(1)
    with when(io.commit_i):
        commit_queue_n.valid[commit_write_pointer_q] <<= speculative_queue_q.valid[speculative_read_pointer_q]
        commit_queue_n.data_size[commit_write_pointer_q] <<= speculative_queue_q.data_size[speculative_read_pointer_q]
        commit_queue_n.data[commit_write_pointer_q] <<= speculative_queue_q.data[speculative_read_pointer_q]
        commit_queue_n.be[commit_write_pointer_q] <<= speculative_queue_q.be[speculative_read_pointer_q]
        commit_queue_n.address[commit_write_pointer_q] <<= speculative_queue_q.address[speculative_read_pointer_q]
        commit_write_pointer_n <<= commit_write_pointer_n + U(1)
        commit_status_cnt <<= commit_status_cnt+ U(1)
    commit_status_cnt_n<<=commit_status_cnt

    io.page_offset_matches_o<<=U(0)
    for i in range(DEPTH_COMMIT):
        with when((io.page_offset_i[11:3]==commit_queue_q.address[i][11:3]) & (commit_queue_q.valid[i])):
            io.page_offset_matches_o <<= U(1)
    for i in range(DEPTH_SPEC):
        with when((io.page_offset_i[11:3]== speculative_queue_q.address[i][11:3]) & (speculative_queue_q.valid[i])):
            io.page_offset_matches_o <<=U(1)
    with when((io.page_offset_i[11:3]==io.paddr_i[11:3]) & (io.valid_without_flush_i)):
        io.page_offset_matches_o <<=U(1)
    clk_i=Reg(U.w(1))
    clk_i <<= io.clk_i
    rst_ni=Reg(U.w(1))
    rst_ni <<= io.rst_ni
    with when(((~clk_i)&io.clk_i) | (rst_ni&(~io.rst_ni))):
        with when(~io.rst_ni):
            speculative_queue_q =type1()
            speculative_read_pointer_q <<=U(0)
            speculative_write_pointer_q <<=U(0)
            speculative_status_cnt_q <<=U(0)
        with otherwise():
            speculative_queue_q = speculative_queue_n
            speculative_read_pointer_q <<=speculative_read_pointer_n
            speculative_write_pointer_q <<= speculative_write_pointer_n
            speculative_status_cnt_q <<= speculative_status_cnt_n

    with when(((~clk_i)&io.clk_i) | (rst_ni&(~io.rst_ni))):
        with when(~io.rst_ni):
            commit_queue_q =type1()
            commit_read_pointer_q <<=U(0)
            commit_write_pointer_q <<=U(0)
            commit_status_cnt_q <<=U(0)
        with otherwise():
            commit_queue_q = commit_queue_n
            commit_read_pointer_q <<=commit_read_pointer_n
            commit_write_pointer_q <<= commit_write_pointer_n
            commit_status_cnt_q <<= commit_status_cnt_n
## ********** 刘敏琪 8.30 End ********** ##

## ********** 刘敏琪 8.31 Begin ********** ##
    #Debug
    #assert
    #commit_and_flush
    with when((~clk_i)&io.clk_i):
        with when(~(io.rst_ni & io.flush_i & (~io.commit_i))):
            print("[Commit Queue] You are trying to commit and flush in the same cycle")
    #speculative_buffer_overflow
    with when((~clk_i)&io.clk_i):
        with when(~(io.rst_ni & (speculative_status_cnt_q==DEPTH_SPEC) & (~io.valid_i))):
            print("[Speculative Queue] You are trying to push new data although the buffer is not ready")
    #speculative_buffer_underflow
    with when((~clk_i)&io.clk_i):
        with when(~(io.rst_ni & (speculative_status_cnt_q==U(0)) & (~io.commit_i))):
            print("[Speculative Queue] You are committing although there are no stores to commit")
    #commit_buffer_overflow
    with when((~clk_i)&io.clk_i):
        with when(~(io.rst_ni & (commit_status_cnt_q==DEPTH_COMMIT) & (~io.commit_i))):
            print("[Commit Queue] You are trying to commit a store although the buffer is full")

## ********** 刘敏琪 8.31 End ********** ##



