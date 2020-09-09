
from pyhcl import *
import math
from enum import Enum
#riscv_pkg.sv
# ********** 戴熠华 2020.8.27 Begin ********** #
riscv_VLEN=64

# ariane_pkg.sv

NR_SB_ENTRIES = 8 #number of scoreboard entries
TRANS_ID_BITS = int(math.log(NR_SB_ENTRIES,2)) #depending on the number of scoreboard entries we need that many bits
REG_ADDR_SIZE = 6 #32 registers + 1 bit for re-naming = 6


# Floating-point extensions configuration
RVF =U(1)       # Is F extension enabled
RVD =U(1)       # Is D extension enabled
#Transprecision floating-point extensions configuration
XF16=U(0)       # Is half-precision float extension (Xf16) enabled
XF16ALT=U(0)    # Is alternative half-precision float extension (Xf16alt) enabled
XF8=U(0)        # Is quarter-precision float extension (Xf8) enabled
#vvvv Don't change these by hand! vvvv
FP_PRESENT=RVF|RVD|XF16|XF16ALT|XF8


        
        
class fu_t(Enum):
    NONE=U(0)      # 0
    LOAD=U(1)      # 1
    STORE=U(2)     # 2
    ALU=U(3)       # 3
    CTRL_FLOW=U(4) # 4
    MULT=U(5)      # 5
    CSR=U(6)       # 6
    FPU=U(7)       # 7
    FPU_VEC=U(8)   # 8

class fu_op(Enum):
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
    io=IO(pp=Input(U.w(1)))
    pc=RegInit(U.w(riscv_VLEN)(0))          #PC of instruction
    trans_id=Wire(U.w(TRANS_ID_BITS)(0))    #this can potentially be simplified, we could index the scoreboard entry
                                            #with the transaction id in any case make the width more generic
                                            #functional unit to use
    fu=Wire(U.w(7))                         #functional unit to use
    op=Wire(U.w(4))                         #operation to perform in each functional unit
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

class bbbb(Module):
    io=IO(
        bbb=scoreboard_entry_t
        )
# -------------------------------
# Extract Src/Dst FP Reg from Op
# -------------------------------
def  is_rs1_fpr(op):
    with when(FP_PRESENT): #makes function static for non-fp case
        with when(fu_op.FMUL<=op and op<=fu_op.FNMADD): #Computational Operations (except ADD/SUB)
            return U(1)
        with elsewhen(op==fu_op.FCVT_F2I):#Float-Int Casts
            return U(1)
        with elsewhen(op==fu_op.FCVT_F2F):#Float-Float Casts
            return U(1)
        with elsewhen(op==fu_op.FSGNJ):#Sign Injections
            return U(1)
        with elsewhen(op==fu_op.FMV_F2X):#FPR-GPR Moves
            return U(1)
        with elsewhen(op==fu_op.FCMP):#Comparisons
            return U(1)
        with elsewhen(op==fu_op.FCLASS):#Classifications
            return U(1)
        with elsewhen(fu_op.VFMIN<=op and op<=fu_op.VFCPKCD_D):#Additional Vectorial FP ops
            return U(1)
        with otherwise():#all other ops
            return U(0)
    with otherwise():
        return U(0) 

def  is_rs2_fpr(op):
    with when(FP_PRESENT): #makes function static for non-fp case
        with when(fu_op.FSD<=op & op<=fu_op.FSB): #FP Stores
            return U(1)
        with when(fu_op.FADD<=op & op<=fu_op.FMIN_MAX): #Computational Operations (no sqrt)
            return U(1)
        with when(fu_op.FMADD<=op & op<=fu_op.FNMADD): #Fused Computational Operations
            return U(1)
        with elsewhen(op==fu_op.FCVT_F2F):#Vectorial F2F Conversions requrie target
            return U(1)
        with elsewhen(fu_op.FSGNJ<=op & op<=fu_op.FMV_F2X):#Sign Injections and moves mapped to SGNJ
            return U(1)
        with elsewhen(op==fu_op.FCMP):#Comparisons
            return U(1)
        with elsewhen(fu_op.VFMIN<=op & op<=fu_op.VFCPKCD_D):#Additional Vectorial FP ops
            return U(1)
        with otherwise():#all other ops
            return U(0)
    with otherwise():
        return U(0)



def is_rd_fpr(op):
    with when(FP_PRESENT): #makes function static for non-fp case
        with when(fu_op.FLD<=op & op<=fu_op.FLB): #FP Loads
            return U(1)
        with elsewhen(fu_op.FADD<=op & op<=fu_op.FNMADD):#Computational Operations
            return U(1)
        with elsewhen(op==fu_op.FCVT_I2F):#Int-Float Casts
            return U(1)
        with elsewhen(op==fu_op.FCVT_F2F):#Float-Float Casts
            return U(1)
        with elsewhen(op==fu_op.FSGNJ):#Sign Injections
            return U(1)
        with elsewhen(op==fu_op.FMV_X2F):#GPR-FPR Moves
            return U(1)
        with elsewhen(fu_op.VFMIN<=op & op<=fu_op.VFSGNJX):#Vectorial MIN/MAX and SGNJ
            return U(1)
        with elsewhen(fu_op.VFCPKAB_S<=op & op<=fu_op.VFCPKCD_D):#Vectorial FP cast and pack ops
            return U(1)
        with otherwise():#all other ops
            return U(0)
    with otherwise():
        return U(0)
    
