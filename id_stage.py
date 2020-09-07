# ********** 郑学钿 2020.8.27,28 Begin ********** #

from header_for_id_stage import *

class Packed:
    valid = Reg(Bool)
    sbe = Reg(ariane_pkg.scoreb)
    is_ctrl_flow = Reg(Bool)


class id_stage(Module):
    io = IO(
        clk_i = Input(Bool),
        rst_ni = Input(Bool),
        flush_i = Input(Bool),
        debug_req_i = Input(Bool),
        # from IF
        fetch_entry_i = Input(ariane_pkg.fetch_entry_t),            
        fetch_entry_valid_i = Input(Bool),
        fetch_entry_ready_o = Output(Bool),                             # acknowledge the instruction (fetch entry)
        # to ID
        issue_entry_o = Output(ariane_pkg.scoreboard_entry_t),          # a decoded instruction
        issue_entry_valid_o = Output(Bool),                             # issue entry is valid
        is_ctrl_flow_o = Output(Bool),                                  # the instruction we issue is a ctrl flow instructions
        issue_instr_ack_i = Input(Bool),                                # issue stage acknowledged sampling of instructions
        # from CSR file
        priv_lvl_i = Input(riscv.priv_lvl_t),                           # current privilege level
        fs_i = Input(riscv.xs_t),                                       # floating point extension status
        frm_i = Input(U.w(3)),                                          # floating-point dynamic rounding mode
        irq_i = Input(U.w(2)),
        irq_ctrl_i = Input(ariane_pkg.irq_ctrl_t),               
        debug_mode_i = Input(Bool),                                     # we are in debug mode
        tvm_i = Input(Bool),
        tw_i = Input(Bool),
        tsr_i = Input(Bool),
    )

    issue_n = Packed()
    issue_q = Packed()

    is_control_flow_instr = Wire(Bool)
    decoded_instruction = Wire(scoreboard_entry_t)
    is_illegal = Wire(Bool)
    instruction = Wire(U.w(32))
    is_compressed = Wire(Bool)

    compressed_decoder_i = compressed_decoder(
        fetch_entry_i.instruction,
        instruction,
        is_illegal,
        is_compressed
        )

    decoder_i = decoder(
        fetch_entry_i.address,
        is_compressed,
        is_illegal,
        instruction,
        fetch_entry_i.instruction,
        fetch_entry_i.branch_predit,
        fetch_entry_i.ex,
        priv_lvl_i,
        debug_mode_i,
        decoded_instruction,
        is_control_flow_instr
    )

    issue_entry_o <<= issue_q.she
    issue_entry_valid_o <<= issue_q.valid
    is_ctrl_flow_o <<= issue_q.is_ctrl_flow

# ********** 郑学钿 2020.8.28 End ********** #


# ********** 郑学钿 2020.8.29 Begin ********** #

    issue_n <<= issue_q
    fetch_entry_ready_o <<= U(0)
    # Clear the valid flag if issue has acknowledged the instruction
    with when(issue_instr_ack_i == Bool(true)):
        issue_n.valid <<= U(0)
    # if we have a space in the register and the fetch is valid, go get it
    # or the issue stage is currently acknowledging an instruction, which means that we will have space
    # for a new instruction
    with when((issue_q.valid == Bool(false) | issue_instr_ack_i == Bool(true)) & fetch_entry_valid_i == Bool(true)):
        fetch_entry_ready_o <<= U(1)
        issue_n.valid <<= U(1)
        issue_n.sbe = decoded_instruction
        issue_n.is_ctrl_flow = is_control_flow_instr)
    
    # invalidate the pipeline register on a flush
    with when(flush_i == Bool(true)):
        issue_n.valid <<= U(0)

    # ------------------------
    # Registers (ID <-> Issue)
    # ------------------------

    issue_q <<= issue_n 

# ********** 郑学钿 2020.8.29 End ********** #

# ----------------------------------------------------------
# 还没有测试
# -----------------------------------------------------------