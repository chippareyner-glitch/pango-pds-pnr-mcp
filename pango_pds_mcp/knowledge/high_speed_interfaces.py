"""
PanGo Logos-2 High-Speed Interfaces Knowledge Base: DDR3 HMIC IP & GTP HSSTLP (UG040007).
Contains Placement & Route constraints for onboard DDR3, PCIe, and SFP+ transceivers on Pangu 200Pro.
"""

from typing import Dict, List, Any

DDR3_HMIC_PNR_RULES = {
    "ip_architecture": "HMIC_S/H (Hard Memory Interface Controller)",
    "hard_macro_location": "Directly adjacent to IO Bank 2 / Bank 3 on PG2L200H.",
    "byte_lane_rules": [
        "DQ[7:0] and DM0 must strictly reside in the same physical DQS0 byte group.",
        "DQ[15:8] and DM1 must strictly reside in the DQS1 byte group.",
        "Crossing byte lanes triggers fatal PDS DRC error: 'DDR3 Data Lane Mismatch'."
    ],
    "essential_fdc_attributes": [
        "define_attribute {p:mem_dqs[0]} {PAP_IO_STANDARD} {SSTL15}",
        "define_attribute {p:mem_dqs[0]} {PAP_IO_DIFF_PAIR} {TRUE}",
        "define_attribute {p:mem_dq[*]} {PAP_IO_STANDARD} {SSTL15}",
        "define_attribute {p:mem_dq[*]} {PAP_IO_VCCIO} {1.5}",
        "define_attribute {p:mem_dq[*]} {PAP_IO_SLEW} {FAST}",
        "define_attribute {i:u_ddr3_controller/u_hmic} {PAP_LOC} {HMIC_X0Y0}"
    ]
}

GTP_HSSTLP_PNR_RULES = {
    "transceiver_type": "HSSTLP (High Speed Serial Transceiver Low Power)",
    "capabilities": "Up to 6.375 Gbps per lane. Supports PCIe Gen1/Gen2, SFP+ 1G/2.5G/5G Ethernet.",
    "quad_location_constraints": {
        "channel_0": "define_attribute {i:u_gtp_top/u_hsstlp_channel0} {PAP_LOC} {HSSTLP_X0Y0}",
        "channel_1": "define_attribute {i:u_gtp_top/u_hsstlp_channel1} {PAP_LOC} {HSSTLP_X0Y1}",
        "channel_2": "define_attribute {i:u_gtp_top/u_hsstlp_channel2} {PAP_LOC} {HSSTLP_X0Y2}",
        "channel_3": "define_attribute {i:u_gtp_top/u_hsstlp_channel3} {PAP_LOC} {HSSTLP_X0Y3}"
    },
    "refclk_rules": [
        "Reference clock must enter via dedicated pins: HSST_REFCLK0_P / HSST_REFCLK0_N.",
        "Do NOT route HSSTLP reference clock through general fabric routing tracks.",
        "Clock jitter on refclk must be < 1.0ps RMS to achieve target BER < 1e-12."
    ]
}

def get_high_speed_pnr_template(interface_type: str) -> str:
    """Returns synthesizable FDC template for DDR3 or GTP interfaces."""
    if interface_type.lower() == "ddr3":
        return "\n".join(DDR3_HMIC_PNR_RULES["essential_fdc_attributes"])
    elif interface_type.lower() in ["gtp", "pcie", "sfp", "hsstlp"]:
        lines = ["# HSSTLP Quad Physical Location Locking"]
        for ch, syntax in GTP_HSSTLP_PNR_RULES["quad_location_constraints"].items():
            lines.append(syntax)
        return "\n".join(lines)
    return "# Unknown interface. Specify 'ddr3' or 'gtp'."
