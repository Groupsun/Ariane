#***********董妙君 8.31 Begin***********#            

from pyhcl import *
import ariane_pkg::*;

class fronted(Module):
    # ????  parameter ariane_pkg::ariane_cfg_t ArianeCfg = ariane_pkg::ArianeDefaultConfig

    io=IO(
        clk_i=Input(Bool), # Clock
        rst_ni=Input(Bool),# Asynchronous reset active low
        flush_i=Input(Bool),# flush request for PCGEN
        flush_bp_i=Input(Bool),# flush branch prediction
        debug_mode_i=Input(Bool),
        
        # global input
        boot_addr_i=Input(U.w(64)),

        # Set a new PC
        # mispredict
        input  bp_resolve_t        resolved_branch_i,  # from controller signaling a branch_predict -> update BTB
  
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
        output icache_dreq_i_t     icache_dreq_o,
        input  icache_dreq_o_t     icache_dreq_i,

        # instruction output port -> to processor back-end
        output fetch_entry_t       fetch_entry_o,       # fetch entry containing all relevant data for the ID stage
        fetch_entry_valid_o=Output(Bool), # instruction in IF is valid
        fetch_entry_ready_i=Input(Bool)  # ID acknowledged this instruction
    )


    # Instruction Cache Registers, from I$
    icache_data_q=Reg(U.w(64)),
    icache_valid_q=Reg(U.w(1)),
    icache_ex_valid_q=Reg(U.w(1)),
    icache_vaddr_q=U.w(64),
    instr_queue_ready=Reg(U.w(1)),
    instr_queue_consumed=Reg(U.w(2)),
    # upper-most branch-prediction from last cycle
    btb_prediction_t        btb_q;
    bht_prediction_t        bht_q;
    # instruction fetch is ready
    if_ready=Reg(U.w(1)),
    npc_d=Reg(U.w(64)), # next PC
    npc_q=Reg(U.w(64)), # next PC

    # indicates whether we come out of reset (then we need to load boot_addr_i)
    npc_rst_load_q=Reg(U.w(1)),

    replay=Reg(U.w(1)),
    replay_addr=Reg(U.w(64)),

    # shift amount
    logic [$clog2(ariane_pkg::INSTR_PER_FETCH)-1:0] shamt;
    # address will always be 16 bit aligned, make this explicit here
    assign shamt = icache_dreq_i.vaddr[$clog2(ariane_pkg::INSTR_PER_FETCH):1];

    # -----------------------
    # Ctrl Flow Speculation
    # -----------------------
    # RVI ctrl flow prediction
    rvi_return=Reg(U.w(2)), 
    rvi_call=Reg(U.w(2)), 
    rvi_branch=Reg(U.w(2)),
    rvi_jalr=Reg(U.w(2)), 
    rvi_jump=Reg(U.w(2)),
    rvi_imm=Reg(Vec(2,U.w(64))),
    # RVC branching
    rvc_branch=Reg(U.w(2)), 
    rvc_jump=Reg(U.w(2)), 
    rvc_jr=Reg(U.w(2)), 
    rvc_return=Reg(U.w(2)),
    rvc_jalr=Reg(U.w(2)), 
    rvc_call=Reg(U.w(2)),
    rvc_imm=Reg(Vec(2,U.w(64))),
    # re-aligned instruction and address (coming from cache - combinationally)
    instr=Reg(Vec(2,U.w(32))),
    addr=Reg(Vec(2,U.w(64))),
    instruction_valid=Reg(U.w(2)),
    # BHT, BTB and RAS prediction
    bht_prediction_t [INSTR_PER_FETCH-1:0] bht_prediction;
    btb_prediction_t [INSTR_PER_FETCH-1:0] btb_prediction;
    bht_prediction_t [INSTR_PER_FETCH-1:0] bht_prediction_shifted;
    btb_prediction_t [INSTR_PER_FETCH-1:0] btb_prediction_shifted;
    ras_t            ras_predict;

    # branch-predict update
    is_mispredict=Reg(U.w(1)),
    ras_push, ras_pop=Reg(U.w(1)),
    ras_update=Reg(U.w(64)),

    # Instruction FIFO
    predict_address=Reg(U.w(64)),
    cf_t  [ariane_pkg::INSTR_PER_FETCH-1:0] cf_type;
    taken_rvi_cf=Reg(U.w(2)),
    taken_rvc_cf=Reg(U.w(2)),
 
    logic serving_unaligned;
    // Re-align instructions
    instr_realign i_instr_realign (
      .clk_i               ( clk_i                 ),
      .rst_ni              ( rst_ni                ),
      .flush_i             ( icache_dreq_o.kill_s2 ),
      .valid_i             ( icache_valid_q        ),
      .serving_unaligned_o ( serving_unaligned     ),
      .address_i           ( icache_vaddr_q        ),
      .data_i              ( icache_data_q         ),
      .valid_o             ( instruction_valid     ),
      .addr_o              ( addr                  ),
      .instr_o             ( instr                 )
    );
    # --------------------
    # Branch Prediction
    # --------------------
    # select the right branch prediction result
    # in case we are serving an unaligned instruction in instr[0] we need to take
    # the prediction we saved from the previous fetch
    if serving_unaligned:
        assign bht_prediction_shifted[0]=bht_q
        btb_prediction_shifted[0]=btb_q
    else:
        assign bht_prediction_shifted[0]=bht_prediction[0]
        btb_prediction_shifted[0]=btb_prediction[0]
    # for all other predictions we can use the generated address to index
    # into the branch prediction data structures
    for i in range(0:INSTR_PER_FETCH+1)
    # ??begin : gen_prediction_address
        assign bht_prediction_shifted[i] = bht_prediction[addr[i][$clog2(INSTR_PER_FETCH):1]];
        assign btb_prediction_shifted[i] = btb_prediction[addr[i][$clog2(INSTR_PER_FETCH):1]];
    # ??end
    # for the return address stack it doens't matter as we have the
    # address of the call/return already
    bp_valid=Reg(U.w(1)),

    is_branch=Reg(U.w(2)),
    is_call=Reg(U.w(2)),
    is_jump=Reg(U.w(2)),
    is_return=Reg(U.w(2)),
    is_jalr=Reg(U.w(2)),

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
    #?? always_comb begin
        taken_rvi_cf = '0; 
        taken_rvc_cf = '0;
        predict_address = '0;

        for  i in range(0:INSTR_PER_FETCH+1)  
            cf_type[i] = ariane_pkg::NoCF;
            ras_push = 1'b0;
            ras_pop = 1'b0;
            ras_update = '0;

        # lower most prediction gets precedence
        for i in range(INSTR_PER_FETCH - 1:-1:-1)         #begin
            unique case ({is_branch[i], is_return[i], is_jump[i], is_jalr[i]})
                4'b0000:;         # regular instruction e.g.: no branch

                # unconditional jump to register, we need the BTB to resolve this
                4'b0001: begin
                    ras_pop = U.w(1)(0)
                    ras_push = U.w(1)(0)
                    if (btb_prediction_shifted[i].valid):
                        predict_address = btb_prediction_shifted[i].target_address
                        cf_type[i] = ariane_pkg::JumpR
                end   

                # its an unconditional jump to an immediate
                4'b0010: begin
                    ras_pop = U.w(1)(0)
                    ras_push = U.w(1)(0)
                    taken_rvi_cf[i] = rvi_jump[i]
                    taken_rvc_cf[i] = rvc_jump[i]
                    cf_type[i] = ariane_pkg::Jump
                end

                # return
                4'b0100: begin
                    // make sure to only alter the RAS if we actually consumed the instruction
                    ras_pop = ras_predict.valid & instr_queue_consumed[i];
                    ras_push = 1'b0;
                    predict_address = ras_predict.ra;
                    cf_t    ype[i] = ariane_pkg::Return;
                end

                # branch prediction
                4'b1000: begin
                    ras_pop = U.w(1)(0)
                    ras_push = U.w(1)(0)
                    # if we have a valid dynamic prediction use it
                    if bht_prediction_shifted[i].valid:
                        taken_rvi_cf[i] = rvi_branch[i] & bht_prediction_shifted[i].taken
                        taken_rvc_cf[i] = rvc_branch[i] & bht_prediction_shifted[i].taken
                    # otherwise default to static prediction
                    else:
                        # set if immediate is negative - static prediction
                        taken_rvi_cf[i] = rvi_branch[i] & rvi_imm[i][riscv::VLEN-1];
                        taken_rvc_cf[i] = rvc_branch[i] & rvc_imm[i][riscv::VLEN-1];
                
                    if (taken_rvi_cf[i] || taken_rvc_cf[i]) cf_type[i] = ariane_pkg::Branch;
                end
            
                default:
                    // default: $error("Decoded more than one control flow");
            endcase
                # if this instruction, in addition, is a call, save the resulting address
                # but only if we actually consumed the address
                if (is_call[i]):
                    ras_push = instr_queue_consumed[i];
                    ras_update = addr[i] + (rvc_call[i] ? 2 : 4);
          
                # calculate the jump target address
                if (taken_rvc_cf[i] || taken_rvi_cf[i]):
                    predict_address = addr[i] + (taken_rvc_cf[i] ? rvc_imm[i] : rvi_imm[i]);
          
    # or reduce struct
    #?? always_comb begin
        bp_valid = U.w(1)(0)
        for i in range(0:INSTR_PER_FETCH+1):
             bp_valid |= (cf_type[i] != NoCF)
    
    is_mispredict = resolved_branch_i.valid & resolved_branch_i.is_mispredict

    # Cache interface
    icache_dreq_o.req = instr_queue_ready
    if_ready = icache_dreq_i.ready & instr_queue_ready
    # We need to flush the cache pipeline if:
    # 1. We mispredicted
    # 2. Want to flush the whole processor front-end
    # 3. Need to replay an instruction because the fetch-fifo was full
    icache_dreq_o.kill_s1 = is_mispredict | flush_i | replay
    # if we have a valid branch-prediction we need to only kill the last cache request
    # also if we killed the first stage we also need to kill the second stage (inclusive flush)
    icache_dreq_o.kill_s2 = icache_dreq_o.kill_s1 | bp_valid

    #Update Control Flow Predictions
    bht_update_t bht_update;
    btb_update_t btb_update;

    bht_update.valid = resolved_branch_i.valid & (resolved_branch_i.cf_type == ariane_pkg::Branch)
    bht_update.pc    = resolved_branch_i.pc
    bht_update.taken = resolved_branch_i.is_taken
    # only update mispredicted branches e.g. no returns from the RAS
    btb_update.valid = resolved_branch_i.valid & resolved_branch_i.is_mispredict
                        & (resolved_branch_i.cf_type == ariane_pkg::JumpR)
    btb_update.pc    = resolved_branch_i.pc
    btb_update.target_address = resolved_branch_i.target_address

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
    always_comb begin : npc_select
        automatic logic [riscv::VLEN-1:0] fetch_address;
        # check whether we come out of reset
        # this is a workaround. some tools have issues
        # having boot_addr_i in the asynchronous
        # reset assignment to npc_q, even though
        # boot_addr_i will be assigned a constant
        # on the top-level.
        if (npc_rst_load_q):
            npc_d         = boot_addr_i[riscv::VLEN-1:0];
            fetch_address = boot_addr_i[riscv::VLEN-1:0];
        else:
            fetch_address    = npc_q;
            # keep stable by default
            npc_d            = npc_q;
        
        # 0. Branch Prediction
        if bp_valid:
            fetch_address = predict_address
            npc_d = predict_address

        # 1. Default assignment
        if (if_ready):
            npc_d = {fetch_address[riscv::VLEN-1:2], 2'b0}  + 'h4;
        # 2. Replay instruction fetch
        if (replay):
            npc_d = replay_addr
        # 3. Control flow change request
        if (is_mispredict):
            npc_d = resolved_branch_i.target_address
        # 4. Return from environment call
        if (eret_i):
            npc_d = epc_i
        # 5. Exception/Interrupt
        if (ex_valid_i):
            npc_d = trap_vector_base_i
        # 6. Pipeline Flush because of CSR side effects
        # On a pipeline flush start fetching from the next address
        # of the instruction in the commit stage
        # we came here from a flush request of a CSR instruction or AMO,
        # as CSR or AMO instructions do not exist in a compressed form
        # we can unconditionally do PC + 4 here
        # TODO(zarubaf) This adder can at least be merged with the one in the csr_regfile stage
        if (set_pc_commit_i):
            npc_d = pc_commit_i + {{riscv::VLEN-3{1'b0}}, 3'b100};
        # 7. Debug
        # enter debug on a hard-coded base-address
        if (set_debug_pc_i):
            npc_d = ArianeCfg.DmBaseAddress[riscv::VLEN-1:0] + dm::HaltAddress[riscv::VLEN-1:0];
            icache_dreq_o.vaddr = fetch_address;
    end

    icache_data=U.w(FETCH_WIDTH)
    # re-align the cache line
    assign icache_data = icache_dreq_i.data >> {shamt, 4'b0};

    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (~rst_ni):
            npc_rst_load_q    <= 1'b1;
            npc_q             <= '0;
            icache_data_q     <= '0;
            icache_valid_q    <= 1'b0;
            icache_vaddr_q    <= 'b0;
            icache_ex_valid_q <= 1'b0;
            btb_q             <= '0;
            bht_q             <= '0;
        else:
            npc_rst_load_q    <= 1'b0;
            npc_q             <= npc_d;
            icache_valid_q    <= icache_dreq_i.valid;
            if (icache_dreq_i.valid):
                icache_data_q        <= icache_data;
                icache_vaddr_q       <= icache_dreq_i.vaddr;
                icache_ex_valid_q    <= icache_dreq_i.ex;
                # save the uppermost prediction
                btb_q                <= btb_prediction[INSTR_PER_FETCH-1];
                bht_q                <= bht_prediction[INSTR_PER_FETCH-1];
    end

    ras #(
      .DEPTH  ( ArianeCfg.RASDepth  )
    ) i_ras (
      .clk_i,
      .rst_ni,
      .flush_i( flush_bp_i  ),
      .push_i ( ras_push    ),
      .pop_i  ( ras_pop     ),
      .data_i ( ras_update  ),
      .data_o ( ras_predict )
    );

    btb #(
      .NR_ENTRIES       ( ArianeCfg.BTBEntries   )
    ) i_btb (
      .clk_i,
      .rst_ni,
      .flush_i          ( flush_bp_i       ),
      .debug_mode_i,
      .vpc_i            ( icache_vaddr_q   ),
      .btb_update_i     ( btb_update       ),
      .btb_prediction_o ( btb_prediction   )
    );

    bht #(
      .NR_ENTRIES       ( ArianeCfg.BHTEntries   )
    ) i_bht (
      .clk_i,
      .rst_ni,
      .flush_i          ( flush_bp_i       ),
      .debug_mode_i,
      .vpc_i            ( icache_vaddr_q   ),
      .bht_update_i     ( bht_update       ),
      .bht_prediction_o ( bht_prediction   )
    );

    # we need to inspect up to INSTR_PER_FETCH instructions for branches
    # and jumps
    for i in range(0:INSTR_PER_FETCH+1): 
        begin : gen_instr_scan
            instr_scan i_instr_scan (
                .instr_i      ( instr[i]      ),
                .rvi_return_o ( rvi_return[i] ),
                .rvi_call_o   ( rvi_call[i]   ),
                .rvi_branch_o ( rvi_branch[i] ),
                .rvi_jalr_o   ( rvi_jalr[i]   ),
                .rvi_jump_o   ( rvi_jump[i]   ),
                .rvi_imm_o    ( rvi_imm[i]    ),
                .rvc_branch_o ( rvc_branch[i] ),
                .rvc_jump_o   ( rvc_jump[i]   ),
                .rvc_jr_o     ( rvc_jr[i]     ),
                .rvc_return_o ( rvc_return[i] ),
                .rvc_jalr_o   ( rvc_jalr[i]   ),
                .rvc_call_o   ( rvc_call[i]   ),
                .rvc_imm_o    ( rvc_imm[i]    )
            );
        end

    instr_queue i_instr_queue (
        .clk_i               ( clk_i                ),
        .rst_ni              ( rst_ni               ),
        .flush_i             ( flush_i              ),
        .instr_i             ( instr                ), # from re-aligner
        .addr_i              ( addr                 ), # from re-aligner
        .exception_i         ( icache_ex_valid_q    ), # from I$
        .predict_address_i   ( predict_address      ),
        .cf_type_i           ( cf_type              ),
        .valid_i             ( instruction_valid    ), # from re-aligner
        .consumed_o          ( instr_queue_consumed ),
        .ready_o             ( instr_queue_ready    ),
        .replay_o            ( replay               ),
        .replay_addr_o       ( replay_addr          ),
        .fetch_entry_o       ( fetch_entry_o        ), # to back-end
        .fetch_entry_valid_o ( fetch_entry_valid_o  ), # to back-end
        .fetch_entry_ready_i ( fetch_entry_ready_i  )  # to back-end
    );

    # pragma translate_off
    `ifndef VERILATOR
        initial begin
            assert (FETCH_WIDTH == 32 || FETCH_WIDTH == 64) else $fatal("[frontend] fetch width != not supported");
        end
    `endif
    # pragma translate_on
endmodule

#***********董妙君 8.31 End***********#            