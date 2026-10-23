"""
PanGo PDS Physical Constraint Knowledge Base (Physical_Constraint_Editor_User_Guide).
Contains exact syntax for LOC, Pblock/Region, RPM, and Floorplanning for PG2L200H.
"""

from typing import Dict, List, Any

PHYSICAL_SYNTAX_RULES = {
    "io_location_pin": {
        "syntax": "define_attribute {p:<port_name>} {PAP_IO_LOC} {<PIN_NAME>}",
        "example": "define_attribute {p:cam_data[0]} {PAP_IO_LOC} {U14}",
        "description": "Binds a top-level primary IO port to a specific physical package ball/pin."
    },
    "primitive_loc_drm": {
        "syntax": "define_attribute {i:<instance_path>} {PAP_LOC} {DRM_X<x>Y<y>}",
        "example": "define_attribute {i:u_xor_diff/mem_reg} {PAP_LOC} {DRM_X2Y15}",
        "description": "Locks an inferred or instantiated DRM 18K/36K Block RAM to a fixed physical column/row."
    },
    "primitive_loc_apm": {
        "syntax": "define_attribute {i:<instance_path>} {PAP_LOC} {APM_X<x>Y<y>}",
        "example": "define_attribute {i:u_pe/mult_core} {PAP_LOC} {APM_X1Y10}",
        "description": "Locks an APM DSP48 multiplier unit to a dedicated column location."
    },
    "primitive_loc_slice": {
        "syntax": "define_attribute {i:<instance_path>} {PAP_LOC} {SLICE_X<x>Y<y>}",
        "example": "define_attribute {i:u_fsm/state_reg[0]} {PAP_LOC} {SLICE_X30Y50}",
        "description": "Locks a critical logic slice / flip-flop to avoid layout jitter."
    },
    "primitive_loc_pll": {
        "syntax": "define_attribute {i:<instance_path>} {PAP_LOC} {GPLL_X<x>Y<y>}",
        "example": "define_attribute {i:u_pll/gpll_inst} {PAP_LOC} {GPLL_X0Y1}",
        "description": "Locks a GPLL/PPLL instance adjacent to dedicated clock input pins."
    }
}

PBLOCK_SYNTAX_GUIDE = {
    "concept": "Pblock (Physical Block) defines a bounding box on the die to constrain module placement.",
    "fdc_commands": [
        "# 1. Create a physical region",
        "create_pblock pblock_npu_core",
        "# 2. Assign primitive ranges to the pblock",
        "add_pblock_range -pblock pblock_npu_core {SLICE_X20Y20:SLICE_X45Y60}",
        "add_pblock_range -pblock pblock_npu_core {DRM_X1Y5:DRM_X2Y15}",
        "# 3. Assign hierarchical RTL instance to the pblock",
        "add_pblock_instance -pblock pblock_npu_core {u_lenet5_top}"
    ],
    "best_practices": [
        "Leave at least 20% slice overhead inside the Pblock to allow routing flexibility.",
        "Ensure the Pblock boundary encompasses the necessary dedicated columns (DRM or APM) if the module instantiates BRAM or DSP.",
        "Keep Pblocks containing IO-bound logic close to the corresponding IO Banks to avoid long snake routes."
    ]
}

RPM_GUIDE = {
    "concept": "Relative Placement Macro (RPM) locks relative offsets (RLOC) among datapath registers and ALUs.",
    "syntax_example": [
        "// In Verilog source code or .fdc:",
        "(* RLOC = \"X0Y0\" *) reg [7:0] stage1_reg;",
        "(* RLOC = \"X0Y1\" *) reg [7:0] stage2_reg;"
    ],
    "benefit": "Guarantees identical ultra-low delay between pipeline registers regardless of overall chip layout."
}

def generate_pblock_fdc(pblock_name: str, instance_path: str, slice_range: str, drm_range: str = None) -> str:
    """Generates standard Pblock FDC constraint snippet."""
    lines = [
        f"# Pblock constraint for module {instance_path}",
        f"create_pblock {pblock_name}",
        f"add_pblock_range -pblock {pblock_name} {{{slice_range}}}"
    ]
    if drm_range:
        lines.append(f"add_pblock_range -pblock {pblock_name} {{{drm_range}}}")
    lines.append(f"add_pblock_instance -pblock {pblock_name} {{{instance_path}}}")
    return "\n".join(lines)
