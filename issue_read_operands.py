## ********** 黄智权、韩耀华 9.8 Begin ********** ##
from pyhcl import *
from functools import reduce
from ariane_pkg import *
import riscv_pkg as riscv

def isunknown(x):
    return x == None

def issue_read_operands(NR_COMMIT_PORTS: int = 2):
  class issue_read_operands(Module):
    io = IO(
      clk_i=Input(U.w(1)), # Clock
      rst_ni=Input(U.w(1)), # Asynchronous reset active low
      # flush
      flush_i=Input(U.w(1)),
      # coming from rename
      issue_instr_i=Input(scoreboard_entry_t),
      issue_instr_valid_i=Input(U.w(1)),
      issue_ack_o=Output(U.w(1)),
      # lookup rd in scoreboard
      rs1_o=Output(U.w(REG_ADDR_SIZE)),
      rs1_i=Input(U.w(64)),
      rs1_valid_i=Input(U.w(1)),
      rs2_o=Output(U.w(REG_ADDR_SIZE)),
      rs2_i=Input(U.w(64)),
      rs2_valid_i=Input(U.w(1)),
      rs3_o=Output(U.w(REG_ADDR_SIZE)),
      rs3_i=Input(U.w(FLEN)),
      rs3_valid_i=Input(U.w(1)),
      # get clobber input
      rd_clobber_gpr_i=Input(Vec(2**REG_ADDR_SIZE-1, fu_t)),
      rd_clobber_fpr_i=Input(Vec(2**REG_ADDR_SIZE-1, fu_t)),
      # To FU, just single issue for now
      fu_data_o=Output(fu_data_t),
      pc_o=Output(U.w(riscv.VLEN)),
      is_compressed_instr_o=Output(U.w(1)),
      # ALU 1
      flu_ready_i=Input(U.w(1)),      # Fixed latency unit ready to accept a new request
      alu_valid_o=Output(U.w(1)),      # Output is valid
      # Branches and Jumps
      branch_valid_o=Output(U.w(1)),   #  this is a valid branch instruction
      branch_predict_o = Output(branchpredict_sbe_t),
      # LSU
      lsu_ready_i=Input(U.w(1)),      # FU is ready
      lsu_valid_o=Output(U.w(1)),      # Output is valid
      # MULT
      mult_valid_o=Output(U.w(1)),     # Output is valid
      # FPU
      fpu_ready_i=Input(U.w(1)),      # FU is ready
      fpu_valid_o=Output(U.w(1)),      # Output is valid
      fpu_fmt_o=Output(U.w(2)),        # FP fmt field from instr.
      fpu_rm_o=Output(U.w(3)),         # FP rm field from instr.
      # CSR
      csr_valid_o=Output(U.w(1)),      # Output is valid
      # commit port
      waddr_i=Input(Vec(NR_COMMIT_PORTS,Vec(5,U.w(1)))),
      wdata_i=Input(Vec(NR_COMMIT_PORTS,Vec(64,U.w(1)))),
      we_gpr_i=Input(U.w(NR_COMMIT_PORTS)),
      we_fpr_i=Input(U.w(NR_COMMIT_PORTS))
      # committing instruction instruction
      # from scoreboard
      # input  scoreboard_entry     commit_instr_i,
      # output logic                commit_ack_o
    )
    stall=Wire(U.w(1))   # stall signal, we do not want to fetch any more entries
    fu_busy=Wire(U.w(1)) # functional unit is busy
    operand_a_regfile=Wire(U.w(64)) 
    operand_b_regfile=Wire(U.w(64))   # operands coming from regfile
    operand_c_regfile=Wire(U.w(FLEN)) # third operand only from fp regfile
    # output flipflop (ID <-> EX)
    operand_a_n=Wire(U.w(64)) 
    operand_a_q=Wire(U.w(64))
    operand_b_n=Wire(U.w(64))
    operand_b_q=Wire(U.w(64))
    imm_n=Wire(U.w(64))
    imm_q=Wire(U.w(64))

    alu_valid_q=Wire(U.w(1))
    mult_valid_q=Wire(U.w(1))
    fpu_valid_q=Wire(U.w(1))
    fpu_fmt_q=Wire(U.w(2))
    fpu_rm_q=Wire(U.w(3))
    lsu_valid_q=Wire(U.w(1))
    csr_valid_q=Wire(U.w(1))
    branch_valid_q=Wire(U.w(1))

    trans_id_n = Wire(U.w(TRANS_ID_BITS))
    trans_id_q = Wire(U.w(TRANS_ID_BITS))
    # operation to perform
    operator_n = fu_op
    operator_q = fu_op
    # functional unit to use
    fu_n = fu_t
    fu_q = fu_t

    # forwarding signals
    forward_rs1=Wire(U.w(1)) 
    forward_rs2=Wire(U.w(1)) 
    forward_rs3=Wire(U.w(1))

    # original instruction stored in tval
    orig_instr = riscv.instruction_t
    orig_instr <<= riscv.instruction_t(io.issue_instr_i.ex.tval[31:0])

    # ID <-> EX registers
    io.fu_data_o.operand_a <<= operand_a_q
    io.fu_data_o.operand_b <<= operand_b_q
    io.fu_data_o.fu        <<= fu_q
    io.fu_data_o.operator  <<= operator_q
    io.fu_data_o.trans_id  <<= trans_id_q
    io.fu_data_o.imm       <<= imm_q
    io.alu_valid_o         <<= alu_valid_q
    io.branch_valid_o      <<= branch_valid_q
    io.lsu_valid_o         <<= lsu_valid_q
    io.csr_valid_o         <<= csr_valid_q
    io.mult_valid_o        <<= mult_valid_q
    io.fpu_valid_o         <<= fpu_valid_q
    io.fpu_fmt_o           <<= fpu_fmt_q
    io.fpu_rm_o            <<= fpu_rm_q

    # ---------------
    # Issue Stage
    # ---------------
    
    # select the right busy signal
    # this obviously depends on the functional unit we need
    # always_comb begin : unit_busy
    with when(io.issue_instr_i.fu == fu_t.NONE):
        fu_busy = U.w(1)(0)
    with elsewhen(io.issue_instr_i.fu == fu_t.ALU or \
                  io.issue_instr_i.fu == fu_t.CTRL_FLOW or \
                  io.issue_instr_i.fu == fu_t.CSR or \
                  io.issue_instr_i.fu == fu_t.MULT):
        fu_busy = ~io.flu_ready_i
    with elsewhen(io.issue_instr_i == fu_t.FPU or io.issue_instr_i == fu_t.FPU_VEC):
        fu_busy = ~io.fpu_ready_i
    with elsewhen(io.issue_instr_i == fu_t.LOAD or io.issue_instr_i == fu_t.STORE):
        fu_busy = ~io.lsu_ready_i
    with otherwise():
        fu_busy = U.w(1)(0)

    # ---------------
    # Register stage
    # ---------------
    # check that all operands are available, otherwise stall
    # forward corresponding register
    # always_comb begin : operands_available
    stall = U.w(1)(0)
    # operand forwarding signals
    forward_rs1 = U.w(1)(0)
    forward_rs2 = U.w(1)(0)
    forward_rs3 = U.w(1)(0); # FPR only
    # poll the scoreboard for those values
    io.rs1_o = io.issue_instr_i.rs1
    io.rs2_o = io.issue_instr_i.rs2
    io.rs3_o = io.issue_instr_i.result[REG_ADDR_SIZE-1:0]; # rs3 is encoded in imm field

    # 0. check that we are not using the zimm type in RS1
    #    as this is an immediate we do not have to wait on anything here
    # 1. check if the source registers are clobbered --> check appropriate clobber list (gpr/fpr)
    # 2. poll the scoreboard
    with when(not io.issue_instr_i.use_zimm and \
              Mux(is_rs1_fpr(io.issue_instr_i.op), 
                  io.rd_clobber_fpr_i[io.issue_instr_i.rs1] != fu_t.NONE, 
                  io.rd_clobber_gpr_i[io.issue_instr_i.rs1] != fu_t.NONE)):
        # check if the clobbering instruction is not a CSR instruction, CSR instructions can only
        # be fetched through the register file since they can't be forwarded
        # if the operand is available, forward it. CSRs don't write to/from FPR
        with when(io.rs1_valid_i and \
                  Mux(is_rs1_fpr(io.issue_instr_i.op), 
                      U.w(1)(1), 
                      io.rd_clobber_gpr_i[io.issue_instr_i.rs1] != fu_t.CSR)):
            forward_rs1 = U.w(1)(1)
        with otherwise(): # the operand is not available -> stall
            stall = U.w(1)(1)

    with when(Mux(is_rs2_fpr(io.issue_instr_i.op), 
                  io.rd_clobber_fpr_i[io.issue_instr_i.rs2] != fu_t.NONE, 
                  io.rd_clobber_gpr_i[io.issue_instr_i.rs2] != fu_t.NONE)):
        # if the operand is available, forward it. CSRs don't write to/from FPR
        with when(io.rs2_valid_i and \
                  Mux(is_rs2_fpr(io.issue_instr_i.op), 
                      U.w(1)(1), 
                      io.rd_clobber_gpr_i[io.issue_instr_i.rs2] != fu_t.CSR)):
            forward_rs2 = U.w(1)(1)
        with otherwise(): # the operand is not available -> stall
            stall = U.w(1)(1)

    with when(is_imm_fpr(io.issue_instr_i.op) and \
              io.rd_clobber_fpr_i[io.issue_instr_i.result[REG_ADDR_SIZE-1:0]] != fu_t.NONE):
        # if the operand is available, forward it. CSRs don't write to/from FPR so no need to check
        with when(io.rs3_valid_i):
            forward_rs3 = U.w(1)(1)
        with otherwise(): # the operand is not available -> stall
            stall = U.w(1)(1)
    # Forwarding/Output MUX
    # always_comb begin : forwarding_operand_select
    # default is regfiles (gpr or fpr)
    operand_a_n = operand_a_regfile
    operand_b_n = operand_b_regfile
    # immediates are the third operands in the store case
    # for FP operations, the imm field can also be the third operand from the regfile
    imm_n      = Mux(is_imm_fpr(io.issue_instr_i.op), 
                     operand_c_regfile, 
                     io.issue_instr_i.result)
    trans_id_n = io.issue_instr_i.trans_id
    fu_n       = io.issue_instr_i.fu
    operator_n = io.issue_instr_i.op
    # or should we forward
    with when(forward_rs1):
        operand_a_n  = io.rs1_i

    with when(forward_rs2):
        operand_b_n  = io.rs2_i

    with when(forward_rs3):
        imm_n  = io.rs3_i

    # use the PC as operand a
    with when(io.issue_instr_i.use_pc):
        operand_a_n = CatBits(*([io.issue_instr_i.pc[riscv.VLEN-1]] * (64-riscv.VLEN)), io.issue_instr_i.pc)

    # use the zimm as operand a
    with when(io.issue_instr_i.use_zimm):
        # zero extend operand a
        operand_a_n = CatBits(U.w(59)(0), io.issue_instr_i.rs1[4:0])

    # or is it an immediate (including PC), this is not the case for a store and control flow instructions
    # also make sure operand B is not already used as an FP operand
    with when(io.issue_instr_i.use_imm and \
              io.issue_instr_i.fu != fu_t.STORE and \
              io.issue_instr_i.fu != fu_t.CTRL_FLOW and \
              not is_rs2_fpr(io.issue_instr_i.op)):
        io.operand_b_n = io.issue_instr_i.result

    # FU select, assert the correct valid out signal (in the next cycle)
    # This needs to be like this to make verilator happy. I know its ugly.
    # always_ff @(posedge clk_i or negedge rst_ni) begin
    with when(not io.rst_ni):
        alu_valid_q    <<= U.w(1)(0)
        lsu_valid_q    <<= U.w(1)(0)
        mult_valid_q   <<= U.w(1)(0)
        fpu_valid_q    <<= U.w(1)(0)
        fpu_fmt_q      <<= U.w(2)(0)
        fpu_rm_q       <<= U.w(3)(0)
        csr_valid_q    <<= U.w(1)(0)
        branch_valid_q <<= U.w(1)(0)
    with otherwise():
        alu_valid_q    <<= U.w(1)(0)
        lsu_valid_q    <<= U.w(1)(0)
        mult_valid_q   <<= U.w(1)(0)
        fpu_valid_q    <<= U.w(1)(0)
        fpu_fmt_q      <<= U.w(2)(0)
        fpu_rm_q       <<= U.w(3)(0)
        csr_valid_q    <<= U.w(1)(0)
        branch_valid_q <<= U.w(1)(0)
    # Exception pass through:
    # If an exception has occurred simply pass it through
    # we do not want to issue this instruction
    with when(not io.issue_instr_i.ex.valid and io.issue_instr_valid_i and io.issue_ack_o):
        with when(io.issue_instr_i.fu == fu_t.ALU):
            alu_valid_q   <<= U.w(1)(1)
        with elsewhen(io.issue_instr_i.fu == fu_t.CTRL_FLOW):
            branch_valid_q<<= U.w(1)(1)
        with elsewhen(io.issue_instr_i.fu == fu_t.MULT):
            mult_valid_q  <<= U.w(1)(1)
        with elsewhen(io.issue_instr_i.fu == fu_t.FPU):
            fpu_valid_q   <<= U.w(1)(1)
            fpu_fmt_q     <<= orig_instr.rftype.fmt; # fmt bits from instruction
            fpu_rm_q      <<= orig_instr.rftype.rm;  # rm bits from instruction
        with elsewhen(io.issue_instr_i.fu == fu_t.FPU_VEC):
            fpu_valid_q   <<= U.w(1)(1)
            fpu_fmt_q     <<= orig_instr.rvftype.vfmt;         # vfmt bits from instruction
            fpu_rm_q      <<= CatBits(U.w(2)(0), orig_instr.rvftype.repl); # repl bit from instruction
        with elsewhen(io.issue_instr_i.fu == fu_t.LOAD or io.issue_instr_i.fu == fu_t.STORE):
            lsu_valid_q   <<= U.w(1)(1)
        with elsewhen(io.issue_instr_i.fu == fu_t.CSR):
            csr_valid_q   <<= U.w(1)(1)
        with otherwise():
            ...
    # if we got a flush request, de-assert the valid flag, otherwise we will start this
    # functional unit with the wrong inputs
    with when(io.flush_i):
        alu_valid_q   <<= U.w(1)(0)
        lsu_valid_q   <<= U.w(1)(0)
        mult_valid_q  <<= U.w(1)(0)
        fpu_valid_q   <<= U.w(1)(0)
        csr_valid_q   <<= U.w(1)(0)
        branch_valid_q<<= U.w(1)(0)

    # We can issue an instruction if we do not detect that any other instruction is writing the same
    # destination register.
    # We also need to check if there is an unresolved branch in the scoreboard.
    # always_comb begin : issue_scoreboard
        # default assignment
        io.issue_ack_o = U.w(1)(0)
        # check that we didn't stall, that the instruction we got is valid
        # and that the functional unit we need is not busy
        with when(io.issue_instr_valid_i):
            # check that the corresponding functional unit is not busy
            with when(not stall and not fu_busy):
                # -----------------------------------------
                # WAW - Write After Write Dependency Check
                # -----------------------------------------
                # no other instruction has the same destination register -> issue the instruction
                with when(Mux(is_rd_fpr(io.issue_instr_i.op), 
                              (io.rd_clobber_fpr_i[io.issue_instr_i.rd] == fu_t.NONE), 
                              (io.rd_clobber_gpr_i[io.issue_instr_i.rd] == fu_t.NONE))):
                    io.issue_ack_o = U.w(1)(1)
                # or check that the target destination register will be written in this cycle by the
                # commit stage
                for i in range(NR_COMMIT_PORTS):
                    with when(Mux(is_rd_fpr(io.issue_instr_i.op),
                              (io.we_fpr_i[i] and io.waddr_i[i] == io.issue_instr_i.rd),
                              (io.we_gpr_i[i] and io.waddr_i[i] == io.issue_instr_i.rd))):
                        io.issue_ack_o = U.w(1)(1)
            # we can also issue the instruction under the following two circumstances:
            # we can do this even if we are stalled or no functional unit is ready (as we don't need one)
            # the decoder needs to make sure that the instruction is marked as valid when it does not
            # need any functional unit or if an exception occurred previous to the execute stage.
            # 1. we already got an exception
            with when(io.issue_instr_i.ex.valid):
                issue_ack_o = U.w(1)(1)
            # 2. it is an instruction which does not need any functional unit
            with when(io.issue_instr_i.fu == fu_t.NONE):
                issue_ack_o = U.w(1)(1)
        # after a multiplication was issued we can only issue another multiplication
        # otherwise we will get contentions on the fixed latency bus
        with when(mult_valid_q and io.issue_instr_i.fu != fu_t.MULT):
            issue_ack_o = U.w(1)(0)

        # ----------------------
        # Integer Register File
        # ----------------------
        rdata = Wire(Vec(2, U.w(64)))
        raddr_pack = Wire(Vec(2, U.w(5)))

        # pack signals
        waddr_pack = Wire(Vec(NR_COMMIT_PORTS,U.w(5)))
        wdata_pack = Wire(Vec(NR_COMMIT_PORTS,U.w(64)))
        we_pack = Wire(U.w(NR_COMMIT_PORTS))
        raddr_pack <<= CatBits(io.issue_instr_i.rs2[4:0], io.issue_instr_i.rs1[4:0])
        for i in range(NR_COMMIT_PORTS): #TODO:gen_write_back_port
            waddr_pack[i] = io.waddr_i[i]
            wdata_pack[i] = io.wdata_i[i]
            we_pack[i]    = io.we_gpr_i[i]

        def ariane_regfile(self,DATA_WIDTH = 64,NR_READ_PORTS  = 2,NR_WRITE_PORTS = NR_COMMIT_PORTS,ZERO_REG_ZERO = 1):
            class i_ariane_regfile(Module):
                io = IO(
                    test_en_i = Input(U.w(1)(0)),
                    raddr_i =   Input(raddr_pack) ,
                    rdata_o =   Output(rdata)      ,
                    waddr_i =   Input(waddr_pack) ,
                    wdata_i =   Input(wdata_pack) ,
                    we_i    =   Input(we_pack)    ,
                    # TODO:*
                )
            return i_ariane_regfile()

        # -----------------------------
        # Floating-Point Register File
        # -----------------------------
        fprdata = Wire(Vec(3, U.w(FLEN)))

        # pack signals
        fp_raddr_pack = Wire(Vec(3, U.w(5)))
        fp_wdata_pack = Wire(Vec(NR_COMMIT_PORTS, U.w(64)))

        with when(FP_PRESENT) : #TODO: float_regfile_gen
            fp_raddr_pack <<= CatBits(io.issue_instr_i.result[4:0], io.issue_instr_i.rs2[4:0], io.issue_instr_i.rs1[4:0])
            for i in range(NR_COMMIT_PORTS): #TODO: gen_fp_wdata_pack
                fp_wdata_pack[i] = CatBits(io.wdata_i[i][FLEN-1:0])

            def ariane_regfile(self,DATA_WIDTH = FLEN,NR_READ_PORTS  = 3,NR_WRITE_PORTS = NR_COMMIT_PORTS,ZERO_REG_ZERO = 0):
                class i_ariane_fp_regfile(Module):
                    io = IO(
                        test_en_i = Input(U.w(1)(0)),
                        raddr_i =   Input(fp_raddr_pack) ,
                        rdata_o =   Output(fprdata)      ,
                        waddr_i =   Input(waddr_pack) ,
                        wdata_i =   Input(wdata_pack) ,
                        we_i    =   Input(we_fpr_i)    ,
                        # TODO:*
                    )
                return i_ariane_fp_regfile()

        with otherwise(): #TODO: no_fpr_gen
            fprdata = CatVecL2H(Vec(3,U.w(FLEN)))

        operand_a_regfile <<= Mux(is_rs1_fpr(io.issue_instr_i.op), fprdata[0], rdata[0])
        operand_b_regfile <<= Mux(is_rs2_fpr(io.issue_instr_i.op), fprdata[1], rdata[1])
        operand_c_regfile <<= fprdata[2]

        # ----------------------
        # Registers (ID <-> EX)
        # ----------------------
        #always_ff @(posedge clk_i or negedge rst_ni) begin
        with when(not io.rst_ni):
            operand_a_q              <<= CatVecL2H(U.w(64))
            operand_b_q              <<= CatVecL2H(U.w(64))
            imm_q                    <<= U(0)
            fu_q                     <<= fu_t.NONE
            operator_q               <<= fu_t.ADD
            trans_id_q               <<= U(0)
            io.pc_o                  <<= U(0)
            io.is_compressed_instr_o <<= U.w(1)(0)
            io.branch_predict_o      <<= CatBits(*(cf_t * [U(0)]), U.w(64)(0))
        with otherwise():
            operand_a_q              <<= operand_a_n
            operand_b_q              <<= operand_b_n
            imm_q                    <<= imm_n
            fu_q                     <<= fu_n
            operator_q               <<= operator_n
            trans_id_q               <<= trans_id_n
            io.pc_o                  <<= io.issue_instr_i.pc
            io.is_compressed_instr_o <<= io.issue_instr_i.is_compressed
            io.branch_predict_o      <<= io.issue_instr_i.bp

        #TODO pragma translate_off
        if not define('VERILATOR'):
            counter = RegInit(U.w(1)(0))
            counter <<= counter + U(1)
            with when(counter and branch_valid_q):
                assert(not isunknown(operand_a_q) and not isunknown(operand_b_q))
            with otherwise():
                print("Got unknown value in one of the operands")

        #TODO pragma translate_on

  return issue_read_operands()


if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(issue_read_operands(2)), "issue_read_operands.fir"))

## ********** 黄智权、韩耀华 9.8 End ********** ##