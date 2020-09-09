#***********董妙君 9.9 Begin***********#            

from pyhcl import *
import ariane_pkg::*;
from enum import Enum
from instr_queue import *

ariane_cfg_t=Bundle(
    RASDepth=U.w(32),
    BTBEntries=U.w(32),
    BHTEntries=U.w(32),
    # PMAs
    NrNonIdempotentRules=U.w(32),               # Number of non idempotent rules
    NonIdempotentAddrBase=Reg(Vec(16,U.w(64))), # base which needs to match
    NonIdempotentLength=Reg(Vec(16,U.w(64))),   # bit mask which bits to consider when matching the rule
    NrExecuteRegionRules=U.w(32),               # Number of regions which have execute property
    ExecuteRegionAddrBase=Reg(Vec(16,U.w(64))), # base which needs to match
    ExecuteRegionLength=Reg(Vec(16,U.w(64))),   # bit mask which bits to consider when matching the rule
    NrCachedRegionRules=U.w(32),                # Number of regions which have cached property
    CachedRegionAddrBase=Reg(Vec(16,U.w(64))),  # base which needs to match
    CachedRegionLength=Reg(Vec(16,U.w(64))),    # bit mask which bits to consider when matching the rule
    # cache config
    Axi64BitCompliant=U.w(1),                   # set to 1 when using in conjunction with 64bit AXI bus adapter
    SwapEndianess=U.w(1),                       # set to 1 to swap endianess inside L1.5 openpiton adapter
    #
    DmBaseAddress=U.w(64)                       # offset of the debug module
)

btb_prediction_t = Bundle(
    valid=Reg(U.w(1)),
    target_address=U.w(64)
)

btb_prediction_t_ = Bundle(
    valid=Reg(Vec(2,U.w(1))),
    target_address=Reg(Vec(2,U.w(64)))
)

bht_prediction_t = Bundle(
    valid=Reg(U.w(1)),
    taken=Reg(U.w(1))
)

bht_prediction_t_ = Bundle(
    valid=Reg(Vec(U.w(1))),
    taken=Reg(Vec(U.w(1)))
)

