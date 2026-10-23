"""
PanGo PDS Place & Route (P&R) Expert MCP Server.
Implements Model Context Protocol (MCP) tools, resources, and prompts for PanGo PDS and Logos-2 FPGA.
Supports both MCP 2.x (MCPServer) and 1.x (FastMCP).
"""

import json
from typing import Dict, Any, Optional

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        raise RuntimeError("mcp package is required. Install via `pip install mcp`.")

from .knowledge.pnr_optimization import (
    PNR_STRATEGIES,
    PDS_SHELL_TCL_TEMPLATES,
    diagnose_mrp_report,
    diagnose_prr_report
)
from .knowledge.physical_constraints import (
    PHYSICAL_SYNTAX_RULES,
    PBLOCK_SYNTAX_GUIDE,
    RPM_GUIDE,
    generate_pblock_fdc
)
from .knowledge.route_constraints import (
    ROUTE_SYNTAX_RULES,
    DESIGN_EDITOR_MANUAL_ROUTING
)
from .knowledge.fdc_syntax import (
    FDC_TIMING_SYNTAX,
    FDC_PHYSICAL_ATTRIBUTES,
    lint_and_diagnose_fdc,
    convert_xdc_to_pango_fdc
)
from .knowledge.clock_architecture import (
    LOGOS2_CLOCK_TOPOLOGY,
    CLOCK_ROUTING_VIOLATIONS,
    diagnose_clock_routing
)
from .knowledge.io_architecture import (
    IO_BANK_RULES,
    validate_bank_voltage
)
from .knowledge.pinout_pg2l200h import (
    PG2L200H_FBB484_SPECS,
    check_pin_legality
)
from .knowledge.high_speed_interfaces import (
    DDR3_HMIC_PNR_RULES,
    GTP_HSSTLP_PNR_RULES,
    get_high_speed_pnr_template
)

# Initialize MCP Server
app = MCPServer("pango-pds-pnr-expert")

# ==============================================================================
# MCP Tools
# ==============================================================================

@app.tool()
def pds_pnr_strategy(goal: str) -> str:
    """
    Query PDS Place & Route (P&R) optimization strategies and parameters.
    Args:
        goal: Strategy target: 'timing_driven_closure', 'congestion_reduction', or 'zero_dsp_bnn_flow'.
    """
    key = goal.lower().strip()
    if key in PNR_STRATEGIES:
        return json.dumps(PNR_STRATEGIES[key], ensure_ascii=False, indent=2)
    return json.dumps({
        "error": f"Unknown strategy '{goal}'.",
        "available_strategies": list(PNR_STRATEGIES.keys())
    }, ensure_ascii=False, indent=2)

@app.tool()
def pds_tcl_flow(flow_type: str = "complete_batch_flow") -> str:
    """
    Returns production-grade pds_shell automated Tcl scripts.
    Args:
        flow_type: 'complete_batch_flow' (end-to-end PDS build) or 'multi_seed_timing_closure' (seed exploration).
    """
    key = flow_type.lower().strip()
    if key in PDS_SHELL_TCL_TEMPLATES:
        return PDS_SHELL_TCL_TEMPLATES[key]
    return f"# Error: Unknown flow '{flow_type}'. Available: {list(PDS_SHELL_TCL_TEMPLATES.keys())}"

@app.tool()
def fdc_linter(fdc_content: str) -> str:
    """
    Lints a PanGo .fdc constraint string, catching Vivado XDC syntax errors (PACKAGE_PIN, IOSTANDARD, set_property).
    Args:
        fdc_content: Constraint text to validate.
    """
    result = lint_and_diagnose_fdc(fdc_content)
    return json.dumps(result, ensure_ascii=False, indent=2)

@app.tool()
def xdc_to_fdc_converter(xdc_content: str) -> str:
    """
    Converts Vivado XDC constraint text into standard PanGo PDS .fdc syntax.
    Args:
        xdc_content: Vivado XDC text block.
    """
    return convert_xdc_to_pango_fdc(xdc_content)

@app.tool()
def physical_floorplan_query(query_type: str = "loc_rules") -> str:
    """
    Returns PanGo PDS physical floorplanning syntax, Pblock regions, and RPM guides.
    Args:
        query_type: 'loc_rules', 'pblock_guide', or 'rpm_guide'.
    """
    qt = query_type.lower().strip()
    if qt in ["loc", "loc_rules"]:
        return json.dumps(PHYSICAL_SYNTAX_RULES, ensure_ascii=False, indent=2)
    elif qt in ["pblock", "pblock_guide"]:
        return json.dumps(PBLOCK_SYNTAX_GUIDE, ensure_ascii=False, indent=2)
    elif qt in ["rpm", "rpm_guide"]:
        return json.dumps(RPM_GUIDE, ensure_ascii=False, indent=2)
    return json.dumps({"available_queries": ["loc_rules", "pblock_guide", "rpm_guide"]}, indent=2)

