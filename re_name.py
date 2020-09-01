
from pyhcl import *
import math
#riscv_pkg.sv
# ********** 戴熠华 2020.8.27 Begin ********** #
riscv_VLEN=64

# ariane_pkg.sv

NR_SB_ENTRIES = 8 #number of scoreboard entries
TRANS_ID_BITS = int(math.log(NR_SB_ENTRIES,2)) #depending on the number of scoreboard entries we need that many bits
REG_ADDR_SIZE = 6 #32 registers + 1 bit for re-naming = 6
class fu_t(Module):
    NONE=U(0)      # 0
    LOAD=U(1)      # 1
    STORE=U(2)     # 2
    ALU=U(3)       # 3
    CTRL_FLOW=U(4) # 4
    MULT=U(5)      # 5
    CSR=U(6)       # 6
    FPU=U(7)       # 7
    FPU_VEC=U(8)   # 8

class fu_op(Module):
    # basic ALU op 4
    ADD, SUB, ADDW, SUBW=U(0),U(1),U(2),U(3)
    # logic operations 3
    XORL, ORL, ANDL=U(4),U(5),U(6)
    # shifts 6
    SRA, SRL, SLL, SRLW, SLLW, SRAW=U(7),U(8),U(9),U(10),U(11),U(12)
    # comparisons 6
    LTS, LTU, GES, GEU, EQ, NE=U(13),U(14),U(15),U(16),U(17),U(18)
    # jumps 2
    JALR, BRANCH=U(19),U(20)
    # set lower than operations 2
    SLTS, SLTU=U(21),U(22)
    # CSR functions 12
    MRET, SRET, DRET, ECALL, WFI, FENCE, FENCE_I, SFENCE_VMA, CSR_WRITE, CSR_READ, CSR_SET, CSR_CLEAR=U(23),U(24),U(25),U(26),U(27),U(28),U(29),U(30),U(31),U(32),U(33),U(34)
    # LSU functions 11
    LD, SD, LW, LWU, SW, LH, LHU, SH, LB, SB, LBU=U(35),U(36),U(37),U(38),U(39),U(40),U(41),U(42),U(43),U(44),U(45)
    # Atomic Memory Operations 4 9 9
    AMO_LRW, AMO_LRD, AMO_SCW, AMO_SCD=U(46),U(47),U(48),U(49)
    AMO_SWAPW, AMO_ADDW, AMO_ANDW, AMO_ORW, AMO_XORW, AMO_MAXW, AMO_MAXWU, AMO_MINW, AMO_MINWU=U(50),U(51),U(52),U(53),U(54),U(55),U(56),U(57),U(58)
    AMO_SWAPD, AMO_ADDD, AMO_ANDD, AMO_ORD, AMO_XORD, AMO_MAXD, AMO_MAXDU, AMO_MIND, AMO_MINDU=U(59),U(60),U(61),U(62),U(63),U(64),U(65),U(66),U(67)
    # Multiplications 5
    MUL, MULH, MULHU, MULHSU, MULW=U(68),U(69),U(70),U(71),U(72)
    # Divisions 8
    DIV, DIVU, DIVW, DIVUW, REM, REMU, REMW, REMUW=U(73),U(74),U(75),U(76),U(77),U(78),U(79),U(80)
    # Floating-Point Load and Store Instructions 8
    FLD, FLW, FLH, FLB, FSD, FSW, FSH, FSB=U(81),U(82),U(83),U(84),U(85),U(86),U(87),U(88)
    # Floating-Point Computational Instructions 10
    FADD, FSUB, FMUL, FDIV, FMIN_MAX, FSQRT, FMADD, FMSUB, FNMSUB, FNMADD=U(89),U(90),U(91),U(92),U(93),U(94),U(95),U(96),U(97),U(98)
    # Floating-Point Conversion and Move Instructions 6
    FCVT_F2I, FCVT_I2F, FCVT_F2F, FSGNJ, FMV_F2X, FMV_X2F=U(99),U(100),U(101),U(102),U(103),U(104)
    # Floating-Point Compare Instructions 1
    FCMP=U(105)
    # Floating-Point Classify Instruction 1
    FCLASS=U(106)
    # Vectorial Floating-Point Instructions that don't directly map onto the scalar ones 15
    VFMIN, VFMAX, VFSGNJ, VFSGNJN, VFSGNJX, VFEQ, VFNE, VFLT, VFGE, VFLE, VFGT, VFCPKAB_S, VFCPKCD_S, VFCPKAB_D, VFCPKCD_D=U(107),U(108),U(109),U(110),U(111),U(112),U(113),U(114),U(115),U(116),U(117),U(118),U(119),U(120),U(121)

