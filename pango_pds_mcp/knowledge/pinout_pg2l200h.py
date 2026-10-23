"""
PanGo PG2L200H-FBB484 Package and Pinout Knowledge Base (PK04009).
Contains dedicated pin tables, Bank mappings, and pre-P&R legality checking.
"""

from typing import Dict, List, Any, Optional

PG2L200H_FBB484_SPECS = {
    "package": "FBB484 (Fine-Pitch Ball Grid Array, 1.0mm pitch, 22x22 matrix)",
    "die": "Logos-2 PG2L200H (200K LUT-equivalent logic cells)",
    "total_user_io": 284,
    "io_banks": {
        "BANK_0": {"location": "Top Left", "default_vccio": "3.3V", "supports_gclk": True, "supports_lvds": True},
        "BANK_1": {"location": "Top Right", "default_vccio": "3.3V", "supports_gclk": True, "supports_lvds": True},
        "BANK_2": {"location": "Right (Memory)", "default_vccio": "1.5V (DDR3)", "supports_dqs": True, "supports_ppll": True},
        "BANK_3": {"location": "Bottom Right (Memory)", "default_vccio": "1.5V (DDR3)", "supports_dqs": True, "supports_ppll": True},
        "BANK_4": {"location": "Bottom Left", "default_vccio": "1.8V / 3.3V", "supports_gclk": True, "supports_lvds": True},
        "BANK_5": {"location": "Left", "default_vccio": "3.3V", "supports_gclk": True, "supports_lvds": True}
    },
    "hsstlp_serdes_channels": 4, # Up to 6.375 Gbps per channel
    "dedicated_clock_pins": {
        "Y12": {"name": "IO_L1P_GCLK_0", "bank": "BANK_0", "type": "GCLK_PAIR_P"},
        "Y13": {"name": "IO_L1N_GCLK_0", "bank": "BANK_0", "type": "GCLK_PAIR_N"},
        "W11": {"name": "IO_L2P_GCLK_1", "bank": "BANK_0", "type": "GCLK_PAIR_P"},
        "W12": {"name": "IO_L2N_GCLK_1", "bank": "BANK_0", "type": "GCLK_PAIR_N"},
        "B10": {"name": "IO_L1P_GCLK_2", "bank": "BANK_1", "type": "GCLK_PAIR_P"},
        "A10": {"name": "IO_L1N_GCLK_2", "bank": "BANK_1", "type": "GCLK_PAIR_N"},
        "C11": {"name": "IO_L2P_GCLK_3", "bank": "BANK_1", "type": "GCLK_PAIR_P"},
        "C12": {"name": "IO_L2N_GCLK_3", "bank": "BANK_1", "type": "GCLK_PAIR_N"}
    },
    "dedicated_dqs_groups": {
        "BYTE_0": {
            "dqs_p": "M2", "dqs_n": "M1", "dm": "N3",
            "dq": ["P1", "P2", "R1", "T1", "P3", "R2", "T2", "U1"],
            "bank": "BANK_2"
        },
        "BYTE_1": {
            "dqs_p": "K2", "dqs_n": "K1", "dm": "L3",
            "dq": ["J1", "J2", "H1", "H2", "K3", "L1", "L2", "M3"],
            "bank": "BANK_2"
        }
    }
}

def check_pin_legality(pin_name: str, desired_function: str) -> Dict[str, Any]:
    """
    Checks if a physical pin on PG2L200H-FBB484 is legal for a given role:
    e.g. 'clock_input', 'dqs_strobe', 'differential_p', 'general_io'.
    """
    pin_clean = pin_name.strip().upper()
    dedicated_clocks = PG2L200H_FBB484_SPECS["dedicated_clock_pins"]

    if desired_function.lower() in ["clock", "clk", "clock_input", "gclk"]:
        if pin_clean in dedicated_clocks:
            info = dedicated_clocks[pin_clean]
            return {
                "is_legal": True,
                "pin": pin_clean,
                "role": "Dedicated Global Clock Input",
                "bank": info["bank"],
                "note": f"Optimal dedicated clock pin ({info['name']}). Zero clock rule violation risk."
            }
        else:
            return {
                "is_legal": False,
                "pin": pin_clean,
                "role": "Ordinary GPIO",
                "warning": "Assigning an incoming clock to this pin will trigger 'Clock Routing Rule Violation' in PDS!",
                "recommendation": f"Please select a dedicated GCLK pin: {list(dedicated_clocks.keys())[:4]}."
            }

    if desired_function.lower() in ["dqs", "dqs_strobe"]:
        for byte_grp, grp_info in PG2L200H_FBB484_SPECS["dedicated_dqs_groups"].items():
            if pin_clean in [grp_info["dqs_p"], grp_info["dqs_n"]]:
                return {
                    "is_legal": True,
                    "pin": pin_clean,
                    "role": f"Dedicated DQS Strobe ({byte_grp})",
                    "bank": grp_info["bank"],
                    "note": "Fully legal hardware DQS strobe pin."
                }
        return {
            "is_legal": False,
            "pin": pin_clean,
            "role": "Non-DQS pin",
            "warning": "DDR memory DQ capture requires dedicated DQS strobe hardware pins."
        }

    return {
        "is_legal": True,
        "pin": pin_clean,
        "role": "General Purpose User I/O",
        "note": "Pin is valid for general logic interfacing."
    }
