# P0: Physical Constraint and Floorplan User Guide
# (紫光同创 PDS 物理位置锁定与平面规划指南)

> **目标芯片**：紫光同创 Logos-2 系列 (PG2L200H / 盘古 200Pro)  
> **核心任务**：LOC 物理锁定、Pblock/Region 区域划分约束、宏模块相对位置约束 (RPM)、DRM/APM/IO 布局规划。

---

## 一、 LOC 物理位置锁定核心语法

在 PDS `.fdc` 约束中，所有物理底层单元的位置锁定统一采用 `define_attribute` 语法：

### 1. I/O 引脚锁定 (Primary I/O Port)
```tcl
# 语法: define_attribute {p:<port_name>} {PAP_IO_LOC} {<PACKAGE_PIN>}
define_attribute {p:sys_clk}       {PAP_IO_LOC} {Y12}
define_attribute {p:cam_data[0]}   {PAP_IO_LOC} {U14}
define_attribute {p:cam_data[1]}   {PAP_IO_LOC} {U15}
```

### 2. 块存储器 (DRM 18K/36K) 锁定
```tcl
# 语法: define_attribute {i:<instance_path>} {PAP_LOC} {DRM_X<x>Y<y>}
define_attribute {i:u_video_cache/mem_reg}  {PAP_LOC} {DRM_X2Y10}
```

### 3. 硬件乘加器 (APM DSP48) 锁定
```tcl
# 语法: define_attribute {i:<instance_path>} {PAP_LOC} {APM_X<x>Y<y>}
define_attribute {i:u_pe_core/mult_reg}     {PAP_LOC} {APM_X1Y8}
```

### 4. 逻辑单元 (Slice / DFF) 锁定
```tcl
# 语法: define_attribute {i:<instance_path>} {PAP_LOC} {SLICE_X<x>Y<y>}
define_attribute {i:u_fsm/state_reg[0]}     {PAP_LOC} {SLICE_X25Y40}
```

---

## 二、 Pblock / Region 区域约束 (Floorplanning)

当工程规模较大或不同子系统（如视频输入流、AI 加速核、HDMI 显存控制器）之间相互干扰导致布局抖动时，必须通过 `Pblock` 将逻辑模块划定在指定的物理矩形区域内。

### 1. Pblock 标准约束模板
```tcl
# 1. 创建物理逻辑块 Pblock
create_pblock pblock_ai_engine

# 2. 为 Pblock 分配物理切片 (Slice) 坐标范围 [Xmin:Xmax, Ymin:Ymax]
add_pblock_range -pblock pblock_ai_engine {SLICE_X20Y30:SLICE_X50Y70}

# 3. 若模块包含片上 BRAM，必须分配对应的 DRM 列范围
add_pblock_range -pblock pblock_ai_engine {DRM_X1Y10:DRM_X2Y25}

# 4. 若模块包含乘法器，必须分配对应的 APM 列范围
add_pblock_range -pblock pblock_ai_engine {APM_X1Y10:APM_X1Y20}

# 5. 将 RTL 中的层次化模块实例化绑定到该 Pblock
add_pblock_instance -pblock pblock_ai_engine {u_gesture_top/u_lenet5_core}
```

### 2. Pblock 规划三大铁律
1. **留出 20% 空间裕量**：Pblock 内部的 LUT 使用率不要超过 80%，否则该区域容易成为局部高阻拥塞死区。
2. **就近原则 (Affinity)**：与摄像头 IO 交互的预处理模块（YCrCb、二值化）放置在靠近 IO 引脚的芯片边缘区域；与计算相关的内部核（CNN、矩阵运算）集中在芯片中央。
3. **跨时钟域模块物理隔离**：将属于不同主频时钟域的模块放在不同的 Pblock 中，避免由于布线杂乱拉高时钟偏斜（Clock Skew）。

---

## 三、 宏模块相对位置约束 (RPM - Relative Placement Macro)

对于关键的高速数据通路（如 16 级脉动阵列、移位寄存器或加法树），如果希望各个触发器在 P&R 时始终保持固定不变的相对几何位置，可以在 Verilog 源码中嵌入 `RLOC` 属性：

```verilog
// 在 Verilog 源码中指定相对位置
(* RLOC = "X0Y0" *) reg [7:0] pipe_stage0;
(* RLOC = "X0Y1" *) reg [7:0] pipe_stage1;
(* RLOC = "X0Y2" *) reg [7:0] pipe_stage2;
```
这样布局布线器无论将该模块移动到芯片的哪个区域，这三级流水寄存器之间的布线延迟都将保持严格一致。