def frontend(ArianeCfg: ariane_cfg_t):
    class cf_t(Enum):
        NoCF    # No control flow prediction
        Branch  # Branch
        Jump    # Jump to address from immediate
        JumpR   # Jump to address from registers
        Return  # Return Address Prediction

    bht_update_t=Bundle(
        valid=U.w(1),
        pc=U.w(64),          # update at PC
        taken=U.w(1)
    )

    btb_update_t=Bundle(
        valid=U.w(1),        
        pc=U.w(64),          # update at PC
        target_address=U.w(64)
    )

    ras_t=Bundle(
        valid=U.w(1), 
        ra=U.w(64)
    )

    class Frontend(Module):
        bp_resolve_t=Bundle(
            valid=U.w(1),           # prediction with all its values is valid
            pc=U.w(64),             # PC of predict or mis-predict
            target_address=U.w(64), # target address at which to jump, or not
            is_mispredict=U.w(1),   # set if this was a mis-predict
            is_taken=U.w(1),        # branch is taken
            cf_type=cf_t()          # Type of control flow change
        )

        icache_dreq_i_t=Bundle(
            req=U.w(1),                    # we request a new word
            kill_s1=U.w(1),                # kill the current request
            kill_s2=U.w(1),                # kill the last request
            vaddr=U.w(64)                  # 1st cycle: 12 bit index is taken for lookup
        )

        exception_t=Bundle(
            cause=U.w(64),                  # cause of exception
            tval=U.w(64),                   # additional information of causing exception (e.g.: instruction causing it),
                                            # address of LD/ST fault
            valid=U.w(1) 
        )

        icache_dreq_o_t=Bundle(
            ready=U.w(1),                  # icache is ready
            valid=U.w(1),                  # signals a valid read
            data=U.w(64),                  # 2+ cycle out: tag
            vaddr=U.w(64),                 # virtual address out
            ex=exception_t()               # we've encountered an exception
        )

        branchpredict_sbe_t=Bundle(
            cf=cf_t(),                      # type of control flow prediction
            predict_address=U.w(64)         # target address at which to jump, or not
        )

        fetch_entry_t=Bundle(
            address=U.w(64),                        # the address of the instructions from below
            instruction=U.w(32),                    # instruction word
            branch_predict=branchpredict_sbe_t(),   # this field contains branch prediction information regarding the forward branch path
            ex=exception_t()                        # this field contains exceptions which might have happened earlier, e.g.: fetch exceptions
        )

        io=IO(
            clk_i=Input(Bool),                      # Clock
            rst_ni=Input(Bool),                     # Asynchronous reset active low
            flush_i=Input(Bool),                    # flush request for PCGEN
            flush_bp_i=Input(Bool),                 # flush branch prediction
            debug_mode_i=Input(Bool),

            # global input
            boot_addr_i=Input(U.w(64)),

            # Set a new PC
            # mispredict
            resolved_branch_i=Input(bp_resolve_t),  # from controller signaling a branch_predict -> update BTB
    
            # from commit, when flushing the whole pipeline
            set_pc_commit_i=Input(Bool),    # Take the PC from commit stage
            pc_commit_i=Input(U.w(64)),     # PC of instruction in commit stage

            # CSR input
            epc_i=Input(U.w(64)),           # exception PC which we need to return to
            eret_i=Input(Bool),             # return from exception
            trap_vector_base_i=Input(U.w(64)), # base of trap vector
            ex_valid_i=Input(Bool),         # exception is valid - from commit
            set_debug_pc_i=Input(Bool),     # jump to debug address

            # Instruction Fetch
            icache_dreq_o=Output(icache_dreq_i_t),
            icache_dreq_i=Input(icache_dreq_o_t),

            # instruction output port -> to processor back-end
            fetch_entry_o=Output(fetch_entry_t),        # fetch entry containing all relevant data for the ID stage
            fetch_entry_valid_o=Output(Bool),           # instruction in IF is valid
            fetch_entry_ready_i=Input(Bool)             # ID acknowledged this instruction
        )


        # Instruction Cache Registers, from I$
        icache_data_q=Reg(U.w(64))
        icache_valid_q=Reg(U.w(1))
        icache_ex_valid_q=Reg(U.w(1))
        icache_vaddr_q=U.w(64)
        instr_queue_ready=Reg(U.w(1))
        instr_queue_consumed=Reg(U.w(2))
        # upper-most branch-prediction from last cycle
        btb_q=btb_prediction_t()
        bht_q=bht_prediction_t()
    
        # instruction fetch is ready
        if_ready=Reg(U.w(1))
        npc_d=Reg(U.w(64)) # next PC
        npc_q=Reg(U.w(64)) # next PC

        # indicates whether we come out of reset (then we need to load boot_addr_i)
        npc_rst_load_q=Reg(U.w(1))

        replay=Reg(U.w(1))
        replay_addr=Reg(U.w(64))

        # shift amount
        shamt=U.w(0)                #当INSTR_PER_FETCH=2，$clog2(ariane_pkg::INSTR_PER_FETCH)=1,此时shamt位宽为0？
        # address will always be 16 bit aligned, make this explicit here
        assign shamt = io.icache_dreq_i.vaddr[1:1]

        # -----------------------
        # Ctrl Flow Speculation
        # -----------------------
        # RVI ctrl flow prediction
        rvi_return=Reg(U.w(2))
        rvi_call=Reg(U.w(2))
        rvi_branch=Reg(U.w(2))
        rvi_jalr=Reg(U.w(2))
        rvi_jump=Reg(U.w(2))
        rvi_imm=Reg(Vec(2,U.w(64)))
        # RVC branching
        rvc_branch=Reg(U.w(2))
        rvc_jump=Reg(U.w(2))
        rvc_jr=Reg(U.w(2))
        rvc_return=Reg(U.w(2))
        rvc_jalr=Reg(U.w(2))
        rvc_call=Reg(U.w(2))
        rvc_imm=Reg(Vec(2,U.w(64)))
        # re-aligned instruction and address (coming from cache - combinationally)
        instr=Reg(Vec(2,U.w(32)))
        addr=Reg(Vec(2,U.w(64)))
        instruction_valid=Reg(U.w(2))
        # BHT, BTB and RAS 
        bht_prediction=bht_prediction_t_()
        btb_prediction=btb_prediction_t_()
        bht_prediction_shifted=bht_prediction_t_()
        btb_prediction_shifted=btb_prediction_t_()
        ras_predict=ras_t()


        # branch-predict update
        is_mispredict=Reg(U.w(1))
        ras_push, ras_pop=Reg(U.w(1))
        ras_update=Reg(U.w(64))

        # Instruction FIFO
        predict_address=Reg(U.w(64))
        cf_type=Vec(2,3)
        taken_rvi_cf=Reg(U.w(2))
        taken_rvc_cf=Reg(U.w(2))
    
        serving_unaligned=Reg(U.w(1))
        # Re-align instructions
        i_instr_realign=instr_realign()
        i_instr_realign.io.clk_i<<=io.clk_i
        i_instr_realign.io.rst_ni<<=io.rst_ni
        i_instr_realign.io.flush_i<<=io.icache_dreq_o.kill_s2
        i_instr_realign.io.valid_i<<=io.icache_valid_q
        i_instr_realign.io.serving_unaligned_o<<=io.serving_unaligned
        i_instr_realign.io.address_i<<=io.icache_vaddr_q
        i_instr_realign.io.data_i<<=io.icache_data_q
        i_instr_realign.io.valid_o<<=io.instruction_valid
        i_instr_realign.io.addr_o<<=io.addr
        i_instr_realign.io.instr_o<<=io.instr
    
        # --------------------
        # Branch Prediction
        # --------------------
        # select the right branch prediction result
        # in case we are serving an unaligned instruction in instr[0] we need to take
        # the prediction we saved from the previous fetch
        if serving_unaligned:
            bht_prediction_shifted.valid[0]=bht_q.valid
            bht_prediction_shifted.taken[0]=bht_q.taken
            btb_prediction_shifted.valid[0]=btb_q.valid
            btb_prediction_shifted.target_address[0]=btb_q.target_address

        else:
            bht_prediction_shifted.valid[0]=bht_prediction.valid[0]
            bht_prediction_shifted.taken[0]=bht_prediction.taken[0]
            btb_prediction_shifted.valid[0]=btb_prediction.valid[0]
            btb_prediction_shifted.target_address[0]=btb_prediction.target_address[0]
        # for all other predictions we can use the generated address to index
        # into the branch prediction data structures
        for i in range(0:INSTR_PER_FETCH+1)
            bht_prediction_shifted.valid[i] = bht_prediction.valid[addr[i][1:1]]  #当INSTR_PER_FETCH=2，$clog2(INSTR_PER_FETCH)=1
            bht_prediction_shifted.taken[i] = bht_prediction.taken[addr[i][1:1]]
            btb_prediction_shifted.valid[i] = btb_prediction.valid[addr[i][1:1]]
            btb_prediction_shifted.target_address[i] = btb_prediction.target_address[addr[i][1:1]]
        # for the return address stack it doens't matter as we have the
        # address of the call/return already
        bp_valid=Reg(U.w(1))

        is_branch=Reg(U.w(2))
        is_call=Reg(U.w(2))
        is_jump=Reg(U.w(2))
        is_return=Reg(U.w(2))
        is_jalr=Reg(U.w(2))

        for i in range(0:INSTR_PER_FETCH+1): 
            # branch history table -> BHT
            assign is_branch[i] =  instruction_valid[i] & (rvi_branch[i] | rvc_branch[i])
            # function calls -> RAS
            assign is_call[i] = instruction_valid[i] & (rvi_call[i] | rvc_call[i])
            # function return -> RAS
            assign is_return[i] = instruction_valid[i] & (rvi_return[i] | rvc_return[i])
            # unconditional jumps with known target -> immediately resolved
            assign is_jump[i] = instruction_valid[i] & (rvi_jump[i] | rvc_jump[i])
            # unconditional jumps with unknown target -> BTB
            assign is_jalr[i] = instruction_valid[i] & ~is_return[i] & ~is_call[i] & (rvi_jalr[i] | rvc_jalr[i] | rvc_jr[i])

        # taken/not taken
        taken_rvi_cf = U(0)
        taken_rvc_cf = U(0)
        predict_address = U(0)

        CT_F={'NoCF':U.w(3)(0),'Branch':U.w(3)(1),'Jump':U.w(3)(2),'JumpR':U.w(3)(3),'Return':U.w(3)(4)}

        for  i in range(0:INSTR_PER_FETCH+1):
            cf_type[i] = CT_F['NoCF']       #ariane_pkg::NoCF; #不是很明白NoCF应该是ct_t的成员，为什么可以直接调用呢？
        
        ras_push = U(0)
        ras_pop = U(0)
        ras_update = U(0)

        # lower most prediction gets precedence
        for i in range(INSTR_PER_FETCH - 1:-1:-1):         #begin
            with when(CatBits(is_branch[i], is_return[i], is_jump[i], is_jalr[i])==U(0)):
                # regular instruction e.g.: no branch

            # unconditional jump to register, we need the BTB to resolve this
            with elsewhen(CatBits(is_branch[i], is_return[i], is_jump[i], is_jalr[i])==U(1)):
                ras_pop = U(0)
                ras_push = U(0)
                with when(btb_prediction_shifted[i].valid):
                    predict_address = btb_prediction_shifted[i].target_address
                    cf_type[i] = CT_F['JumpR']

            # its an unconditional jump to an immediate
            with elsewhen(CatBits(is_branch[i], is_return[i], is_jump[i], is_jalr[i])==U(2)):
                ras_pop = U(0)
                ras_push = U(0)
                taken_rvi_cf[i] = rvi_jump[i]
                taken_rvc_cf[i] = rvc_jump[i]
                cf_type[i] = CT_F['Jump']

            # return
            with elsewhen(CatBits(is_branch[i], is_return[i], is_jump[i], is_jalr[i])==U(4)):
                # make sure to only alter the RAS if we actually consumed the instruction
                ras_pop = ras_predict.valid & instr_queue_consumed[i]
                ras_push = U(0)
                predict_address = ras_predict.ra
                cf_t    ype[i] = CT_F['Return']

            # branch prediction
            with elsewhen(CatBits(is_branch[i], is_return[i], is_jump[i], is_jalr[i])==U(8)):
                ras_pop = U(0)
                ras_push = U(0)
                # if we have a valid dynamic prediction use it
                if bht_prediction_shifted.valid[i]:
                    taken_rvi_cf[i] = rvi_branch[i] & bht_prediction_shifted.taken[i]
                    taken_rvc_cf[i] = rvc_branch[i] & bht_prediction_shifted.taken[i]
                # otherwise default to static prediction
                else:
                    # set if immediate is negative - static prediction
                    taken_rvi_cf[i] = rvi_branch[i] & rvi_imm[i][U(63)]
                    taken_rvc_cf[i] = rvc_branch[i] & rvc_imm[i][U(63)]
                if (taken_rvi_cf[i] or taken_rvc_cf[i]):
                    cf_type[i] = CT_F['Branch']

            with otherwise():
                # default: $error("Decoded more than one control flow");

            # if this instruction, in addition, is a call, save the resulting address
            # but only if we actually consumed the address
            if (is_call[i]):
                ras_push = instr_queue_consumed[i]
                ras_update = addr[i] + Mux(rvc_call[i],2,4)
            
            # calculate the jump target address
            if (taken_rvc_cf[i] or taken_rvi_cf[i]):
                predict_address = addr[i] + Mux(taken_rvc_cf[i],rvc_imm[i],rvi_imm[i])
            
        # or reduce struct
        bp_valid = U.w(1)(0)
        for i in range(0:INSTR_PER_FETCH+1):
            bp_valid = bp_valid | (cf_type[i] != CT_F['NoCF'])
        
        is_mispredict = io.resolved_branch_i.valid & io.resolved_branch_i.is_mispredict

        # Cache interface
        io.icache_dreq_o.req = instr_queue_ready
        if_ready = io.icache_dreq_i.ready & instr_queue_ready
        # We need to flush the cache pipeline if:
        # 1. We mispredicted
        # 2. Want to flush the whole processor front-end
        # 3. Need to replay an instruction because the fetch-fifo was full
        io.icache_dreq_o.kill_s1 = is_mispredict | io.flush_i | replay
        # if we have a valid branch-prediction we need to only kill the last cache request
        # also if we killed the first stage we also need to kill the second stage (inclusive flush)
        io.icache_dreq_o.kill_s2 = io.icache_dreq_o.kill_s1 | bp_valid

        #Update Control Flow Predictions
        bht_update=bht_update_t()
        btb_update=btb_update_t()

        bht_update.valid = io.resolved_branch_i.valid & (io.resolved_branch_i.cf_type == CT_F['Branch'])
        bht_update.pc    = io.resolved_branch_i.pc
        bht_update.taken = io.resolved_branch_i.is_taken
        # only update mispredicted branches e.g. no returns from the RAS
        btb_update.valid = io.resolved_branch_i.valid & io.resolved_branch_i.is_mispredict
                            & (io.resolved_branch_i.cf_type == CT_F['NoCF'])
        btb_update.pc    = io.resolved_branch_i.pc
        btb_update.target_address = io.resolved_branch_i.target_address

