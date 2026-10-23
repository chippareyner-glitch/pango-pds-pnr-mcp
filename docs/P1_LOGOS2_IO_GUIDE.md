# P1: Logos-2 I/O Interface and Pin Packing Guide (UG040006)
# (紫光同创 Logos-2 系列输入输出接口与引脚打包指南)

> **目标芯片**：紫光同创 Logos-2 系列 (PG2L200H / 盘古 200Pro)  
> **核心任务**：解决管脚电平冲突、IO 寄存器无法打入 IOB 导致的输入/输出建立保持时间违例。

---

## 一、 I/O Bank 物理分布与供电电压 (VCCIO) 铁律

PG2L200H-FBB484 划分为 6 个主要通用 IO Bank（Bank 0 至 Bank 5）：

1. **单 Bank 统一电平原则**：
   * 同一个 IO Bank 内的所有管脚必须由同一个物理引脚供电。
   * **绝对禁止**在同一个 Bank 内混合分配不同供电电压标准的引脚（例如同时分配 3.3V 的 `LVCMOS33` 和 1.5V 的 `SSTL15`）。
2. **违规后果**：PDS 在 `dev_map` 阶段会直接报错中断编译：
   ```text
   ERROR [DRC_IO_004]: Bank VCCIO conflict detected on BANK_2.
   Port 'mem_dq[0]' requires VCCIO=1.5V, but port 'uart_txd' requires VCCIO=3.3V.
   ```
3. **分配规范建议**：
   * Bank 0 / Bank 1：分配给 3.3V 摄像头传感器 DVP、HDMI 发送、UART、按键/LED。
   * Bank 2 / Bank 3：专供 DDR3 存储器接口（统一 1.5V SSTL15）。
   * Bank 4 / Bank 5：分配给 1.8V/2.5V 差分 LVDS 接口或千兆以太网 RGMII。

---

## 二、 ILOGIC / OLOGIC 寄存器打包 (IOB Register Packing)

### 1. 为什么必须将寄存器打入 IOB？
* **未打入 IOB**：输入数据必须从管脚经过一段芯片内部布线金属线（延迟 1.5~3.5ns），再进入内部 Slice 触发器。布线延迟随编译批次剧烈波动，输入建立保持时间极难收敛。
* **成功打入 IOB**：触发器物理位于 IO Pad 焊盘的正下方，没有内部布线延迟，时钟到输出延迟 $T_{co}$ 与输入建立时间 $T_{su}$ 达到皮秒级（ps）极致稳定。

### 2. 打入 IOB 的必备条件
1. 寄存器必须直接与顶层 I/O 端口相连，**中间绝对不能有任何 LUT 组合逻辑门**。
2. 寄存器输出不能既连管脚，又分叉去驱动内部其他逻辑模块（若有分叉，需在 RTL 中显式复制一个独立寄存器专门负责给管脚输出）。
3. 寄存器的复位信号类型与极性需匹配 IOB 硬件支持的异步/同步复位。

### 3. FDC 强制打包属性
```tcl
# 强制将摄像头输入数据总线的输入打拍寄存器吸收进 ILOGIC
define_attribute {p:cam_data[*]} {PAP_IOB_REG} {TRUE}
```
并在 Verilog 源码中辅助声明：
```verilog
(* IOB = "TRUE" *) reg [7:0] cam_data_in_d1;
always @(posedge cam_pclk) begin
    cam_data_in_d1 <= cam_data;
end
```

---

## 三、 IODELAY 硬件可编程微调延时

在千兆以太网（RGMII）或高速并行摄像头接口中，时钟与数据存在几十到几百皮秒的布线偏斜：
* 每个 I/O Pad 均配备 64/128 级抽头（Tap）的硬件 IODELAY 单元，单级延时精度约为 25ps ~ 50ps。
* 可在 RTL 中例化 `IODELAY` 原语，通过静态参数或动态状态机调整抽头数值，将时钟边沿精确挪移至数据眼图的中心位置。
