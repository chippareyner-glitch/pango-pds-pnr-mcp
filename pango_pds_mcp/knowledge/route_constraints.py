"""
PanGo PDS Route Constraint Knowledge Base (Route_Constraint_Editor_User_Guide).
Contains syntax for dedicated routing resource locking, net routing control, and manual routing in Design Editor.
"""

from typing import Dict, List, Any

ROUTE_SYNTAX_RULES = {
    "promote_net_to_global_clock": {
        "syntax": "define_attribute {n:<net_name>} {PAP_NET_ROUTE_TYPE} {GLOBAL_CLOCK}",
        "example": "define_attribute {n:clk_pixel_buf} {PAP_NET_ROUTE_TYPE} {GLOBAL_CLOCK}",
        "description": "Forces a high-fanout clock or reset net onto low-skew Global Clock (GCLK) tree spines."
    },
    "promote_net_to_regional_clock": {
        "syntax": "define_attribute {n:<net_name>} {PAP_NET_ROUTE_TYPE} {REGIONAL_CLOCK}",
        "example": "define_attribute {n:u_cam_rx/byte_clk} {PAP_NET_ROUTE_TYPE} {REGIONAL_CLOCK}",
        "description": "Routes a clock net onto Regional Clock (RCLK) network spanning 1-2 adjacent Clock Regions."
    },
    "lock_fixed_route": {
        "syntax": "define_attribute {n:<net_name>} {PAP_NET_LOCK_ROUTE} {TRUE}",
        "example": "define_attribute {n:crit_sync_bus[*]} {PAP_NET_LOCK_ROUTE} {TRUE}",
        "description": "Freezes existing routing tracks for a timing-sensitive net across iterative P&R runs."
    },
    "set_net_max_delay": {
        "syntax": "set_max_delay <delay_ns> -from [get_pins <pin1>] -to [get_pins <pin2>] -datapath_only",
        "example": "set_max_delay 2.500 -from [get_pins u_fsm/cur_state_reg[*]/CLK] -to [get_pins u_fsm/next_state_reg[*]/D] -datapath_only",
        "description": "Applies a strict upper limit on datapath interconnect delay to prevent router detours."
    }
}

DESIGN_EDITOR_MANUAL_ROUTING = {
    "workflow": [
        "1. Open PDS Floorplan & Routing GUI via Design Editor (`dev_pnr -gui` or Tools -> Design Editor).",
        "2. Locate unrouted nets from .prr report under 'Unrouted Net Browser'.",
        "3. Highlight congested switchboxes (colored red/orange indicating capacity exceeded).",
        "4. Use 'Manual Route Mode' (Wire Tool) to pick adjacent unused PIPs (Programmable Interconnect Points).",
        "5. Right-click the modified net and select 'Fix/Lock Route' to emit PAP_NET_LOCK_ROUTE attribute."
    ],
    "high_fanout_remedies": [
        "For reset nets with fanout > 1000 causing routing congestion: Insert MAX_FANOUT attribute in RTL: `(* MAX_FANOUT = 100 *) wire rst_n_tree;`.",
        "Promote high-fanout global enable signals to GCLK spines using PAP_NET_ROUTE_TYPE = GLOBAL_CLOCK."
    ]
}