#***********董妙君 9.9 End***********#            

#***********余宛书 9.8 Begin***********#    
        # -------------------
        # Next PC
        # -------------------
        # next PC (NPC) can come from (in order of precedence):
        # 0. Default assignment/replay instruction
        # 1. Branch Predict taken
        # 2. Control flow change request (misprediction)
        # 3. Return from environment call
        # 4. Exception/Interrupt
        # 5. Pipeline Flush because of CSR side effects
        # Mis-predict handling is a little bit different
        # select PC a.k.a PC Gen
        #always_comb begin : npc_select 表示设计组合逻辑电路
        fetch_address=Reg(U.w(64))
        # check whether we come out of reset
        # this is a workaround. some tools have issues
        # having boot_addr_i in the asynchronous
        # reset assignment to npc_q, even though
        # boot_addr_i will be assigned a constant
        # on the top-level.
        if npc_rst_load_q:
            npc_d <<= io.boot_addr_i[63:0]
            fetch_address <<= io.boot_addr_i[63:0]
        else:
            fetch_address = npc_q
            # keep stable by default
            npc_d = npc_q
        
        # 0. Branch Prediction
        if bp_valid:
            fetch_address = predict_address
            npc_d = predict_address

        # 1. Default assignment
        if if_ready:
            npc_d = CatBits(fetch_address[63:2], U.w(2)(0))  + U(4)
        # 2. Replay instruction fetch
        if replay:
            npc_d = replay_addr
        # 3. Control flow change request
        if is_mispredict:
            npc_d <<= io.resolved_branch_i.target_address
        # 4. Return from environment call
        if io.eret_i:
            npc_d <<= io.epc_i
        # 5. Exception/Interrupt
        if io.ex_valid_i:
            npc_d <<= io.trap_vector_base_i
        # 6. Pipeline Flush because of CSR side effects
        # On a pipeline flush start fetching from the next address
        # of the instruction in the commit stage
        # we came here from a flush request of a CSR instruction or AMO,
        # as CSR or AMO instructions do not exist in a compressed form
        # we can unconditionally do PC + 4 here
        # TODO(zarubaf) This adder can at least be merged with the one in the csr_regfile stage
        if io.set_pc_commit_i:
            npc_d <<= io.pc_commit_i + U.w(64)(4) # + {{riscv::VLEN-3{1'b0}}, 3'b100}
        # 7. Debug
        # enter debug on a hard-coded base-address
        if io.set_debug_pc_i:
            npc_d = ArianeCfg.DmBaseAddress[63:0] + dm.HaltAddress[63:0]
            io.icache_dreq_o.vaddr = fetch_address
        #end

        icache_data = U.w(64)
        # re-align the cache line
        icache_data = io.icache_dreq_i.data >> CatBits(shamt, U.w(4)(0))

        #always_ff @(posedge clk_i or negedge rst_ni) begin
        if ~io.rst_ni:
            npc_rst_load_q = U.w(1)(1)
            npc_q = U(0)
            icache_data_q = U(0)
            icache_valid_q = U.w(1)(0)
            icache_vaddr_q = U(0)
            icache_ex_valid_q = U.w(1)(0)
            btb_q = U(0)
            bht_q = U(0)
        else:
            npc_rst_load_q = U.w(1)(0)
            npc_q = npc_d
            icache_valid_q <<= io.icache_dreq_i.valid
            if io.icache_dreq_i.valid:
                icache_data_q = icache_data
                icache_vaddr_q = io.icache_dreq_i.vaddr
                icache_ex_valid_q = io.icache_dreq_i.ex
                # save the uppermost prediction
                btb_q.valid = btb_prediction.valid[1]
                btb_q.target_address = btb_prediction.target_address[1]
                bht_q.valid = bht_prediction.valid[1]
                bht_q.taken = bht_prediction.taken[1]
        #end

        #ras
        i_ras = ras(ArianeCfg.RASDepth)
        i_ras.io.clk_i <<= io.clk_i
        i_ras.io.rst_ni <<= io.rst_ni
        i_ras.io.flush_i <<= io.flush_bp_i
        i_ras.io.push_i <<= io.ras_push
        i_ras.io.pop_i <<= io.clk_i.ras_pop
        i_ras.io.data_i <<= io.ras_update
        i_ras.io.data_o <<= io.ras_predict

        #btb
        i_btb = btb(ArianeCfg.BTBEntries)
        i_btb.io.clk_i <<= io.clk_i
        i_btb.io.rst_ni <<= io.rst_ni
        i_btb.io.flush_i <<= io.flush_bp_i
        i_btb.io.debug_mode_i <<= io.debug_mode_i
        i_btb.io.vpc_i <<= io.icache_vaddr_q
        i_btb.io.btb_update_i <<= io.btb_update
        i_btb.io.btb_prediction_o <<= io.btb_prediction
        
        #bht
        i_bht = bht(ArianeCfg.BHTEntries)
        i_bht.io.clk_i <<= io.clk_i
        i_bht.io.rst_ni <<= io.rst_ni
        i_bht.io.flush_i <<= io.flush_bp_i
        i_bht.io.debug_mode_i <<= io.debug_mode_i
        i_bht.io.vpc_i <<= io.icache_vaddr_q
        i_bht.io.bht_update_i <<= io.bht_update
        i_bht.io.bht_prediction_o <<= io.bht_prediction
        
        # we need to inspect up to INSTR_PER_FETCH instructions for branches
        # and jumps
        for i in range(0:3): 
            #begin : gen_instr_scan
            i_instr_scan = instr_scan()
            i_instr_scan.io.instr_i <<= instr[i]
            i_instr_scan.io.rvi_return_o <<= rvi_return[i]
            i_instr_scan.io.rvi_call_o <<= rvi_call[i]
            i_instr_scan.io.rvi_branch_o <<= rvi_branch[i]
            i_instr_scan.io.rvi_jalr_o <<= rvi_jalr[i]
            i_instr_scan.io.rvi_imm_o <<= rvi_imm[i]
            i_instr_scan.io.rvc_branch_o <<= rvc_branch[i]
            i_instr_scan.io.rvc_jump_o <<= rvc_jump[i]
            i_instr_scan.io.rvc_jr_o <<= rvc_jr[i]
            i_instr_scan.io.rvc_return_o <<= rvc_return[i]
            i_instr_scan.io.rvc_jalr_o <<= rvc_jalr[i]
            i_instr_scan.io.rvc_call_o <<= rvc_call[i]
            i_instr_scan.io.rvc_imm_o <<= rvc_imm[i]
            #end

        i_instr_queue = instr_queue()
        i_instr_queue.io.clk_i <<= io.clk_i
        i_instr_queue.io.rst_ni <<= io.rst_ni
        i_instr_queue.io.flush_i <<= io.flush_i
        i_instr_queue.io.instr_i <<= instr  # from re-aligner
        i_instr_queue.io.addr_i <<= addr    # from re-aligner
        i_instr_queue.io.exception_i <<= icache_ex_valid_q   # from I$
        i_instr_queue.io.predict_address_i <<= predict_address
        i_instr_queue.io.cf_type_i <<= cf_type
        i_instr_queue.io.valid_i <<= instruction_valid    # from re-aligner
        i_instr_queue.io.consumed_o <<= instr_queue_consumed
        i_instr_queue.io.ready_o <<= instr_queue_ready
        i_instr_queue.io.replay_o <<= io.replay
        i_instr_queue.io.replay_addr_o <<= replay_addr
        i_instr_queue.io.fetch_entry_o <<= io.fetch_entry_o  # to back-end
        i_instr_queue.io.fetch_entry_valid_o <<= io.fetch_entry_valid_o  # to back-end
        i_instr_queue.io.fetch_entry_ready_i <<= io.fetch_entry_ready_i  # to back-end


        # pragma translate_off
        '''
        `ifndef VERILATOR
            initial begin
                assert (FETCH_WIDTH == 32 || FETCH_WIDTH == 64) else $fatal("[frontend] fetch width != not supported");
            end
        `endif
        '''
        #if FETCH_WIDTH != 32 and FETCH_WIDTH != 64:
        with when(FETCH_WIDTH != 32 and FETCH_WIDTH != 64):
            assert FETCH_WIDTH == 32 or FETCH_WIDTH == 64, print("[frontend] fetch width != not supported")  
        # pragma translate_on

#***********余宛书 9.9 End***********#    
