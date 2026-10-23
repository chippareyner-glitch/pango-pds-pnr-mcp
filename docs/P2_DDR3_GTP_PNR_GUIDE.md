# P2: DDR3 HMIC IP and GTP HSSTLP SerDes Placement & Route Guide
# (紫光同创 DDR3 内存与 GTP 高速串行收发器布局布线约束指南)

> **目标芯片**：紫光同创 Logos-2 系列 (PG2L200H / 盘古 200Pro)  
> **核心任务**：解决盘古 200Pro 板载 DDR3、PCIe 和 SFP 光口（HSSTLP）硬核通道的物理位置与布线报错。

---

## 一、 DDR3 HMIC 存储器控制器布局布线硬约束

盘古 200Pro 搭载的紫光同创硬核存储控制器（HMIC_S/H）在物理上紧贴芯片右侧的 Bank 2 和 Bank 3。

### 1. 必备 FDC 约束配置
```tcl
# ==============================================================================
# DDR3 HMIC_S/H 物理与时序约束 (严格区分 1.5V SSTL15)
# ==============================================================================

# 1. 内存硬核物理位置锁定
define_attribute {i:u_ddr3_top/u_hmic_inst} {PAP_LOC} {HMIC_X0Y0}

# 2. DQS 差分选通信号约束
define_attribute {p:mem_dqs[0]}  {PAP_IO_LOC}       {M2}
define_attribute {p:mem_dqs[0]}  {PAP_IO_STANDARD}  {SSTL15}
define_attribute {p:mem_dqs[0]}  {PAP_IO_DIFF_PAIR} {TRUE}
define_attribute {p:mem_dqs[1]}  {PAP_IO_LOC}       {K2}
define_attribute {p:mem_dqs[1]}  {PAP_IO_STANDARD}  {SSTL15}
define_attribute {p:mem_dqs[1]}  {PAP_IO_DIFF_PAIR} {TRUE}

# 3. DQ 数据信号约束 (必须匹配 Byte Group)
define_attribute {p:mem_dq[*]}   {PAP_IO_STANDARD}  {SSTL15}
define_attribute {p:mem_dq[*]}   {PAP_IO_VCCIO}     {1.5}
define_attribute {p:mem_dq[*]}   {PAP_IO_SLEW}      {FAST}

# 4. 参考电压 VREF 生成方式 (优先片上内部生成)
define_attribute {p:mem_vref}    {PAP_IO_VREF}      {INTERNAL}
```

### 2. 布局布线避坑技巧
* **不要在 DDR3 控制器与物理引脚之间加入任何布线层逻辑**，所有走线必须全部由 HMIC 专用的 IOCLK 与硬连线直通。
* 在 PDS 的 `dev_map` 选项中，确保开启 `-optimize_drm true`，允许读写双口 FIFO 使用内置专用缓冲。

---

## 二、 GTP / HSSTLP SerDes 收发器物理布局规划 (PCIe / SFP+)

PG2L200H 配备 4 通道 HSSTLP（单通道最高速率 6.375 Gbps），支持 PCIe Gen2 x1/x4 与 SFP+ 光口：

### 1. 通道物理位置锁定 (PAP_LOC)
收发器原语必须严格绑定到底层的 HSSTLP Quad 物理槽位：
```tcl
# 锁定 SFP+ 光口使用的收发器通道 0
define_attribute {i:u_sfp_top/u_hsstlp_lane0} {PAP_LOC} {HSSTLP_X0Y0}

# 若使用 PCIe x4，则锁定连续的 4 个物理通道
define_attribute {i:u_pcie_top/u_hsstlp_lane0} {PAP_LOC} {HSSTLP_X0Y0}
define_attribute {i:u_pcie_top/u_hsstlp_lane1} {PAP_LOC} {HSSTLP_X0Y1}
define_attribute {i:u_pcie_top/u_hsstlp_lane2} {PAP_LOC} {HSSTLP_X0Y2}
define_attribute {i:u_pcie_top/u_hsstlp_lane3} {PAP_LOC} {HSSTLP_X0Y3}
```

### 2. 高频参考时钟 (HSST_REFCLK) 约束原则
1. **严禁走普通布线层**：HSSTLP 差分参考时钟必须经由 `HSST_REFCLK0_P` / `HSST_REFCLK0_N` 专有引脚引入，绝不可先经过普通 IOB 缓冲再接入收发器。
2. **PCB 等长与去耦**：差分线对内等长误差严格控制在 5mil 以内，并串接 100nF 高频陶瓷交流耦合电容。
