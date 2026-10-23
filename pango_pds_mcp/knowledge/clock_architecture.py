"""
PanGo Logos-2 FPGA Clock Architecture and Routing Rules Knowledge Base (UG040004).
Covers: GCLK, RCLK, IOCLK, Clock Regions, 10 GPLL + 10 PPLL rules, and Clock Routing Rule Violations.
"""

from typing import Dict, List, Any

LOGOS2_CLOCK_TOPOLOGY = {
    "device_family": "PanGo Logos-2 (PG2L200H)",
    "clock_networks": {
        "GCLK": {
            "name": "Global Clock Network",
            "capacity": "32 GCLK spines",
            "reach": "Entire die (all Slices, DRMs, APMs, IOBs)",
            "driver_sources": ["Dedicated GCLK pins", "GPLL outputs", "Internal logic fabric via CLK_DIV"],
            "characteristics": "Lowest skew, highest fanout, primary choice for synchronous system clocks."
        },
        "RCLK": {
            "name": "Regional Clock Network",
            "capacity": "8 RCLK per Clock Region",
            "reach": "1-2 adjacent Clock Regions along horizontal spine",
            "driver_sources": ["Dedicated RCLK pins", "PPLL outputs"],
            "characteristics": "Low latency, ideal for localized interface controllers (e.g. camera sensor DVP, SPI, I2S)."
        },
        "IOCLK": {
            "name": "I/O High Speed Clock Network",
            "capacity": "Dedicated high-speed tracks per IO Bank",
            "reach": "ILOGIC / OLOGIC primitives within the Bank",
            "driver_sources": ["PPLL high-speed outputs", "DQS strobe buffers"],
            "characteristics": "Speeds up to 800+ MHz, matched trace length to IODELAY and SERDES."
        }
    },
    "pll_resources": {
        "total_gpll": 10,
        "total_ppll": 10,
        "gpll_features": "Wide frequency synthesis range, dynamic phase shift (DPS), feedback compensation.",
        "ppll_features": "Tightly coupled to IO Banks, ultra-low jitter, optimized for DDR3/LPDDR and high-speed SERDES."
    }
}

CLOCK_ROUTING_VIOLATIONS = {
    "RULE_CLK_001": {
        "error_pattern": "Clock Routing Rule Violation: Non-clock pin connected directly to GCLK or GPLL input.",
        "root_cause": "The input clock signal is assigned to an ordinary GPIO ball instead of a dedicated GCLK_IN / PLL_IN pin.",
        "hardware_impact": "Causes severe clock jitter, non-deterministic routing skew, and potential setup/hold failures.",
        "solutions": [
            "Preferred: Reassign clock port to a dedicated GCLK pin in .fdc (e.g. check PK04009 pinout table for GCLK tag).",
            "Workaround (if PCB is already frozen): Add relaxation constraint in .fdc: `define_attribute {n:<clk_net_name>} {PAP_CLOCK_DEDICATED_ROUTE} {FALSE}`.",
            "Workaround 2: Route through an internal fabric LUT buffer to break dedicated routing rule (adds ~1.5ns insertion delay)."
        ]
    },
    "RULE_CLK_002": {
        "error_pattern": "Cross-Clock-Region Violation: RCLK attempted to drive primitives across >2 Clock Regions.",
        "root_cause": "Regional clock load spans across non-adjacent clock regions.",
        "solutions": [
            "Promote the clock from RCLK to GCLK: `define_attribute {n:<clk_net>} {PAP_NET_ROUTE_TYPE} {GLOBAL_CLOCK}`.",
            "Apply Pblock constraint to cluster all module logic into the specific Clock Region."
        ]
    }
}

def diagnose_clock_routing(error_message: str) -> Dict[str, Any]:
    """Provides actionable remedies for clock-related P&R failures."""
    for rule_id, rule_info in CLOCK_ROUTING_VIOLATIONS.items():
        if "Non-clock pin" in error_message or "dedicated" in error_message.lower():
            return {
                "rule_id": "RULE_CLK_001",
                "diagnosis": rule_info["root_cause"],
                "hardware_impact": rule_info["hardware_impact"],
                "remedies": rule_info["solutions"]
            }
        if "Region" in error_message or "RCLK" in error_message:
            return {
                "rule_id": "RULE_CLK_002",
                "diagnosis": rule_info["root_cause"],
                "remedies": rule_info["solutions"]
            }
    return {
        "diagnosis": "Generic clock routing issue. Ensure all clock nets pass through GCLK spines.",
        "remedies": [
            "Inspect GCLK utilization in .mrp report (must be <= 32).",
            "Ensure PLL reference clocks enter via dedicated GCLK/PPLL input pin pairs."
        ]
    }
