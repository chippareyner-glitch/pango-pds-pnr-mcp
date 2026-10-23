# P1: PG2L200H-FBB484 Pinout and Package Specification (PK04009)
# (紫光同创 PG2L200H-FBB484 封装管脚与专用引脚映射全解)

> **封装规格**：FBB484 (Fine-pitch BGA，484 球，1.0mm 间距，22x22 矩阵)  
> **芯片型号**：紫光同创 Logos-2 PG2L200H  
> **核心用途**：在布局布线前校验管脚物理合法性，严禁普通 I/O 占用专用时钟与 DQS 通道。

---

## 一、 IO Bank 物理分布与主要功能划分

```text
                  [ TOP: BANK_0 (3.3V) ]   |   [ TOP: BANK_1 (3.3V) ]
               +-----------------------------------------------------+
               |                                                     |
 [ LEFT:       |   专用时钟: Y12/Y13 (GCLK0)      专用时钟: B10/A10 (GCLK2)  |  [ RIGHT:
   BANK_5      |            W11/W12 (GCLK1)               C11/C12 (GCLK3)  |    BANK_2 (DDR3)
   (3.3V)      |                                                     |    Byte 0: DQS0=M2/M1
   通用 GPIO   |               紫光同创 PG2L200H 逻辑阵列               |    Byte 1: DQS1=K2/K1
   HDMI/UART   |              (196,800 LUT5 + 840 DRM18K)            |    统一 1.5V SSTL15 ]
               |                                                     |
               |   HSSTLP SerDes Quad (PCIe Gen2 / SFP+ 光口通道)     |  [ BOTTOM RIGHT:
 [ BOTTOM LEFT:|   专用参考时钟: HSST_REFCLK_P/N                       |    BANK_3 (DDR3)
   BANK_4      |                                                     |    控制/地址总线 ]
   (1.8/3.3V) ]+-----------------------------------------------------+
```

---

## 二、 关键专用引脚速查表 (Dedicated Pins)

### 1. 全局时钟专用差分对输入管脚 (Global Clock Inputs)
| 引脚球号 | 硬件引脚全名 | 所属 Bank | 推荐连接功能 | 硬件注意事项 |
| :---: | :---: | :---: | :---: | :--- |
| **`Y12`** | `IO_L1P_GCLK_0` | BANK_0 | 系统主晶振输入 (P端) | **强烈推荐**作为板载 50MHz/100MHz 主时钟输入引脚！ |
| **`Y13`** | `IO_L1N_GCLK_0` | BANK_0 | 系统主晶振输入 (N端) | 差分晶振时使用，单端时可作为普通 IO。 |
| **`W11`** | `IO_L2P_GCLK_1` | BANK_0 | 备用时钟 / 外部同步时钟 | 可直连 Bank 0 的 GPLL0 专用输入端。 |
| **`B10`** | `IO_L1P_GCLK_2` | BANK_1 | 摄像头传感器 PCLK 输入 | 直连摄像头像元时钟，零布线违例。 |
| **`C11`** | `IO_L2P_GCLK_3` | BANK_1 | 外部以太网 RXC 时钟输入 | 走线直达千兆 RGMII 接收逻辑。 |

### 2. DDR3 存储器硬件专用选通管脚 (DQS & Byte Group)
| 字节组 | DQS 差分选通管脚 | 数据掩码 DM | 数据总线 DQ[7:0] 引脚列表 | 所在 Bank |
| :---: | :---: | :---: | :---: | :---: |
| **Byte 0** | **`M2`** (P) / **`M1`** (N) | **`N3`** | `P1, P2, R1, T1, P3, R2, T2, U1` | BANK_2 (1.5V) |
| **Byte 1** | **`K2`** (P) / **`K1`** (N) | **`L3`** | `J1, J2, H1, H2, K3, L1, L2, M3` | BANK_2 (1.5V) |

> ⚠️ **致命违例警告**：DQ 数据线必须严格隶属于其对应的 DQS 所在组！若将 `P1` (Byte 0) 误配给 DQS1 控制，硬件硬件培训（Calibration）将 100% 失败。

### 3. 高速串行收发器 (HSSTLP SerDes)
* **PCIe / SFP+ 差分收发通道**：位于芯片专用 SerDes Quad 物理硬核区域。
* **参考时钟**：必须通过专用的 `HSST_REFCLK_P` 和 `HSST_REFCLK_N` 接入（抖动 < 1ps RMS）。
