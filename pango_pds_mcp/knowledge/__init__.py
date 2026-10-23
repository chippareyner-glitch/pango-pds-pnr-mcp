"""
Knowledge modules package for PanGo PDS MCP server.
"""

from .pnr_optimization import PNR_STRATEGIES, PDS_SHELL_TCL_TEMPLATES, diagnose_mrp_report, diagnose_prr_report
from .physical_constraints import PHYSICAL_SYNTAX_RULES, PBLOCK_SYNTAX_GUIDE, RPM_GUIDE, generate_pblock_fdc
from .route_constraints import ROUTE_SYNTAX_RULES, DESIGN_EDITOR_MANUAL_ROUTING
from .fdc_syntax import FDC_TIMING_SYNTAX, FDC_PHYSICAL_ATTRIBUTES, lint_and_diagnose_fdc, convert_xdc_to_pango_fdc
from .clock_architecture import LOGOS2_CLOCK_TOPOLOGY, CLOCK_ROUTING_VIOLATIONS, diagnose_clock_routing
from .io_architecture import IO_BANK_RULES, validate_bank_voltage
from .pinout_pg2l200h import PG2L200H_FBB484_SPECS, check_pin_legality
from .high_speed_interfaces import DDR3_HMIC_PNR_RULES, GTP_HSSTLP_PNR_RULES, get_high_speed_pnr_template

__all__ = [
    "PNR_STRATEGIES",
    "PDS_SHELL_TCL_TEMPLATES",
    "diagnose_mrp_report",
    "diagnose_prr_report",
    "PHYSICAL_SYNTAX_RULES",
    "PBLOCK_SYNTAX_GUIDE",
    "RPM_GUIDE",
    "generate_pblock_fdc",
    "ROUTE_SYNTAX_RULES",
    "DESIGN_EDITOR_MANUAL_ROUTING",
    "FDC_TIMING_SYNTAX",
    "FDC_PHYSICAL_ATTRIBUTES",
    "lint_and_diagnose_fdc",
    "convert_xdc_to_pango_fdc",
    "LOGOS2_CLOCK_TOPOLOGY",
    "CLOCK_ROUTING_VIOLATIONS",
    "diagnose_clock_routing",
    "IO_BANK_RULES",
    "validate_bank_voltage",
    "PG2L200H_FBB484_SPECS",
    "check_pin_legality",
    "DDR3_HMIC_PNR_RULES",
    "GTP_HSSTLP_PNR_RULES",
    "get_high_speed_pnr_template"
]