#Only use struct when signals have same direction
#exception
class exception_t(Module):
    cause=Wire(U.w(64)(0))      #cause of exception
    tval=Wire(U.w(64)(0))       #additional information of causing exception (e.g.: instruction causing it),
                                #address of LD/ST fault
    valid=Wire(Bool)


class cf_t(Module):
    NoCF=U(0)       #No control flow prediction
    Branch=U(1)     #Branch
    Jump=U(2)       #Jump to address from immediate
    JumpR=U(3)      #Jump to address from registers
    Return=U(4)     #Return Address Prediction


#branchpredict scoreboard entry
#this is the struct which we will inject into the pipeline to guide the various
#units towards the correct branch decision and resolve
class branchpredict_sbe_t(Module):
    cf=cf_t()
    predict_address=Wire(U.w(riscv_VLEN)(0))
    


#---------------
#ID/EX/WB Stage
#---------------
    
class scoreboard_entry_t(Module):
    pc=RegInit(U.w(riscv_VLEN)(0))          #PC of instruction
    trans_id=Wire(U.w(TRANS_ID_BITS)(0))    #this can potentially be simplified, we could index the scoreboard entry
                                            #with the transaction id in any case make the width more generic
                                            #functional unit to use
    fu=fu_t()                               #functional unit to use
    op=fu_op()                              #operation to perform in each functional unit
    rs1=RegInit(U.w(REG_ADDR_SIZE)(0))      #register source address 1
    rs2=RegInit(U.w(REG_ADDR_SIZE)(0))      #register source address 2
    rd=RegInit(U.w(REG_ADDR_SIZE)(0))       #register destination address

    result=RegInit(U.w(64)(0))              #for unfinished instructions this field also holds the immediate,
                                            #for unfinished floating-point that are partly encoded in rs2, this field also holds rs2
                                            #for unfinished floating-point fused operations (FMADD, FMSUB, FNMADD, FNMSUB)
                                            #this field holds the address of the third operand from the floating-point register file
    valid = Wire(Bool)                      #is the result valid
    use_imm=Wire(Bool)                      #should we use the immediate as operand b?
    use_zimm=Wire(Bool)                     #use zimm as operand a
    use_pc=Wire(Bool)                       #set if we need to use the PC as operand a, PC from exception
    ex=exception_t()                        #exception has occurred
    bp=branchpredict_sbe_t()                #branch predict scoreboard data structure
    
    is_compressed=Wire(Bool)                #signals a compressed instructions, we need this information at the commit stage if

                                            #we want jump accordingly e.g.: +4, +2
# re_name.sv

class re_name(Module):
    io = IO(
        clk_i=Input(Bool),
        rst_ni=Input(Bool),#Flush renaming state
        flush_i=Input(Bool),
        flush_unissied_instr_i=Input(Bool),#Flush renaming state

        #from/to scoreboard

        issue_instr_i=Input(scoreboard_entry_t())

        issue_instr_valid_i=Input(Bool),
        issue_ack_o=Output(Bool),
        # from/to issue and read operands

        issue_instr_o=Output(scoreboard_entry_t()),

        issue_instr_valid_o=Output(Bool),
        issue_ack_i=Input(Bool)
    )
    #pass through handshaking signals
    io.issue_instr_valid_o <<= io.issue_instr_valid_i
    io.issue_ack_o         <<= io.issue_ack_i
    #keep track of re-naming data structures
    re_name_table_gpr_n=RegInit(U.w(32)(0))
    re_name_table_gpr_q=RegInit(U.w(32)(0))
    re_name_table_fpr_n=RegInit(U.w(32)(0))
    re_name_table_fpr_q=RegInit(U.w(32)(0))

    #Re-naming

    #MSB of the renamed source register addresses
    name_bit_rs1=RegInit(U.w(1)(0))
    name_bit_rs2=RegInit(U.w(1)(0))
    name_bit_rs3=RegInit(U.w(1)(0))
    name_bit_rd=RegInit(U.w(1)(0))

    #default assignments
    re_name_table_gpr_n <<= re_name_table_gpr_q
    re_name_table_fpr_n <<= re_name_table_fpr_q

    #io.issue_instr_o       <<= io.issue_instr_i

    #with when(io.issue_ack_i==Bool(True)&io.flush_unissied_instr_i==Bool(False)):
        #if we acknowledge the instruction tic the corresponding destination register
    #    with when()

# ********** 戴熠华 2020.8.30 End ********** #
