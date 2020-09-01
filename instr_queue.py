#***********黄铭绚 8.31 Begin***********#
'''
typedef enum logic [2:0] {
      NoCF,   // No control flow prediction
      Branch, // Branch
      Jump,   // Jump to address from immediate
      JumpR,  // Jump to address from registers
      Return  // Return Address Prediction
    } cf_t;
'''



from pyhcl import *
from lzc import *
import math






class instr_data_t:
    def __init__(self):
        self. instr=Reg(U.w(32))
        self.cf=Reg(U.w(3))
        self.ex=Reg(U.w(1))

def OR(a,length):
    for i in range(length):
        if(a[i]==True)return True
    return False

def AND(a,length):
    for i in range(length):
        if(a[i]==False)return False
    return True



class  instr_queue(Module):
    io=IO(
        rst_ni=Input(Bool),
        flush_i=Input(Bool),
        instr_i=Input(Vec(2,32)),
        addr_i=Input(Vec(2,64)),
        valid_i=Input(U.w(2)),
        predict_address_i=Input(U.w(64)),
        cf_type_i=Input(Vec(2,3)),
        fetch_entry_ready_i=Input(Bool),
        exception_i=Input(Bool),
         

        ready_o=Output(Bool),
        consumed_o=Output(U.w(2)),
        replay_o=Output(Bool),
        replay_addr_o=Output(U.w(64)),

        #    fetch_entry_t-fetch_entry_o
        address=Output(U.w(64)),#the address of the instructions from below
        instruction=Output(U.w(32)),#instruction word
        #branchpredict_sbe_t-branch_predict:this field contains branch prediction information regarding the forward branch path
        b_cf=Output(U.w(3)),#   type of control flow prediction
        predict_address=Output(U.w(64)),#target address at which to jump, or not
        #exception_t-ex:his field contains exceptions which might have happened earlier, e.g.: fetch exceptions
        ex_cause=Output(U.w(64)),#cause of exception
        ex_tval=Output(U.w(64)),# additional information of causing exception (e.g.: instruction causing it), address of LD/ST fault
        ex_valid=Output(Bool),

        fetch_entry_valid_o=Output(Bool)
    )
    

    branch_index=Wire(U.w(1))
    #instruction queues
    instr_queue_usage=Reg(Vec(2,4))
    instr_data_in=[]
    instr_data_out=[]
    for i in range(2):
        instr_data_in[i]=instr_data_t()
        instr_data_out[i]=instr_data_t()
    push_instr=Wire(U.w(2))
    push_instr_fifo=Wire(U.w(2))
    pop_instr=Reg(U.w(2))
    instr_queue_full=Reg(U.w(2))
    instr_queue_empty=Reg(U.w(2))
    instr_overflow=Reg(U.w(1))
    #address queue
    address_queue_usage=Reg(U.w(4))
    address_out=Reg(U.w(64))
    pop_address=Reg(U.w(1))
    push_address=Reg(U.w(1))
    full_address=Reg(U.w(1))
    empty_address=Reg(U.w(1))
    address_overflow=Reg(U.w(1))
    #input stream counter
    idx_is_d=Wire(U.w(1))
    idx_is_q=Wire(U.w(1))

    #register
    #output FIFO select, one-hot
    idx_ds_d=Wire(U.w(2))
    idx_ds_q=Reg(U.w(2))
    #current PC
    pc_d=Wire(U.w(64))
    pc_q=Reg(U.w(64))
    #we need to re-set the address because of a flush
    reset_address_d=Wire(U.w(1))
    reset_address_q=Reg(U.w(1))
    branch_mask_extended=Wire(U.w(3))
    branch_mask=Wire(U.w(2))
    branch_empty=Wire(U.w(1))
    taken=Wire(U.w(2))
    #shift amount, e.g.: instructions we want to retire
    popcount=Wire(U.w(2))
    shamt=Wire(U.w(1))
    valid=Wire(U.w(2))
    consumed_extended=Wire(U.w(4))
    #FIFO mask
    fifo_pos_extended=U.w(4)
    fifo_pos=U.w(2)
    instr=Vec(4,32)
    cf=Vec(4,3)
    #replay interface
    instr_overflow_fifo=U.w(2)

    CT_F={'NoCF':U.w(3)(0),'Branch':U.w(3)(1),'Jump':U.w(3)(2),'JumpR':U.w(3)(3),'Return':U.w(3)(4)}
    ready_o <<= ~OR(instr_queue_full,2) & (~full_address)
    for i in range(2):
        taken[i]<<=cf_type_i[i]!=CT_F['NoCF'] 
    

    #================  lzc========================
    i_lzc_branch_index=lzc(2,False)
    i_lzc_branch_index.io.in_i<<=taken
    branch_index<<=i_lzc_branch_index.io.cnt_o
    branch_empty<<=i_lzc_branch_index.io.empty_o
   
    
    
    branch_mask_extended<<=U.w(3)(3)<<branch_index
    branch_mask<<=branch_mask_extended[2:1]
    valid<<=io.valid_i & branch_mask
    consumed_extended<<=CatBits(push_instr_fifo, push_instr_fifo)>> idx_is_q
    io.consumed_o <<=consumed_extended[1:0]

    #===============popcount===================


    shamt=popcount[0]
    idx_is_d = idx_is_q + shamt
    fifo_pos_extended=CatBits(valid, valid)<<idx_is_q
    fifo_pos=fifo_pos_extended[3:2]
    push_instr=fifo_pos & ~instr_queue_full

    for i in range(2):
        instr[i] = io.instr_i[i]
        instr[i + 2] = io.instr_i[i]
        cf[i] = io.cf_type_i[i]
        cf[i + 2] = cf_type_i[i]
    
    for i in range(2):
        instr_data_in[i].instr=instr[i + idx_is_q]
        instr_data_in[i].cf = cf[i + idx_is_q]
        instr_data_in[i].ex = io.exception_i
    instr_overflow_fifo = instr_queue_full & fifo_pos
    instr_overflow = OR(instr_overflow_fifo,2)
    address_overflow = full_address & push_address
    replay_o = instr_overflow | address_overflow
    replay_addr_o=Mux(address_overflow,addr_i[0],addr_i[shamt])
    io.fetch_entry_valid_o<< = ~AND(instr_queue_empty,2)

    dx_ds_d = idx_ds_q
    pop_instr=U(0)#?
    io.instruction<<=U(0)#?
    io.address<<=pc_q
    io.ex_valid<<=U(0)
    io.ex_cause<<=U.w(64)(12)
    io.ex_tval<<=U(0)#?
    io.predict_address<<=address_out
    io.b_cf<<=CT_F['NoCF']

    for i in range(2):
        if(idx_ds_q[i]):
            io.instruction<<=instr_data_in[i].instr
            io.ex_valid<<=instr_data_in[i].ex
            io.ex_tval<<=pc_q
            io.b_cf<<=instr_data_out[i].cf
            pop_instr[i]<<=io.fetch_entry_valid_o&io.fetch_entry_ready_i
    
    if(fetch_entry_ready_i):
        pc_d<<=pc_q+Mux((io.instruction[1:0]!=U(3)),U(2),U(4))
    if(pop_address):
        pc_d<<=address_out
        if (io.valid_i[0]  and  reset_address_q):
            pc_d<<=io.addr_i[0]
            reset_address_d<<=U.w(1)(0)
    
    for i in range(2):
        push_instr_fifo[i] <<= push_instr[i] & ~address_overflow
        #===================fifo_v3=====================
    
    push_address=U.w(1)(0)
    for i in range(2):
        push_address=push_address|(push_instr[i] &(instr_data_in[i].cf!=CT_F['NoCF']))
    
    #===================fifo_v3=========================
         
#***********黄铭绚 8.31 End***********#            

            
            
            

    







    

    




   

