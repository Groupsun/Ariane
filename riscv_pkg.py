## ********** 黄智权、韩耀华 9.8 Begin ********** ##
from pyhcl import *
VLEN = 64

# --------------------
# Instruction Types
# --------------------
rtype_t = Bundle(
    funct7=U.w(7),
    rs2=U.w(5),
    rs1=U.w(5),
    funct3=U.w(3),
    rd=U.w(5),
    opcode=U.w(7)
)

r4type_t = Bundle(
    rs3=U.w(5),
    funct2=U.w(2),
    rs2=U.w(5),
    rs1=U.w(5),
    funct3=U.w(3),
    rd=U.w(5),
    opcode=U.w(7)
)

rftype_t = Bundle(
    funct5=U.w(5),
    fmt=U.w(2),
    rs2=U.w(5),
    rs1=U.w(5),
    rm=U.w(3),
    rd=U.w(5),
    opcode=U.w(7)
) # floating-point

rvftype_t = Bundle(
    funct2=U.w(2),
    vecfltop=U.w(5),
    rs2=U.w(5),
    rs1=U.w(5),
    repl=U.w(1),
    vfmt=U.w(2),
    rd=U.w(5),
    opcode=U.w(7)
) # vectorial floating-point

itype_t = Bundle(
    imm=U.w(12),
    rs1=U.w(5),
    funct3=U.w(3),
    rd=U.w(5),
    opcode=U.w(7)
)

stype_t = Bundle(
    imm=U.w(7),
    rs2=U.w(5),
    rs1=U.w(5),
    funct3=U.w(3),
    imm0=U.w(5),
    opcode=U.w(7)
)

utype_t = Bundle(
    funct3=U.w(20),
    rd=U.w(5),
    opcode=U.w(7)
)

# atomic instructions
atype_t = Bundle(
    funct5=U.w(5),
    aq=U.w(1),
    rl=U.w(1),
    rs2=U.w(5),
    rs1=U.w(5),
    funct3=U.w(3),
    rd=U.w(5),
    opcode=U.w(7)
)

instruction_t = Bundle(
    instr=U.w(32),
    rtype=rtype_t,
    r4type=r4type_t,
    rftype=rftype_t,
    rvftype=rvftype_t,
    itype=itype_t,
    stype=stype_t,
    utype=utype_t,
    atype=atype_t
)

## ********** 黄智权、韩耀华 9.8 End ********** ##