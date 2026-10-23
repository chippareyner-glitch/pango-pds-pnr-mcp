# P0: PDS Place & Route and Device Map Optimization User Guide
# (紫光同创 PDS 布局布线与器件映射优化指南)

> **目标芯片**：紫光同创 Logos-2 系列 (PG2L200H / 盘古 200Pro)  
> **核心任务**：时序驱动布局布线、布线拥塞缓解、pds_shell 自动化 Tcl 脚本与 .mrp/.prr 报告解析。

---

## 一、 Device Map (器件映射) 阶段核心参数与策略

器件映射阶段 (`dev_map`) 负责将综合后的网表逻辑门映射到 FPGA 底层的物理基本单元（LUT5、LUT6、DFF、Carry4、DRM18K、APM48）。

| 参数选项 | 可选值 | 推荐使用场景 | 硬件行为与影响 |
| :--- | :--- | :--- | :--- |
| `-effort` | `standard` \| `timing` \| `high` | 关键时钟 > 150MHz 时选 `timing` | 优先优化关键路径上的 LUT 级联级数，控制逻辑延迟在 4 级以内。 |
| `-optimize_drm` | `true` \| `false` | 包含大量片内 BRAM 时设为 `true` | 自动识别级联 RAM，开启硬核内部直连级联通道，规避布线资源消耗。 |
| `-optimize_apm` | `true` \| `false` | 使用 DSP48 做乘加流水线时设为 `true` | 将乘加操作打包进 APM 硬核，开启片内流水寄存器（AREG/BREG/MREG/PREG）。 |
| `-register_duplication` | `true` \| `false` | 高扇出网络引发延迟时设为 `true` | 物理映射层自动复制高扇出寄存器，将单个寄存器就近放置在多个逻辑簇旁。 |

---

## 二、 Place & Route (布局布线) 核心优化算法

布局布线 (`dev_pnr`) 决定了各个 Slice、DRM、APM 的具体物理坐标以及金属连线轨迹。

### 1. 布局阶段 (Placer)
* **时序驱动布局 (`-timing_effort timing_driven`)**：以 `.fdc` 中的时序约束为成本函数，优先将关键路径上的逻辑单元聚拢在同一个或相邻的 CLB Slice 内。
* **拥塞感知布局 (`-congestion_effort medium|high`)**：当芯片利用率超过 75% 时，Placer 会主动将密集逻辑打散（Logic Spreading），避免引脚过密导致后续 Router 无法布通。

### 2. 布线阶段 (Router)
* **多轮迭代拆线重布 (Rip-up and Reroute)**：遇到短路或时序违例的连线，自动拆除次要路径的走线，给时序最差网络让出直连高速走线。
* **热点消除 (`-hotspot_removal on`)**：对布线拥塞度达到 Level 4 以上的 Switchbox（开关矩阵）强制分散引流。

---

## 三、 pds_shell 自动化批处理与多种子探索脚本 (Multi-Seed DSE)

在终端或 CI/CD 流程中，使用 `pds_shell` 可脱离 GUI 实现一键编译与自动时序收敛：

```tcl
# ==============================================================================
# pds_shell 自动化批量多 Seed 探索脚本 (timing_dse.tcl)
# ==============================================================================
open_project -project pangu_top.pds

set SEED_LIST [list 1 7 13 42 100 128]
set TARGET_MET False

foreach seed $SEED_LIST {
    puts "--> Testing P&R with Seed: $seed"
    dev_pnr -opt_effort high -timing_effort timing_driven -congestion_effort medium -seed $seed
    
    # 提取 WNS (Worst Negative Slack)
    report_timing -setup -npaths 1 -file ./reports/setup_seed_${seed}.rpt
    # 若 WNS >= 0 则提前收敛
    set wns_val [get_timing_metric -wns]
    if {$wns_val >= 0.0} {
        puts "--> [SUCCESS] Timing closure achieved at Seed $seed (WNS = ${wns_val} ns)!"
        set TARGET_MET True
        break
    }
}
if {!$TARGET_MET} {
    puts "--> [WARNING] Timing not closed across all seeds. Consider RTL pipelining or Floorplan."
}
gen_bitstream
exit
```

---

## 四、 报告解读与故障诊断 (.mrp & .prr)

### 1. 器件映射报告 (.mrp) 关键指标
* **Slice / LUT5 利用率**：若 > 85%，布线拥塞概率剧增，必须在 `dev_pnr` 中开启 `-congestion_effort high`。
* **Registers not packed into IOB**：如果出现输入/输出寄存器未能打入 IOB，会导致输入建立时间 $T_{su}$ 或输出时钟到有效时间 $T_{co}$ 恶化 2~4ns。解决方法：在 `.fdc` 中为该管脚添加 `define_attribute {p:port} {PAP_IOB_REG} {TRUE}`。

### 2. 布局布线报告 (.prr) 关键指标
* **WNS (Worst Negative Slack)**：若为负值，表示建立时间违例（Setup Violation）。
  * 若“逻辑级数（Logic Levels）”大于 5，说明 RTL 中单周期组合逻辑过长，必须打拍。
  * 若“网络连线延迟占比（Net Delay %）”超过 65%，说明跨区域绕线过长，需要通过 `Pblock` 进行局部物理锁定。
* **WHS (Worst Hold Slack)**：若为负值，表示保持时间违例（Hold Violation）。通常发生在异步时钟域跨越未做假路径（False Path）隔离的场景下。
* **Unrouted Nets**：布线未完成。必须检查是否有非时钟管脚直接驱动全局时钟树，或者局部连线资源彻底耗尽。
