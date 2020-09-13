from store_buffer_08_31 import *
from amo_buffer import *
from pyhcl import  *
from pkg import *
### ---------刘敏琪 Begin--------- ###
class store_unit(Module):
    io=IO(
        clk_i=Input(U.w(1)),
        rst_ni=Input(U.w(1)),
        flush_i=Input(U.w(1)),
        no_st_pending_o=Output(U.w(1)),
        store_buffer_empty_o=Output(U.w(1)),
        valid_i=Input(U.w(1)),
        lsu_ctrl_i=Input(lsu_ctrl_t),
        pop_st_o=Output(U.w(1)),
        commit_i=Input(U.w(1)),
        commit_ready_o=Output(U.w(1)),
        amo_valid_commit_i=Input(U.w(1)),
        valid_o=Output(U.w(1)),
        trans_id_o=Output(U.w(TRANS_ID_BITS)),
        result_o=Output(U.w(64)),
        ex_o=Output(exception_t),
        translation_req_o=Output(U.w(1)),
        vaddr_o=Output(U.w(VLEN)),
        paddr_i=Input(U.w(PLEN)),
        ex_i=Input(exception_t),
        dtlb_hit_i=Input(U.w(1)),
        page_offset_i=Input(U.w(12)),
        page_offset_matches_o=Output(U.w(1)),
        amo_req_o=Output(amo_req_t),
        amo_resp_i=Input(amo_resq_t),
        req_port_i = Input(dcache_req_o_t),
        req_port_o = Output(dcache_req_i_t)
    )
    io.result_o<<=U.w(64)(0)
    class state:
        IDLE=U(0)
        VALID_STORE=U(1)
        WAIT_TRANSLATION=U(2)
        WAIT_STORE_READY=U(3)
        dtype=U.w(2)
    state_q=Reg(state.dtype)
    state_d=Reg(state.dtype)
    st_ready =Reg(U.w(1))
    st_valid=Reg(U.w(1))
    st_valid_without_flush=Reg(U.w(1))
    instr_is_amo=Reg(U.w(1))
    instr_is_amo <<= is_amo(io.lsu_ctrl_i.operator)
    st_data_n=Reg(U.w(64))
    st_data_q=Reg(U.w(64))
    st_be_n=Reg(U.w(8))
    st_be_q=Reg(U.w(8))
    st_data_size_n=Reg(U.w(2))
    st_data_size_q=Reg(U.w(2))
    #amo_t
    amo_op_d=Reg(amo_t.dtype)
    amo_op_q=Reg(amo_t.dtype)
    trans_id_n=Reg(U.w(TRANS_ID_BITS))
    trans_id_q=Reg(U.w(TRANS_ID_BITS))
    io.vaddr_o <<= io.lsu_ctrl_i.vaddr
    io.trans_id_o <<= trans_id_q
    #store_control
    io.translation_req_o <<=U(0)
    io.valid_o <<= U(0)
    st_valid <<= U(0)
    st_valid_without_flush <<=U(0)
    io.pop_st_o <<= U(0)
    io.ex_o <<= io.ex_i
    trans_id_n<<=io.lsu_ctrl_i.trans_id
    state_d <<= state_q
    #case
    #IDLE
    with when(state_q==state.IDLE):
        with when(io.valid_i):
            state_d <<= state_q
            io.translation_req_o <<= U(1)
            io.pop_st_o <<= U(1)
            with when(~io.dtlb_hit_i):
                state_d <<= state.WAIT_TRANSLATION
                io.pop_st_o <<= U(0)
            with when(~st_ready):
                state_d <<=state.WAIT_STORE_READY
                io.pop_st_o <<= U(0)
    #VALID_STORE
    with when(state_q==state.VALID_STORE):
        io.valid_o <<= U(1)
        with when(~io.flush_i):
            st_valid <<= U(1)
        st_valid_without_flush <<=U(1)
        with when(io.valid_i & (~instr_is_amo)):
            io.translation_req_o <<= U(1)
            state_d = state.VALID_STORE
            io.pop_st_o <<=U(1)
            with when(~io.dtlb_hit_i):
                state_d <<= state.WAIT_TRANSLATION
                io.pop_st_o <<= U(0)
            with when(~st_ready):
                state_d=state.WAIT_STORE_READY
                io.pop_st_o<<=U(0)
        with otherwise():
            state_d=state.IDLE
    #WAIT_STORE_READY
    with when(state_q==state.WAIT_STORE_READY):
        io.translation_req_o <<=U(1)
        with when(st_ready & io.dtlb_hit_i):
            state_d <<=state.IDLE
    #WAIT_TRANSLATION
    with when(state_q==state.WAIT_TRANSLATION):
        io.translation_req_o <<= U(1)
        with when(io.dtlb_hit_i):
            state_d <<= state.IDLE
    #encase
    with when(io.ex_i.valid & (state_q!=state.IDLE)):
        io.pop_st_o <<= U(1)
        st_valid <<=U(0)
        state_d <<= state.IDLE
        io.valid_o <<= U(1)

    with when(io.flush_i):
        state_d <<= state.IDLE

    #Re-aligner
    st_be_n <<= io.lsu_ctrl_i.be
    st_data_n <<= io.lsu_ctrl_i.data if instr_is_amo else data_align(io.lsu_ctrl_i.vaddr[2:0],io.lsu_ctrl_i.data)
    st_data_size_n <<= extract_transfer_size(io.lsu_ctrl_i.operator)
    with when(io.lsu_ctrl_i.operator == fu_op.AMO_SCW | io.lsu_ctrl_i.operator == fu_op.AMO_SCD):
        amo_op_d <<= amo_t.AMO_SC
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_SWAPW |io.lsu_ctrl_i.operator==fu_op.AMO_SWAPD ):
        amo_op_d <<=amo_t.AMO_SWAP
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_ADDW |io.lsu_ctrl_i.operator==fu_op.AMO_ADDD ):
        amo_op_d <<=amo_t.AMO_ADD
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_ANDW |io.lsu_ctrl_i.operator==fu_op.AMO_ANDD ):
        amo_op_d <<=amo_t.AMO_AND
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_ORW |io.lsu_ctrl_i.operator==fu_op.AMO_ORD ):
        amo_op_d <<=amo_t.AMO_OR
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_XORW |io.lsu_ctrl_i.operator==fu_op.AMO_XORD ):
        amo_op_d <<=amo_t.AMO_XOR
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_MAXW |io.lsu_ctrl_i.operator==fu_op.AMO_MAXD ):
        amo_op_d <<=amo_t.AMO_MAX
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_MAXWU |io.lsu_ctrl_i.operator==fu_op.AMO_MAXDU ):
        amo_op_d <<=amo_t.AMO_MAXU
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_MINW |io.lsu_ctrl_i.operator==fu_op.AMO_MIND ):
        amo_op_d <<=amo_t.AMO_MIN
    with elsewhen(io.lsu_ctrl_i.operator==fu_op.AMO_MINWU |io.lsu_ctrl_i.operator==fu_op.AMO_MINDU ):
        amo_op_d <<=amo_t.AMO_MINU
    with otherwise():
        amo_op_d <<=amo_t.AMO_NONE

    store_buffer_valid=Reg(U.w(1))
    amo_buffer_valid=Reg(U.w(1))
    store_buffer_ready=Reg(U.w(1))
    amo_buffer_ready=Reg(U.w(1))
    store_buffer_valid <<= st_valid & (amo_op_q == amo_t.AMO_NONE)
    amo_buffer_valid <<= st_valid & (amo_op_q != amo_t.AMO_NONE)
    st_ready <<= store_buffer_ready & amo_buffer_ready

    store_buffer_i=store_buffer()
    store_buffer_i.io.ready_o <<= store_buffer_ready
    store_buffer_i.io.valid_i <<= store_buffer_valid
    store_buffer_i.io.valid_without_flush_i <<= st_valid_without_flush
    store_buffer_i.io.data_i <<= st_data_q
    store_buffer_i.io.be_i <<= st_be_q
    store_buffer_i.io.data_size_i <<= st_data_size_q
    store_buffer_i.io.req_port_i <<= io.req_port_i
    store_buffer_i.io.req_port_o <<= io.req_port_o

    i_amo_buffer=amo_buffer()
    i_amo_buffer.io.valid_i <<= amo_buffer_valid
    i_amo_buffer.io.ready_o <<= amo_buffer_ready
    i_amo_buffer.io.paddr_i <<= io.paddr_i
    i_amo_buffer.io.amo_op_i <<= amo_op_q
    i_amo_buffer.io.data_i <<= st_data_q
    i_amo_buffer.io.data_size_i <<= st_data_size_q
    i_amo_buffer.io.amo_req_o <<= io.amo_req_o
    i_amo_buffer.io.amo_resp_i <<= io.amo_resp_i
    i_amo_buffer.io.amo_valid_commit_i <<= io.amo_valid_commit_i
    i_amo_buffer.io.no_st_pending_i <<= io.no_st_pending_o

    clk_i =Reg(U.w(1))
    rst_ni =Reg(U.w(1))
    clk_i <<= io.clk_i
    rst_ni <<= io.rst_ni
    with when( ((~clk_i)&io.clk_i) | ((~io.rst_ni) & rst_ni) ):
        with(when(~io.rst_ni)):
            state_q <<= state.IDLE
            st_be_q <<= U(0)
            st_data_q <<= U(0)
            st_data_size_q <<= U(0)
            trans_id_q <<= U(0)
            amo_op_q <<= amo_t.AMO_NONE
        with otherwise():
            state_q <<= state_d
            st_be_q <<= st_be_n
            st_data_q <<= st_data_n
            trans_id_q <<= trans_id_n
            st_data_size_q <<= st_data_size_n
            amo_op_q <<= amo_op_d


### ---------刘敏琪 End--------- ###
