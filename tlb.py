from pyhcl import *
import math

# ********** 徐琬玮 8.31 Begin ********** #
def tlb(TLB_ENTRIES: int = 4, ASID_WIDTH: int = 1):
    PLEN = 56

    class pte_t:
        reserved = Reg(Vec(10, U.w(1)))
        ppn = Reg(Vec(PLEN - 12, U.w(1)))
        rsw = Reg(Vec(2, U.w(1)))
        d = Reg(U.w(1))
        a = Reg(U.w(1))
        g = Reg(U.w(1))
        u = Reg(U.w(1))
        x = Reg(U.w(1))
        w = Reg(U.w(1))
        r = Reg(U.w(1))
        v = Reg(U.w(1))

    class bun:
        valid = Reg(U.w(1))
        is_2M = Reg(U.w(1))
        is_1G = Reg(U.w(1))
        vpn = Reg(Vec(27, U.w(1)))
        asid = Reg(Vec(ASID_WIDTH, U.w(1)))
        content = pte_t()

    class tlb_update_t:
        valid = Reg(U.w(1))
        is_2M = Reg(U.w(1))
        is_1G = Reg(U.w(1))
        vpn = Reg(Vec(27, U.w(1)))
        asid = Reg(Vec(ASID_WIDTH, U.w(1)))
        # TODO: type riscv::pte_t
        content = pte_t()

    class tlb2(Module):
        io = IO(
            clk_i=Input(U.w(1)),
            rst_ni=Input(U.w(1)),
            flush_i=Input(U.w(1)),
            # update tlb
            update_i=Input(tlb_update_t),
            # lookup signal
            lu_access_i=Input(U.w(1)),
            lu_asid_i=Input(U.w(1)),
            lu_vaddr_i=Input(U.w(1)),
            lu_content_o=Output(pte_t),
            lu_is_2M_o=Output(U.w(1)),
            lu_is_1G_o=Output(U.w(1)),
            lu_hit_o=Output(U.w(1))
        )

        bun = Bundle(
            asid=Vec(ASID_WIDTH, U.w(1)),
            vpn2=Vec(9, U.w(1)),
            vpn1=Vec(9, U.w(1)),
            vpn0=Vec(9, U.w(1)),
            is_2M=U.w(1),
            valid=U.w(1),
            is_1G=U.w(1)
        )
        tags_q = Reg(Vec(TLB_ENTRIES, bun))
        tags_n = Reg(Vec(TLB_ENTRIES, bun))

        content_q = Reg(Vec(TLB_ENTRIES, pte_t))
        content_n = Reg(Vec(TLB_ENTRIES, pte_t))
        vpn0 = Reg(Vec(9, U.w(1)))
        vpn1 = Reg(Vec(9, U.w(1)))
        vpn2 = Reg(Vec(9, U.w(1)))
        lu_hit = Reg(Vec(TLB_ENTRIES, U.w(1)))
        replace_en = Reg(Vec(TLB_ENTRIES, U.w(1)))

        # TODO: always_comb name translation
        # TODO: index upper lower?
        vpn0 <<= io.lu_vaddr_i[20:12]
        vpn1 <<= io.lu_vaddr_i[29:21]
        vpn2 <<= io.lu_vaddr_i[38:30]

        for i in range(TLB_ENTRIES):
            lu_hit[i] <<= U.w(1)(0)
        io.lu_hit_o <<= U.w(1)(0)
        # TODO: default assignment riscv::pte_t
        io.lu_content_o <<= U(0)
        io.lu_is_1G_o <<= U.w(1)(0)
        io.lu_is_2M_o <<= U.w(1)(0)

        # TODO: always_comb, translation part
        for i in range(TLB_ENTRIES):
            with when(tags_q[i].valid & io.lu_asid_i == tags_q[i].asid & vpn2 == tags_q[i].vpn2):
                with when(tags_q[i].is_1G):
                    io.lu_is_1G_o <<= U.w(1)(1)
                    io.lu_content_o <<= content_q[i]
                    io.lu_hit_o <<= U.w(1)(1)
                    lu_hit[i] <<= U.w(1)(1)
                with elsewhen(vpn1 == tags_q[i].vpn1):
                    with when(tags_q[i].is_2M | vpn0 == tags_q[i].vpn0):
                        io.lu_is_2M_o <<= tags_q[i].is_2M
                        io.lu_content_o <<= content_q[i]
                        io.lu_hit_o <<= U.w(1)(1)
                        lu_hit[i] <<= U.w(1)(1)

        # TODO: always_comb, update_flush part
        tags_n <<= tags_q
        content_n <<= content_q

        for i in range(TLB_ENTRIES):
            with when(io.flush_i):
                with when(io.lu_asid_i == U.w(1)(0)):
                    tags_n[i].valid <<= U.w(1)(0)
                with elsewhen(io.lu_asid_i == tags_q[i].asid):
                    tags_n[i].valid <<= U.w(1)(0)
            with otherwise():
                with when(io.update_i.valid & replace_en[i]):
                    tags_n[i].asid <<= io.update_i.asid
                    tags_n[i].vpn2 <<= io.update_i.vpn[26:18]
                    tags_n[i].vpn1 <<= io.update_i.vpn[17:9]
                    tags_n[i].vpn0 <<= io.update_i.vpn[8:0]
                    tags_n[i].is_1G <<= io.update_i.is_1G
                    tags_n[i].is_2M <<= io.update_i.is_2M
                    tags_n[i].valid <<= U.w(1)(1)
                    content_n[i] <<= io.update_i.content

        plru_tree_q = Reg(Vec(2 * (TLB_ENTRIES - 1), U.w(1)))
        plru_tree_n = Reg(Vec(2 * (TLB_ENTRIES - 1), U.w(1)))

        # TODO: always_comb, plru_replacement part
        plru_tree_n <<= plru_tree_q
        for i in range(TLB_ENTRIES):
            # TODO: automatic int unsigned
            idx_base = shift = new_index = 0
            with when(lu_hit[i] & io.lu_access_i):
                for lvl in range(int(math.log2(TLB_ENTRIES))):
                    idx_base = (2 ** lvl) - 1
                    shift = int(math.log2(TLB_ENTRIES) - lvl)
                    new_index = ~((i >> (shift - U(1))) & 1)
                    # TODO: type shift reg? int?
                    plru_tree_n[idx_base + (i >> shift)] <<= new_index[0]

        for i in range(TLB_ENTRIES):
            en = Reg(U.w(1))
            # TODO: automatic int unsigned
            idx_base = shift = new_index = 0
            en <<= U.w(1)(1)
            for lvl in range(int(math.log2(TLB_ENTRIES))):
                idx_base = (2 ** lvl) - 1
                shift = int(math.log2(TLB_ENTRIES) - lvl)
                new_index = (i >> (shift - 1)) & 1
                with when(new_index):
                    en &= plru_tree_q[idx_base + (i >> shift)]
                with otherwise():
                    en &= ~plru_tree_q[idx_base + (i >> shift)]
            replace_en[i] = en

        # TODO: sequential process always_ff
        # TODO: negedge
        with when(~io.rst_ni):
            # TODO: '{default: 0}
            tags_q <<= 0
            content_q <<= 0
            plru_tree_q <<= 0
        with otherwise():
            tags_q <<= tags_n
            content_q <<= content_n
            plru_tree_q <<= plru_tree_n

        # TODO: ifdef VERILATOR

        # TODO: initial begin
        # TODO: $stop()
        with when((TLB_ENTRIES % 2 != 0) | (TLB_ENTRIES <= 1)):
            print("TLB size must be a multiple of 2 and greater than 1")
        with when(ASID_WIDTH < 1):
            print("ASID width must be at least 1")

        def countSetBits(vect: Vec(TLB_ENTRIES, U.w(1))):
            count = 0
            for i in vect:
                count += i
            return count

        with when(countSetBits(lu_hit) > 1):
            print("More then one hit in TLB!")
        with when(countSetBits(replace_en) > 1):
            print("More then one TLB entry selected for next replace!")

    return tlb2()
# ********** 徐琬玮 8.28 End ********** #

if __name__ == '__main__':
    Emitter.dumpVerilog(Emitter.dump(Emitter.emit(tlb(4, 1)), "tlb.fir"))
