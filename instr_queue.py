#***********黄铭绚 8.31 Begin***********#

from pyhcl import *
from popcount import *
from lzc import *
import math
from fifo_v3 import *


class instr_data_t:
    instr=Reg(U.w(32))
    cf=Reg(U.w(3))
    ex=Reg(U.w(1))

class unread(Module):
    io=IO(
        d_i=Input(U.w(1))
    )


def OR(a,length):
    for i in range(length):
        with when(a[i]==True):
            return True
    return False

def AND(a,length):
    for i in range(length):
        with when(a[i]==False):
            return False
    return True

def onhot0(a,width):
    count=0
    for i in range(width):
        with when(a[i]==U.w(1)(1)):
            count+=1
        with when(count>1):
            return False
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
    instr_queue_usage=Wire(Vec(2,4))
    instr_data_in=[]
    instr_data_out=[]
    for i in range(2):
        instr_data_in[i]=instr_data_t()
        instr_data_out[i]=instr_data_t()
    push_instr=Wire(U.w(2))
    push_instr_fifo=Wire(U.w(2))
    pop_instr=Wire(U.w(2))
    instr_queue_full=Wire(U.w(2))
    instr_queue_empty=Wire(U.w(2))
    instr_overflow=Wire(U.w(1))
    #address queue
    address_queue_usage=Wire(U.w(4))
    address_out=Wire(U.w(64))
    pop_address=Wire(U.w(1))
    push_address=Wire(U.w(1))
    full_address=Wire(U.w(1))
    empty_address=Wire(U.w(1))
    address_overflow=Wire(U.w(1))
    #input stream counter
    idx_is_d=Wire(U.w(1))
    idx_is_q=Reg(U.w(1))#2

    #register
    #output FIFO select, one-hot
    idx_ds_d=Wire(U.w(2))
    idx_ds_q=Reg(U.w(2))#1
    #current PC
    pc_d=Wire(U.w(64))
    pc_q=Reg(U.w(64))#3
    #we need to re-set the address because of a flush
    reset_address_d=Wire(U.w(1))
    reset_address_q=Reg(U.w(1))#4
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
    fifo_pos_extended=Wire(U.w(4))
    fifo_pos=Wire(U.w(2))
    instr=Wire(Vec(4,32))
    cf=Wire(Vec(4,3))
    #replay interface
    instr_overflow_fifo=Wire(U.w(2))

    CT_F={'NoCF':U.w(3)(0),'Branch':U.w(3)(1),'Jump':U.w(3)(2),'JumpR':U.w(3)(3),'Return':U.w(3)(4)}
    ready_o <<= ~OR(instr_queue_full,2) & (~full_address)
    for i in range(2):
        taken[i]<<=cf_type_i[i]!=CT_F['NoCF'] 
    

    #================  lzc========================
    i_lzc_branch_index=LZC(2,False)
    i_lzc_branch_index.io.in_i<<=taken
    branch_index<<=i_lzc_branch_index.io.cnt_o
    branch_empty<<=i_lzc_branch_index.io.empty_o
   
    
    
    branch_mask_extended<<=U.w(3)(3)<<branch_index
    branch_mask<<=branch_mask_extended[2:1]
    valid<<=io.valid_i & branch_mask
    consumed_extended<<=CatBits(push_instr_fifo, push_instr_fifo)>> idx_is_q
    io.consumed_o <<=consumed_extended[1:0]

    #===============popcount===================
    i_popcount=popcountAdder(2)
    i_popcount.io.data_i<<=push_instr_fifo
    popcount<<=i_popcount.io.popcount_o


    shamt<<=popcount[0]
    idx_is_d <<= idx_is_q + shamt
    fifo_pos_extended<<=CatBits(valid, valid)<<idx_is_q
    fifo_pos<<=fifo_pos_extended[3:2]
    push_instr<<=fifo_pos & ~instr_queue_full

    for i in range(2):
        instr[i] <<= io.instr_i[i]
        instr[i + 2] <<= io.instr_i[i]
        cf[i] <<= io.cf_type_i[i]
        cf[i + 2] <<= cf_type_i[i]
    
    for i in range(2):
        instr_data_in[i].instr<<=instr[i + idx_is_q]
        instr_data_in[i].cf <<= cf[i + idx_is_q]
        instr_data_in[i].ex <<= io.exception_i
    instr_overflow_fifo <<= instr_queue_full & fifo_pos
    instr_overflow <<= OR(instr_overflow_fifo,2)
    address_overflow <<= full_address & push_address
    replay_o <<= instr_overflow | address_overflow
    replay_addr_o<<=Mux(address_overflow,addr_i[0],addr_i[shamt])
    io.fetch_entry_valid_o<< = ~AND(instr_queue_empty,2)

    dx_ds_d <<= idx_ds_q
    pop_instr<<=U(0)#?
    io.instruction<<=U(0)#?
    io.address<<=pc_q
    io.ex_valid<<=U(0)
    io.ex_cause<<=U.w(64)(12)
    io.ex_tval<<=U(0)#?
    io.predict_address<<=address_out
    io.b_cf<<=CT_F['NoCF']

    for i in range(2):
        with when(idx_ds_q[i]):
            io.instruction<<=instr_data_in[i].instr
            io.ex_valid<<=instr_data_in[i].ex
            io.ex_tval<<=pc_q
            io.b_cf<<=instr_data_out[i].cf
            pop_instr[i]<<=io.fetch_entry_valid_o&io.fetch_entry_ready_i
    
    with when(fetch_entry_ready_i):
        pc_d<<=pc_q+Mux((io.instruction[1:0]!=U(3)),U(2),U(4))
    with when(pop_address):
        pc_d<<=address_out
    with when(io.valid_i[0]  and  reset_address_q):
        pc_d<<=io.addr_i[0]
        reset_address_d<<=U.w(1)(0)
    
    for i in range(2):
        push_instr_fifo[i] <<= push_instr[i] & ~address_overflow
        #===================fifo_v3=====================
        i_fifo_instr_data=fifo_v3(4,instr_data_t)
        i_fifo_instr_data.flush_i<<=io.flush_i
        i_fifo_instr_data.testmode_i<<=U(0)
        instr_queue_full[i]<<=i_fifo_instr_data.full_o
        instr_queue_empty[i]<<=i_fifo_instr_data.empty_o
        instr_queue_usage[i]<<=i_fifo_instr_data.usage_o
        i_fifo_instr_data.data_i<<=instr_data_in[i] 
        i_fifo_instr_data.push_i<<=push_instr_fifo[i]
        instr_data_out[i]<<=i_fifo_instr_data..data_o
        i_fifo_instr_data.pop_i<<=pop_instr[i]
    
    push_address<<=U.w(1)(0)
    for i in range(2):
        push_address<<=push_address|(push_instr[i] &(instr_data_in[i].cf!=CT_F['NoCF']))
    
    #===================fifo_v3=========================
    i_fifo_address=fifo_v3(4,64)
    i_fifo_address.flush_i<<=io.flush_i
    i_fifo_address.testmode_i<<=U(0)
    full_address<<=i_fifo_address.full_o
    empty_address<<=i_fifo_address.empty_o 
    address_queue_usage<<=i_fifo_address.usage_o
    i_fifo_address.data_i<<=predict_address_i 
    i_fifo_address.push_i<<=push_address & ~full_address
    address_out<<=i_fifo_address.data_o
    i_fifo_address.pop_i<<=pop_address
        
    i_unread_address_fifo=unread()
    i_unread_address_fifo.io.d_i<<=OR(CatBits(empty_address, address_queue_usage),5)  
    i_unread_branch_mask=unread()
    i_unread_branch_mask.io.d_i<<=OR(branch_mask_extended,3)
    i_unread_lzc=unread()
    i_unread_lzc.io.d_i<<=OR(branch_empty,1)
    i_unread_fifo_pos=unread()
    i_unread_fifo_pos.io.d_i<<=OR(fifo_pos_extended,4)
    i_unread_instr_fifo=unread()
    k=Wire(U.w(1))
    k<<=OR(instr_queue_usage[0],4)|OR(instr_queue_usage[1],4)
    i_unread_instr_fifo.io.d_i<<=k

    with when(Module.reset == U(0)):
        idx_ds_q<<=U(1)
        idx_is_q<<=U(0)
        pc_q<<=U(0)
        reset_address_q<<=U(1)
    with otherwise():
        pc_q<<=pc_d
        reset_address_q<<=reset_address_d
        with when(io.flush_i):
            idx_ds_q<<=U(1)
            idx_is_q<<U(0)
            reset_address_q<<=U(1)
        with otherwise():
            idx_ds_q<<=idx_ds_d
            idx_is_q<<=idx_is_d


#?????????????????
    with when(Module.clock==U(1)):
        assert Module.reset==U(0),print("[instr_queue] Pushing address although replay asserted")
        with when(replay_o):
            i_fifo_address.push_i=~i_fifo_address.push_i


    with when(Module.clock==U(1)):
        assert onhot0(idx_ds_q,2),"Output select should be one-hot encoded"
    
#***********黄铭绚 8.31 End***********#            



            
            

    







    

    




   

