"""
PanGo PDS User Constraint (.fdc) Syntax Engine and XDC-to-FDC Linter/Translator.
Addresses: User_Constraint_Editor_User_Guide, preventing Vivado XDC syntax pollution.
"""

import re
from typing import Dict, List, Any, Tuple

FDC_TIMING_SYNTAX = {
    "create_clock": {
        "syntax": "create_clock -name <clk_name> -period <period_ns> [get_ports {<port_name>}]",
        "example": "create_clock -name clk_50m -period 20.000 [get_ports {clk_50m}]",
        "note": "Standard SDC command supported directly in PDS .fdc."
    },
    "create_generated_clock": {
        "syntax": "create_generated_clock -name <gen_clk_name> -source [get_pins {<src_pin>}] -divide_by <div_factor> [get_pins {<out_pin>}]",
        "example": "create_generated_clock -name clk_25m -source [get_pins {u_pll/clk_in}] -divide_by 2 [get_pins {u_pll/clkout0}]",
        "note": "Used for clock dividers or PLL outputs."
    },
    "set_clock_groups": {
        "syntax": "set_clock_groups -asynchronous -group [get_clocks {<clk_group1>}] -group [get_clocks {<clk_group2>}]",
        "example": "set_clock_groups -asynchronous -group [get_clocks {clk_sys}] -group [get_clocks {clk_pixel}]",
        "note": "Crucial to decouple asynchronous clock domains and prevent false hold time violations."
    },
    "set_clock_uncertainty": {
        "syntax": "set_clock_uncertainty -setup <val_ns> [get_clocks {<clk_name>}]",
        "example": "set_clock_uncertainty -setup 0.200 [get_clocks {clk_pixel}]",
        "note": "Models clock jitter and duty cycle distortion."
    },
    "set_false_path": {
        "syntax": "set_false_path -from [get_pins {<from_pin>}] -to [get_pins {<to_pin>}]",
        "example": "set_false_path -from [get_pins {u_rst/rst_n_meta_reg/CLK}] -to [get_pins {u_rst/rst_n_sync_reg/D}]",
        "note": "Excludes static resets and CDC synchronizer stages from timing analysis."
    }
}

FDC_PHYSICAL_ATTRIBUTES = {
    "PAP_IO_LOC": "define_attribute {p:<port>} {PAP_IO_LOC} {<PIN_BALL>}",
    "PAP_IO_VCCIO": "define_attribute {p:<port>} {PAP_IO_VCCIO} {1.5|1.8|2.5|3.3}",
    "PAP_IO_STANDARD": "define_attribute {p:<port>} {PAP_IO_STANDARD} {LVCMOS33|LVCMOS18|SSTL15|LVDS25}",
    "PAP_IO_DRIVE": "define_attribute {p:<port>} {PAP_IO_DRIVE} {4|8|12|16}",
    "PAP_IO_PULLUP": "define_attribute {p:<port>} {PAP_IO_PULLUP} {TRUE|FALSE}",
    "PAP_IO_SLEW": "define_attribute {p:<port>} {PAP_IO_SLEW} {FAST|SLOW}",
    "PAP_IO_DIFF_PAIR": "define_attribute {p:<port>} {PAP_IO_DIFF_PAIR} {TRUE|FALSE}"
}

