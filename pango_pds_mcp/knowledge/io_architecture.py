"""
PanGo Logos-2 FPGA Input/Output (I/O) Architecture Knowledge Base (UG040006).
Covers: IO Banks, VCCIO voltage compatibility, ILOGIC/OLOGIC packing, IODELAY, and Differential Pairs.
"""

from typing import Dict, List, Any

IO_BANK_RULES = {
    "vccio_consistency": {
        "rule": "Single VCCIO Rail Per Bank",
        "detail": "All pins allocated within the same physical IO Bank must share an identical VCCIO voltage (1.2V, 1.5V, 1.8V, 2.5V, or 3.3V).",
        "violation_symptom": "PDS Device Map DRC Error: Bank VCCIO conflict (e.g. LVCMOS33 and SSTL15 assigned to same Bank).",
        "resolution": "Relocate SSTL15 pins to the dedicated memory Bank (typically Bank 2/3 for DDR3), keeping Bank 0/1 for LVCMOS33."
    },
    "iob_register_packing": {
        "rule": "ILOGIC / OLOGIC Direct Packing",
        "benefit": "Drastically reduces clock-to-out (Tco) and input setup times by placing registers right at the pad, bypassing fabric routing delay.",
        "fdc_syntax": "define_attribute {p:<port_name>} {PAP_IOB_REG} {TRUE}",
        "verilog_syntax": "(* IOB = \"TRUE\" *) reg data_out_reg;",
        "common_packing_failures": [
            "Register output has fanout to internal logic fabric in addition to the pin.",
            "Asynchronous reset on the register is incompatible with IOB reset routing.",
            "Combinational logic exists between register and IO pad."
        ]
    },
    "iodelay_calibration": {
        "rule": "Fine-grained delay insertion",
        "resolution_steps": "Provides up to 64/128 taps of delay (~25ps to 50ps per tap) to center clock in data eye for high-speed parallel buses."
    },
    "differential_pairs": {
        "rule": "P/N Adjacent Pairing",
        "requirement": "True differential inputs (e.g. LVDS25) must use dedicated adjacent P/N pairs (IO_LxxP / IO_LxxN).",
        "on_chip_termination": "Enable 100-ohm internal differential termination: `define_attribute {p:<port_p>} {PAP_IO_DIFF_TERM} {TRUE}`."
    }
}

def validate_bank_voltage(pin_assignments: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Validates a list of pin assignments for Bank VCCIO conflicts.
    Expected dict format: {"port": "cam_data[0]", "bank": "Bank 1", "vccio": "3.3"}
    """
    bank_voltages: Dict[str, str] = {}
    conflicts = []

    for item in pin_assignments:
        bank = item.get("bank", "Unknown")
        vccio = item.get("vccio", "3.3")
        port = item.get("port", "unknown")

        if bank not in bank_voltages:
            bank_voltages[bank] = vccio
        else:
            if bank_voltages[bank] != vccio:
                conflicts.append({
                    "bank": bank,
                    "existing_vccio": bank_voltages[bank],
                    "conflicting_port": port,
                    "conflicting_vccio": vccio
                })

    is_valid = len(conflicts) == 0
    return {
        "is_valid": is_valid,
        "conflicts": conflicts,
        "bank_voltages": bank_voltages,
        "summary": "Bank VCCIO assignment clean." if is_valid else f"Detected {len(conflicts)} Bank voltage conflicts!"
    }