@app.tool()
def route_constraint_query(feature: str = "all") -> str:
    """
    Returns PanGo dedicated routing attributes (GLOBAL_CLOCK, LOCK_ROUTE, MAX_DELAY) and Design Editor manual routing steps.
    """
    return json.dumps({
        "route_syntax_rules": ROUTE_SYNTAX_RULES,
        "design_editor_manual_routing": DESIGN_EDITOR_MANUAL_ROUTING
    }, ensure_ascii=False, indent=2)

@app.tool()
def clock_rules_diagnose(error_message: str) -> str:
    """
    Diagnoses Clock Routing Rule Violations in PDS and provides hardware-compliant remedies.
    Args:
        error_message: Error log text from PDS (e.g. 'Non-clock pin connected directly to GCLK').
    """
    res = diagnose_clock_routing(error_message)
    return json.dumps(res, ensure_ascii=False, indent=2)

@app.tool()
def pin_legality_checker(pin: str, desired_function: str = "clock_input") -> str:
    """
    Checks if a pin on PG2L200H-FBB484 is legal for dedicated roles (clock_input, dqs_strobe, general_io).
    Args:
        pin: Package ball name (e.g. 'Y12', 'B10', 'M2', 'U14').
        desired_function: 'clock_input', 'dqs_strobe', or 'general_io'.
    """
    res = check_pin_legality(pin, desired_function)
    return json.dumps(res, ensure_ascii=False, indent=2)

@app.tool()
def high_speed_pnr_query(interface: str = "ddr3") -> str:
    """
    Returns placement & routing rules and FDC syntax for onboard DDR3 (HMIC) or GTP (HSSTLP) on Pangu 200Pro.
    Args:
        interface: 'ddr3' or 'gtp' (PCIe / SFP+).
    """
    template = get_high_speed_pnr_template(interface)
    rules = DDR3_HMIC_PNR_RULES if interface.lower() == "ddr3" else GTP_HSSTLP_PNR_RULES
    return json.dumps({
        "interface": interface,
        "rules": rules,
        "fdc_template": template
    }, ensure_ascii=False, indent=2)

@app.tool()
def report_diagnoser(report_text: str, report_type: str = "auto") -> str:
    """
    Diagnoses PanGo PDS Device Map (.mrp) or Place & Route (.prr) reports.
    Identifies WNS/WHS violations, unrouted nets, resource exhaustion, and IOB packing issues.
    """
    is_mrp = "mrp" in report_type.lower() or "Device Map" in report_text or "MAP REPORT" in report_text
    is_prr = "prr" in report_type.lower() or "Place & Route" in report_text or "WNS" in report_text

    if is_mrp:
        return json.dumps(diagnose_mrp_report(report_text), ensure_ascii=False, indent=2)
    elif is_prr:
        return json.dumps(diagnose_prr_report(report_text), ensure_ascii=False, indent=2)
    else:
        # Run both
        mrp_res = diagnose_mrp_report(report_text)
        prr_res = diagnose_prr_report(report_text)
        return json.dumps({"mrp_diagnosis": mrp_res, "prr_diagnosis": prr_res}, ensure_ascii=False, indent=2)

# ==============================================================================
# MCP Resources
# ==============================================================================

@app.resource("pds://guides/pnr-optimization")
def resource_pnr_guide() -> str:
    """PDS Place & Route timing and congestion optimization guide."""
    return json.dumps(PNR_STRATEGIES, ensure_ascii=False, indent=2)

@app.resource("pds://guides/fdc-syntax-reference")
def resource_fdc_guide() -> str:
    """PanGo FDC timing and physical attribute syntax reference."""
    return json.dumps({
        "timing_syntax": FDC_TIMING_SYNTAX,
        "physical_attributes": FDC_PHYSICAL_ATTRIBUTES
    }, ensure_ascii=False, indent=2)

@app.resource("pds://guides/logos2-clock-architecture")
def resource_clock_architecture() -> str:
    """Logos-2 clocking network, GPLL/PPLL, and clock routing rules."""
    return json.dumps(LOGOS2_CLOCK_TOPOLOGY, ensure_ascii=False, indent=2)

@app.resource("pds://guides/pg2l200h-pinout-table")
def resource_pinout_table() -> str:
    """PG2L200H-FBB484 dedicated pinout table and rules."""
    return json.dumps(PG2L200H_FBB484_SPECS, ensure_ascii=False, indent=2)

# ==============================================================================
# Entry Point
# ==============================================================================

def main():
    """Runs the MCP server over standard I/O."""
    app.run()

if __name__ == "__main__":
    main()