def is_imm_fpr(op):
    with when(FP_PRESENT): #makes function static for non-fp case
        with when(fu_op.FADD<=op & op<=fu_op.FSUB): #FP Loads
            return U(1)
        with elsewhen(fu_op.FMADD<=op & op<=fu_op.FNMADD):#Computational Operations
            return U(1)
        with elsewhen(fu_op.VFCPKAB_S<=op & op<=fu_op.VFCPKCD_D):#Vectorial FP cast and pack ops
            return U(1)
        with otherwise():#all other ops
            return U(0)
    with otherwise():
        return U(0)  
    
# re_name.sv

class re_name(Module):
    io = IO(
        clk_i=Input(Bool),
        rst_ni=Input(Bool),#Flush renaming state
        flush_i=Input(Bool),
        flush_unissied_instr_i=Input(Bool),#Flush renaming state

        #from/to scoreboard

        issue_instr_i=Input(scoreboard_entry_t()),

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
    io.issue_instr_o    <<= io.issue_instr_i
    with when(io.issue_ack_i==Bool(True)&io.flush_unissied_instr_i==Bool(False)):
        #if we acknowledge the instruction tic the corresponding destination register
        with when(is_rd_fpr(io.issue_instr_i.op)):
            re_name_table_fpr_n[io.issue_instr_i.rd]<<=re_name_table_fpr_q[io.issue_instr_i.rd] & U(1)
        with otherwise():
            re_name_table_gpr_n[io.issue_instr_i.rd]<<=re_name_table_gpr_q[io.issue_instr_i.rd] & U(1)
    #select name bit according to the register file used for source operands
    with when(is_rs1_fpr(io.issue_instr_i.op)):
        name_bit_rs1 <<=re_name_table_fpr_q[io.issue_instr_i.rs1]
    with otherwise():
        name_bit_rs1 <<=re_name_table_gpr_q[io.issue_instr_i.rs1]
    
    with when(is_rs2_fpr(io.issue_instr_i.op)):
        name_bit_rs1 <<=re_name_table_fpr_q[io.issue_instr_i.rs2]
    with otherwise():
        name_bit_rs1 <<=re_name_table_gpr_q[io.issue_instr_i.rs2]
    #rs3 is only used in certain FP operations and held like an immediate
    name_bit_rs3<<=re_name_table_fpr_q[io.issue_instr_i.result[4:0]]
    #select name bit according to the state it will have after renaming
    with when(is_rd_fpr(io.issue_instr_i.op)):
        name_bit_rd<<=re_name_table_fpr_q[io.issue_instr_i.rd] & U(1)
    with otherwise():
        name_bit_rd<<=re_name_table_gpr_q[io.issue_instr_i.rd] & (issue_instr_i.rd != U(0))

    #re-name the destination register
    ENABLE_RENAME=U(1)
    carry = Wire(Vec(6, Bool))
    with when(is_imm_fpr(io.issue_instr_i.op)):
        carry[5]<<=ENABLE_RENAME & name_bit_rs3
        for i in range(5):
            carry[i]<<=io.issue_instr_i.rd[i]
        io.issue_instr_o.rd<<=CatVecH2L(carry)
    carry[5]<<=name_bit_rd & name_bit_rd
    for i in range(5):
        carry[i]<<=io.issue_instr_i.rd[i]
    io.issue_instr_o.rd<<=CatVecH2L(carry)

    re_name_table_gpr_n[0]<<=U(1)

    with when(io.flush_i==Bool(True)):
        re_name_table_gpr_n <<=U(0)
        re_name_table_fpr_n <<=U(0) 
    #re-name the source registers
# ********** 戴熠华 2020.9.1 End ********** #
# ********** 戴熠华 2020.9.2 Begin ********** #
    # -------------------
    # Registers
    # -------------------
    flagger=RegInit(U.w(1)(0))
    clk_i_reg=Reg(U.w(1))
    rst_ni_reg=Reg(U.w(1))
    with when(flagger==U(0)):
        clk_i_reg<<=clk_i
        rst_ni_reg<<=rst_ni
    
    with when((clk_i_reg==Bool(False)&clk_i==Bool(True)) or (rst_ni_reg==Bool(True) & rst_ni==Bool(False))):
        with when(rst_ni==Bool(False)):
            re_name_table_gpr_q<<=U(0)
            re_name_table_fpr_q<<=U(0)
        with otherwise:
            re_name_table_gpr_q<<=re_name_table_gpr_n
            re_name_table_fpr_q<<=re_name_table_fpr_n

    clk_i_reg<<=clk_i
    rst_ni_reg<<=rst_ni
# ********** 戴熠华 2020.9.2 End ********** #
if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(re_name()), "re_name.fir"))
