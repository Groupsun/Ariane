# ********** 郑学钿 2020.8.27,28 Begin ********** #

from pyhcl import *

class Packed:
    valid = Bool
    sbe = Bool
    is_ctrl_flow = Bool

    ariane = ariane_pkg()
    ariane.scoreboard_entry_t = sbe


class id_stage(Module):
    io = IO(
        clk_i = Input(Bool),
        rst_ni = Input(Bool),
        flush_i = Input(Bool),
        debug_req_i = Input(Bool),
        # from IF
    #    fetch_entry_i = Input(Bool),            # 待改
        fetch_entry_valid_i = Input(Bool),
        fetch_entry_ready_o = Output(Bool),     # acknowledge the instruction (fetch entry)
        # to ID
    #    issue_entry_o = Output(Bool),           # 待改 a decoded instruction
        issue_entry_valid_o = Output(Bool),     # issue entry is valid
        is_ctrl_flow_o = Output(Bool),          # the instruction we issue is a ctrl flow instructions
        issue_instr_ack_i = Input(Bool),        # issue stage acknowledged sampling of instructions
        # from CSR file
    #    priv_lvl_i = Input(Bool),               # 待改 current privilege level
    #    fs_i = Input(Bool),                     # 待改 floating point extension status
        frm_i = Input(U.w(3)),                  # floating-point dynamic rounding mode
        irq_i = Input(U.w(2)),
    #    irq_ctrl_i = Input(Bool),               #待改
        debug_mode_i = Input(Bool),             # we are in debug mode
        tvm_i = Input(Bool),
        tw_i = Input(Bool),
        tsr_i = Input(Bool),
    )

    # --------------------------------------------------------------
    # 继承？部分后来看了include里面的代码发现和一开始的想法有不小的出入
    # 一开始以为都只是某个变量？原来是一个结构体？大部分都得重新修改
    # --------------------------------------------------------------
    ariane = ariane_pkg()
    risc = riscv()
    
    ariane.io.fetch_entry_t <<= io.fetch_entry_i
    ariane.io.scoreboard_entry_t <<= io.issue_entry_o
    risc.io.priv_lvl_t <<= io.priv_lvl_i
    risc.io.xs_t <<= io.fs_i
    ariane.io.irq_ctrl_t <<= io.irq_ctrl_i

    issue_n = Packed()
    issue_q = Packed()

    is_control_flow_instr = Bool
    decoded_instruction = Bool
    is_illegal = Bool
    instruction = U.w(32)
    is_compressed = Bool

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

    issue_entry_o <<= issue_q.she;
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
    with when((issue_q.valid == Bool(false) || issue_instr_ack_i == Bool(true)) && fetch_entry_valid_i == Bool(true)):
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
# 调用到的include文件夹中文件的类还没有实现
# 重新阅读include文件夹中相关代码后发现许多做错了
# 还没有尝试编译
# 后面的东西大部分还没写，写完的还没好好检查，应该还有很多要改的
# -----------------------------------------------------------