def lint_and_diagnose_fdc(content: str) -> Dict[str, Any]:
    """
    Checks if a constraint file accidentally contains Vivado XDC syntax,
    or invalid PanGo FDC syntax.
    """
    issues = []
    corrections = []
    lines = content.splitlines()

    xdc_patterns = [
        (r"set_property\s+PACKAGE_PIN\s+(\w+)\s+\[get_ports\s+(\w+)\]",
         "Detected Vivado XDC `set_property PACKAGE_PIN`. In PanGo FDC use: `define_attribute {p:\\2} {PAP_IO_LOC} {\\1}`"),
        (r"set_property\s+IOSTANDARD\s+(\w+)\s+\[get_ports\s+(\w+)\]",
         "Detected Vivado XDC `set_property IOSTANDARD`. In PanGo FDC use: `define_attribute {p:\\2} {PAP_IO_STANDARD} {\\1}`"),
        (r"set_property\s+PULLUP\s+true\s+\[get_ports\s+(\w+)\]",
         "Detected Vivado XDC `set_property PULLUP`. In PanGo FDC use: `define_attribute {p:\\1} {PAP_IO_PULLUP} {TRUE}`"),
        (r"set_property\s+DRIVE\s+(\d+)\s+\[get_ports\s+(\w+)\]",
         "Detected Vivado XDC `set_property DRIVE`. In PanGo FDC use: `define_attribute {p:\\2} {PAP_IO_DRIVE} {\\1}`")
    ]

    for line_idx, line in enumerate(lines, 1):
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue

        for pat, err_msg in xdc_patterns:
            m = re.search(pat, line_strip, re.IGNORECASE)
            if m:
                issues.append({
                    "line_number": line_idx,
                    "original_line": line_strip,
                    "problem": "Vivado XDC syntax error in PanGo FDC file",
                    "suggestion": re.sub(r"\\(\d)", lambda sm: m.group(int(sm.group(1))), err_msg)
                })

    is_valid = len(issues) == 0
    return {
        "is_valid_pango_fdc": is_valid,
        "total_issues": len(issues),
        "issues": issues,
        "summary": "FDC constraint syntax check passed." if is_valid else f"Found {len(issues)} syntax violations (likely Vivado XDC leftovers)."
    }

def convert_xdc_to_pango_fdc(xdc_text: str) -> str:
    """Converts a standard Vivado XDC text block into PanGo PDS .fdc syntax."""
    out_lines = []
    lines = xdc_text.splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            out_lines.append("")
            continue
        if line_clean.startswith("#"):
            out_lines.append(line_clean)
            continue

        # Package pin
        m_pin = re.search(r"set_property\s+PACKAGE_PIN\s+(\w+)\s+\[get_ports\s+([\{\}\w\d_\[\]]+)\]", line_clean, re.I)
        if m_pin:
            pin = m_pin.group(1)
            port = m_pin.group(2).strip("{}")
            out_lines.append(f"define_attribute {{p:{port}}} {{PAP_IO_LOC}} {{{pin}}}")
            continue

        # IOSTANDARD
        m_io = re.search(r"set_property\s+IOSTANDARD\s+(\w+)\s+\[get_ports\s+([\{\}\w\d_\[\]]+)\]", line_clean, re.I)
        if m_io:
            iostd = m_io.group(1)
            port = m_io.group(2).strip("{}")
            vccio = "3.3"
            if "18" in iostd: vccio = "1.8"
            elif "25" in iostd: vccio = "2.5"
            elif "15" in iostd: vccio = "1.5"
            elif "12" in iostd: vccio = "1.2"
            out_lines.append(f"define_attribute {{p:{port}}} {{PAP_IO_STANDARD}} {{{iostd}}}")
            out_lines.append(f"define_attribute {{p:{port}}} {{PAP_IO_VCCIO}} {{{vccio}}}")
            continue

        # PULLUP
        m_pull = re.search(r"set_property\s+PULLUP\s+true\s+\[get_ports\s+([\{\}\w\d_\[\]]+)\]", line_clean, re.I)
        if m_pull:
            port = m_pull.group(1).strip("{}")
            out_lines.append(f"define_attribute {{p:{port}}} {{PAP_IO_PULLUP}} {{TRUE}}")
            continue

        # DRIVE
        m_drv = re.search(r"set_property\s+DRIVE\s+(\d+)\s+\[get_ports\s+([\{\}\w\d_\[\]]+)\]", line_clean, re.I)
        if m_drv:
            drv = m_drv.group(1)
            port = m_drv.group(2).strip("{}")
            out_lines.append(f"define_attribute {{p:{port}}} {{PAP_IO_DRIVE}} {{{drv}}}")
            continue

        # SDC Timing commands (pass-through with clean port brackets)
        if line_clean.startswith("create_clock") or line_clean.startswith("set_clock_groups") or line_clean.startswith("set_false_path"):
            out_lines.append(line_clean)
            continue

        # Fallback
        out_lines.append(f"# [REVIEW NEEDED] {line_clean}")

    return "\n".join(out_lines)
