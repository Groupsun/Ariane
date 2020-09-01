from amobuf_header import *

# ********** 蒋宇涛 2020.8.27,28 Begin ********** #
def amo_buffer():
    class amo_buf(Module):
        io = IO(
            flush_i=Input(Bool),
            valid_i=Input(Bool),
            ready_o=Output(Bool),
            amo_op_i=Input(ariane_pkg.amo_t.dtype),
            paddr_i=Input(U.w(riscv.PLEN)),
            data_i=Input(U.w(64)),
            data_size_i=Input(U.w(2)),
            amo_valid_commit_i=Input(Bool),
            no_st_pending_i=Input(Bool),
            amo_req_o=Output(ariane_pkg.amo_req_t),
            amo_resp_i=Input(ariane_pkg.amo_resp_t)
        )
        
        flush_amo_buffer=Wire(Bool)
        amo_valid=Wire(Bool)

        amo_op_t=Bundle(
            op=ariane_pkg.amo_t.dtype,
            paddr=U.w(riscv.PLEN),
            data=U.w(64),
            sizex=U.w(2)
        )
        
        amo_data_in=Reg(amo_op_t)
        amo_data_out=Reg(amo_op_t)
        
        io.amo_req_o.req <<= io.no_st_pending_i & io.amo_valid_commit_i & amo_valid
        io.amo_req_o.amo_op <<= amo_data_out.op
        io.amo_req_o.sizex <<= amo_data_out.sizex
        io.amo_req_o.operand_a <<= CatBits(U.w(64-riscv.PLEN)(0),amo_data_out.paddr)
        io.amo_req_o.operand_b <<= amo_data_out.data

        amo_data_in.op <<= io.amo_op_i
        amo_data_in.data <<= io.data_i
        amo_data_in.paddr <<= io.paddr_i
        amo_data_in.sizex <<= io.data_size_i
# ********** 蒋宇涛 2020.8.27,28 End ********** #
# ********** 蒋宇涛 2020.8.29,31 Start ********** #        
        i_amo_fifo = fifo_v3(DEPTH=1,dtype=amo_op_t)
        fifo_io = i_amo_fifo.io

        fifo_io.flush_i <<= flush_amo_buffer
        fifo_io.testmode_i <<= U(0)
        amo_valid <<= fifo_io.full_o
        io.ready_o <<= fifo_io.empty_o
        
        BundleLink(fifo_io.data_i,amo_data_in,amo_op_t)
        fifo_io.push_i <<= io.valid_i

        BundleLink(amo_data_out,fifo_io.data_o,amo_op_t)
        fifo_io.pop_i <<= io.amo_resp_i.ack
        
        
    return amo_buf()

# ********** 蒋宇涛 2020.8.29,31 End ********** #

if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(amo_buffer()), "amo_buffer.fir"))