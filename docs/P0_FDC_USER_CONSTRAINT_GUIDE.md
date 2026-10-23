# P0: User Constraint (.fdc) Complete Syntax & XDC Migration Guide
# (紫光同创 PDS 用户约束 .fdc 语法全解与 XDC 避坑指南)

> **核心目标**：彻底纠正误用 Vivado XDC 语法的习惯，写出 100% 驱动 PDS 布局布线时序收敛的标准 `.fdc` 约束。

---

## 一、 Vivado XDC 与 PanGo FDC 语法全面对照表 (Syntax Comparison)

| 约束类型 | Vivado XDC 语法 (错误示范❌) | PanGo PDS .fdc 标准语法 (正确示范✅) |
| :--- | :--- | :--- |
| **物理引脚绑定** | `set_property PACKAGE_PIN Y12 [get_ports clk]` | `define_attribute {p:clk} {PAP_IO_LOC} {Y12}` |
| **IO 电平标准** | `set_property IOSTANDARD LVCMOS33 [get_ports clk]` | `define_attribute {p:clk} {PAP_IO_STANDARD} {LVCMOS33}` |
| **IO 供电电压** | *(XDC 通常省略或隐含于 IOSTANDARD)* | `define_attribute {p:clk} {PAP_IO_VCCIO} {3.3}` |
| **弱上拉使能** | `set_property PULLUP true [get_ports scl]` | `define_attribute {p:scl} {PAP_IO_PULLUP} {TRUE}` |
| **驱动电流强度**| `set_property DRIVE 8 [get_ports txd]` | `define_attribute {p:txd} {PAP_IO_DRIVE} {8}` |
| **输出压摆率** | `set_property SLEW FAST [get_ports hsync]` | `define_attribute {p:hsync} {PAP_IO_SLEW} {FAST}` |
| **差分端接电阻**| `set_property DIFF_TERM TRUE [get_ports lvds_p]` | `define_attribute {p:lvds_p} {PAP_IO_DIFF_TERM} {TRUE}` |
| **IO 寄存器打包**| `set_property IOB TRUE [get_ports din]` | `define_attribute {p:din} {PAP_IOB_REG} {TRUE}` |
| **主时钟定义** | `create_clock -period 20.0 -name clk [get_ports clk]` | `create_clock -name {clk} -period {20.000} [get_ports {clk}]` |
| **异步时钟域隔离**| `set_clock_groups -async -group [get_clocks c1] -group [get_clocks c2]` | `set_clock_groups -asynchronous -group [get_clocks {c1}] -group [get_clocks {c2}]` |
| **假路径屏蔽** | `set_false_path -from [get_pins p1] -to [get_pins p2]` | `set_false_path -from [get_pins {p1}] -to [get_pins {p2}]` |

---

## 二、 PanGo PDS .fdc 约束完整规范工程模板

```tcl
# ==============================================================================
# PanGo PDS 综合与布局布线标准约束文件 (constraints.fdc)
# Target: PanGo Logos-2 PG2L200H-6FBB484
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. 基础主时钟定义 (Primary Clocks)
# ------------------------------------------------------------------------------
create_clock -name {clk_50m}   -period {20.000} [get_ports {clk_50m}]
create_clock -name {cam_pclk}  -period {13.468} [get_ports {cam_pclk}]   ;# 74.25MHz

# ------------------------------------------------------------------------------
# 2. 时钟不确定度 (Clock Uncertainty / Jitter)
# ------------------------------------------------------------------------------
set_clock_uncertainty -setup 0.150 [get_clocks {clk_50m}]
set_clock_uncertainty -setup 0.150 [get_clocks {cam_pclk}]

# ------------------------------------------------------------------------------
# 3. 异步时钟域解耦 (Asynchronous Clock Groups)
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous \
    -group [get_clocks {clk_50m}] \
    -group [get_clocks {cam_pclk}]

# ------------------------------------------------------------------------------
# 4. 静态复位与调试假路径 (False Paths)
# ------------------------------------------------------------------------------
set_false_path -from [get_ports {rst_n_key}]
set_false_path -to   [get_ports {led_status[*]}]

# ------------------------------------------------------------------------------
# 5. 关键 I/O 物理位置与电平约束
# ------------------------------------------------------------------------------
# 系统主时钟 (专用 GCLK 输入管脚)
define_attribute {p:clk_50m}         {PAP_IO_LOC}      {Y12}
define_attribute {p:clk_50m}         {PAP_IO_VCCIO}    {3.3}
define_attribute {p:clk_50m}         {PAP_IO_STANDARD} {LVCMOS33}

# 复位按键 (普通 IO, 带弱上拉)
define_attribute {p:rst_n_key}       {PAP_IO_LOC}      {K18}
define_attribute {p:rst_n_key}       {PAP_IO_VCCIO}    {3.3}
define_attribute {p:rst_n_key}       {PAP_IO_STANDARD} {LVCMOS33}
define_attribute {p:rst_n_key}       {PAP_IO_PULLUP}   {TRUE}

# 摄像头数据总线 (强制打入 IOB 寄存器以最小化输入建立时间偏差)
define_attribute {p:cam_data[0]}     {PAP_IO_LOC}      {U14}
define_attribute {p:cam_data[0]}     {PAP_IO_VCCIO}    {3.3}
define_attribute {p:cam_data[0]}     {PAP_IO_STANDARD} {LVCMOS33}
define_attribute {p:cam_data[0]}     {PAP_IOB_REG}     {TRUE}
```
