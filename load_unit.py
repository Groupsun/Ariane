from amobuf_and_loadunit_header import *
# ********** 蒋宇涛  Begin ********** #
def load_unit(ArianeCfg = ariane_pkg.ArianeDefaultConfig):
    class loadunit(Module):
        io=IO(
            flush_i=Input(Bool),

            valid_i=Input(Bool),
            lsu_ctrl_i=Input(ariane_pkg.lsu_ctrl_t),
            pop_ld_o=Output(Bool),

            valid_o=Output(Bool),
            trans_id_o=Output(U.w(ariane_pkg.TRANS_ID_BITS)),
            result_o=Output(U.w(64)),
            ex_o=Output(ariane_pkg.exception_t),

            translation_req_o=Output(Bool),
            vaddr_o=Output(U.w(riscv.VLEN)),
            paddr_i=Input(U.w(riscv.PLEN)),
            ex_i=Input(ariane_pkg.exception_t),
            dtlb_hit_i=Input(Bool),

            page_offset_o=Output(U.w(12)),
            page_offset_matches_i=Input(Bool),
            store_buffe_empty_i=Input(Bool),
            commit_tran_id_i=Input(U.w(ariane_pkg.TRANS_ID_BITS)),

            req_port_i=Input(ariane_pkg.dcache_req_o_t),
            req_port_o=Output(ariane_pkg.dcache_req_i_t),
            dcache_wbuffer_empty_i=Input(Bool)
        )  

        class state():
            IDLE=U(0)
            WAIT_GNT=U(1)
            SEND_TAG=U(2)
            WAIT_PAGE_OFFSET=U(3)
            ABORT_TRANSACTION=U(4)
            ABORT_TRANSACTION_NC=U(5)
            WAIT_TRANSLATION=U(6)
            WAIT_FLUSH=U(7)
            WAIT_WB_EMPTY=U(8)

            dtype=U.w(4)

        state_d=Reg(state.dtype)
        state_q=Reg(state.dtype)

        databundle = Bundle(
            trans_id=U.w(ariane_pkg.TRANS_ID_BITS),
            address_offset=U.w(3),
            operator=ariane_pkg.fu_op.dtype.value
        )
        load_data_d=Reg(databundle)
        load_data_q=Reg(databundle)
        in_data=Wire(databundle)

        io.page_offset_o <<= io.lsu_ctrl_i.vaddr[11:0]
        io.vaddr_o <<= io.lsu_ctrl_i.vaddr
        io.req_port_o.data_we <<= U(0)
        io.req_port_o.data_wdata <<= U(0)

        BundleLink(in_data, CatBits(io.lsu_ctrl_i.trans_id,io.lsu_ctrl_i.vaddr[2:0],io.lsu_ctrl_i.operator),databundle)
        io.req_port_o.address_index <<= io.lsu_ctrl_i.vaddr[ariane_pkg.DCACHE_INDEX_WIDTH-1:0]
        io.req_port_o.address_tag <<= io.paddr_i[ariane_pkg.DCACHE_TAG_WIDTH+ariane_pkg.DCACHE_INDEX_WIDTH-1:ariane_pkg.DCACHE_TAG_WIDTH]
        BundleLink(io.ex_o, io.ex_i,ariane_pkg.exception_t)

        stall_nc = Wire(Bool)
        stall_nc <<= (
            ~ (io.dcache_wbuffer_empty_i|io.store_buffe_empty_i) 
            & (ariane_pkg.is_inside_cacheable_regions(ArianeCfg,io.paddr_i))
        )|(
            io.commit_tran_id_i != io.lsu_ctrl_i.trans_id 
            & ariane_pkg.is_inside_nonidempotent_regions(ArianeCfg,io.paddr_i)
        )

        # load control
        state_d <<= state_q
        BundleLink(load_data_d,load_data_q,databundle)
        io.translation_req_o <<= U(0)
        io.req_port_o.data_req <<= U(0)
        io.pop_ld_o <<= U(0)

        io.req_port_o.kill_req <<= U(0)
        io.req_port_o.tag_valid <<= U(0)
        io.req_port_o.data_be <<= io.lsu_ctrl_i.be
        io.req_port_o.data_size <<= ariane_pkg.extract_transfer_size(io.lsu_ctrl_i.operator)

        with when(state_q == state.IDLE):
            with when(io.valid_i):
                io.translation_req_o <<= U(1)
                with when(~io.page_offset_matches_i):
                    io.req_port_o.data_req <<= U(1)
                    with when(~io.req_port_i.data_gnt):
                        state_d <<= state.WAIT_GNT
                    with otherwise():
                        with when(io.dtlb_hit_i & ~stall_nc):
                            state_d <<= state.SEND_TAG
                            io.pop_ld_o <<= U(1)
                        with elsewhen(io.dtlb_hit_i & stall_nc):
                            state_d <<= state.ABORT_TRANSACTION_NC
                        with otherwise():
                            state_d <<= state.ABORT_TRANSACTION
                with otherwise():
                    state_d <<= state.WAIT_PAGE_OFFSET
        
        with elsewhen(state_q == state.WAIT_PAGE_OFFSET):
            with when(~io.page_offset_matches_i):
                state_d <<= state.WAIT_GNT
        
        with elsewhen((state_q==state.ABORT_TRANSACTION)|(state_q==state.ABORT_TRANSACTION_NC)):
            io.req_port_o.kill_req <<= U(1)
            io.req_port_o.tag_valid <<= U(1)
            with when(state_q == state.ABORT_TRANSACTION_NC):
                state_d <<= state.WAIT_WB_EMPTY
            with otherwise():
                state_d <<= state.WAIT_TRANSLATION
            
        with elsewhen(state_q==state.WAIT_WB_EMPTY):
            with when(io.dcache_wbuffer_empty_i):
                state_d <<= state.WAIT_TRANSLATION
        
        with elsewhen(state_q==state.WAIT_TRANSLATION):
            io.translation_req_o <<= U(1)
            with when(io.dtlb_hit_i):
                state_d <<= state.WAIT_GNT
            
        with elsewhen(state_q==state.WAIT_GNT):
            io.translation_req_o <<= U(1)
            io.req_port_o.data_req <<= U(1)
            with when(io.req_port_i.data_gnt):
                with when(io.dtlb_hit_i & ~stall_nc):
                    state_d <<= state.SEND_TAG
                    io.pop_ld_o <<= U(1)
                with elsewhen(io.dtlb_hit_i & stall_nc):
                    state_d <<= state.ABORT_TRANSACTION_NC
                with otherwise():
                    state_d <<= state.ABORT_TRANSACTION

        with elsewhen(state_q==state.SEND_TAG):
            io.req_port_o.tag_valid <<= U(1)
            state_d <<= state.IDLE
            with when(io.valid_i):
                io.translation_req_o <<= U(1)
                with when(~io.page_offset_matches_i):
                        io.req_port_o.data_req <<= U(1)
                        with when(~io.req_port_i.data_gnt):
                            state_d <<= state.WAIT_GNT
                        with otherwise():
                            with when(io.dtlb_hit_i & ~stall_nc):
                                state_d <<= state.SEND_TAG
                                io.pop_ld_o <<= U(1)
                            with elsewhen(io.dtlb_hit_i & stall_nc):
                                state_d <<= state.ABORT_TRANSACTION_NC
                            with otherwise():
                                state_d <<= state.ABORT_TRANSACTION
                with otherwise():
                    state_d <<= state.WAIT_PAGE_OFFSET
            with when(io.ex_i.valid):
                io.req_port_o.kill_req <<= U(1)
            
        with elsewhen(state_q==state.WAIT_FLUSH):
            io.req_port_o.kill_req <<= U(1)
            io.req_port_o.tag_valid <<= U(1)
            state_d <<= state.IDLE
    
        # we got an exception
        with when(io.ex_i.valid & io.valid_i):
            state_d <<= state.IDLE
            with when(~io.req_port_i.data_rvalid):
                io.pop_ld_o <<= U(1)
        
        with when(io.pop_ld_o & ~io.ex_i.valid):
            BundleLink(load_data_d,in_data,databundle)

        with when(io.flush_i):
            state_d <<= state.WAIT_FLUSH

        #retire load
        io.valid_o <<= U(0)
        io.trans_id_o <<= load_data_q.trans_id
        with when(io.req_port_i.data_rvalid & state_q != state.WAIT_FLUSH):
            with when(~io.req_port_o.kill_req):
                io.valid_o <<= U(1)
            with when(io.ex_i.valid):
                io.valid_o <<= U(1)
        
        with when((io.valid_i & io.ex_i.valid) & (~io.req_port_i.data_rvalid)):
            io.valid_o <<= U(1)
            io.trans_id_o = io.lsu_ctrl_i.trans_id
        with elsewhen(state_q == state.WAIT_TRANSLATION):
            io.valid_o <<= U(0)

        with when(Module.reset == U(0)):
            state_q <<= state.IDLE
            BundleLink(load_data_q,U(0),databundle)
        with otherwise():
            state_q <<= state_d
            BundleLink(load_data_q ,load_data_d,databundle)
        
        # sign extend
        shifted_data = Wire(U.w(64))
        shifted_data <<= io.req_port_i.data_rdata >> CatBits(load_data_q.address_offset,U.w(3)(0))
        sign_bits = Wire(Vec(8,Bool))
        idx_d = Wire(U.w(3))
        idx_q = Wire(U.w(3))
        sign_bit, signed_d, signed_q, fp_sign_d, fp_sign_q = [Wire(Bool) for i in range(5)]
        
        signed_d <<= Inside(load_data_d.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LW,ariane_pkg.fu_op.LH,ariane_pkg.fu_op.LB])))
        fp_sign_d <<= Inside(load_data_d.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.FLW,ariane_pkg.fu_op.FLH,ariane_pkg.fu_op.FLB])))
        
        with when(Inside(load_data_d.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LW,ariane_pkg.fu_op.FLW])))):
            idx_d <<= load_data_d.address_offset + U(3)
        with otherwise():
            with when(Inside(load_data_d.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LH,ariane_pkg.fu_op.FLH])))):
                idx_d <<= load_data_d.address_offset + U(1)
            with otherwise():
                idx_d <<= load_data_d.address_offset
        
        sbs = [
            io.req_port_i.data_rdata[63],
            io.req_port_i.data_rdata[55],
            io.req_port_i.data_rdata[47],
            io.req_port_i.data_rdata[39],
            io.req_port_i.data_rdata[31],
            io.req_port_i.data_rdata[23],
            io.req_port_i.data_rdata[15],
            io.req_port_i.data_rdata[7]
        ]
        for i in range(8):
            sign_bits[i] <<= sbs[i]
        
        sign_bit <<= signed_q & sign_bits[idx_q] | fp_sign_q
        
        io.result_o <<= shifted_data
        
        with when(Inside(load_data_q.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LW,ariane_pkg.fu_op.LWU,ariane_pkg.fu_op.FLW])))):
            co = ""
            for i in range(32):
                co+="sign_bit,"
            co+="shifted_data[31:0]"
            exec("io.result_o <<= CatBits({})".format(co))
        with when(Inside(load_data_q.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LH,ariane_pkg.fu_op.LHU,ariane_pkg.fu_op.FLH])))):
            co = ""
            for i in range(48):
                co+="sign_bit,"
            co+="shifted_data[15:0]"
            exec("io.result_o <<= CatBits({})".format(co))
        with when(Inside(load_data_q.operator,list(map(lambda x: U(x.value),[ariane_pkg.fu_op.LB,ariane_pkg.fu_op.LBU,ariane_pkg.fu_op.FLB])))):
            co = ""
            for i in range(56):
                co+="sign_bit,"
            co+="shifted_data[7:0]"
            exec("io.result_o <<= CatBits({})".format(co))
        
        
        with when(Module.reset == U(0)):
            idx_q <<= U(0)
            signed_q <<= U(0)
            fp_sign_q <<= U(0)
        with otherwise():
            idx_q <<= idx_d
            signed_q <<= signed_d
            fp_sign_q <<= fp_sign_d
        
    return loadunit()
# ********** 蒋宇涛  End ********** #
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(load_unit()), "load_unit.fir"))