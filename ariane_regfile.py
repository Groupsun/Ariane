
from pyhcl import *
#********刘康杰 2020.8.31 Begin *******#
   #DATA_WIDTH     = 32
   #NR_READ_PORTS  = 2
   #NR_WRITE_PORTS = 2
   #ZERO_REG_ZERO  = 0
def Ariane_regfile_lol(DATA_WIDTH:int,NR_READ_PORTS:int,NR_WRITE_PORTS:int,ZERO_REG_ZERO:):
  # ZERO_REG_ZEROd的数据类型还没弄好 
    ADDR_WIDTH = 5
    NUM_WORDS  = 2**ADDR_WIDTH
  
    class ariane_regfile_lol(Module):
        io = IO(
            clk_i=Input(U.w(1)),
            
            rst_ni=Input(U.w(1)),
            
            test_en_i=Input(1),
            
            raddr_i=Input(Vec(NR_READ_PORTS,U.w(5))),

            rdata_o=Output(Vec(NR_READ_PORTS,U.w(DATA_WIDTH))),

            waddr_i=Input(Vec(NR_WRITE_PORTS,U.w(5))),
            
            wdata_i=Input(Vec(NR_WRITE_PORTS,U.w(DATA_WIDTH))),
            
            we_i=Input(U.w(NR_WRITE_PORTS))
            

        )


    mem_clocks= U.w(NUM_WORDS-ZERO_REG_ZERO)
    mem=Vec(NUM_WORDS,U.w(DATA_WIDTH))
    waddr_onehot=Vec(NR_WRITE_PORTS,U.w(NUM_WORDS))
    waddr_onehot_q=Vec(NR_WRITE_PORTS,U.w(NUM_WORDS))
    wdata_q=Vec(NR_WRITE_PORTS,U.w(DATA_WIDTH))

    for i in range(NR_READ_PORTS):
        rdata_o[i]<<=mem[raddr_i[i][ADDR_WIDTH-1:0]]
        #这里的连续赋值有点奇怪，估计要改
    #还未修改部分
    always_ff @(posedge clk_i, negedge rst_ni) begin : sample_waddr
        if (~rst_ni) begin
            wdata_q <= '0;
        end else begin
            for (int unsigned i = 0; i < NR_WRITE_PORTS; i++)
                // enable flipflop will most probably infer clock gating
                if (we_i[i]) begin
                    wdata_q[i]     <= wdata_i[i];
                end
            waddr_onehot_q <= waddr_onehot;
        end
    end


    always_comb begin : decode_write_addess
        for (int unsigned i = 0; i < NR_WRITE_PORTS; i++) begin
            for (int unsigned j = 1; j < NUM_WORDS; j++) begin
                if (we_i[i] && (waddr_i[i] == j))
                    waddr_onehot[i][j] = 1'b1;
                else
                    waddr_onehot[i][j] = 1'b0;
            end
        end
    end

   
    for (genvar x = ZERO_REG_ZERO; x < NUM_WORDS; x++) begin

        logic [NR_WRITE_PORTS-1:0] waddr_ored;

        for (genvar i = 0; i < NR_WRITE_PORTS; i++)
          assign waddr_ored[i] = waddr_onehot[i][x];

        cluster_clock_gating i_cg (
            .clk_i     ( clk_i         ),
            .en_i      ( |waddr_ored   ),
            .test_en_i ( test_en_i     ),
            .clk_o     ( mem_clocks[x] )
        );
    end


    always_latch begin : latch_wdata
   
        if (ZERO_REG_ZERO)
            mem[0] = '0;

        for (int unsigned i = 0; i < NR_WRITE_PORTS; i++) begin
            for (int unsigned k = ZERO_REG_ZERO; k < NUM_WORDS; k++) begin
                if (mem_clocks[k] && waddr_onehot_q[i][k])
                    mem[k] = wdata_q[i];
            end
        end
    end
    



    

    return ariane_regfile_lol()
#********刘康杰 2020.8.31 End *******#
