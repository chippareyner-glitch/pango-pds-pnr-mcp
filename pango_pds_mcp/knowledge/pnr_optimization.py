"""
PanGo PDS Place & Route (P&R) and Device Map Optimization Knowledge Base.
Contains detailed parameters, strategies, pds_shell Tcl automation, and report diagnostics.
"""

from typing import Dict, List, Any

PNR_STRATEGIES = {
    "timing_driven_closure": {
        "description": "Aggressive timing closure flow for high-frequency designs (>150MHz) on Logos-2 PG2L200H.",
        "dev_map_flags": [
            "-effort timing",
            "-optimize_drm true",
            "-optimize_apm true",
            "-register_duplication true"
        ],
        "dev_pnr_flags": [
            "-opt_effort high",
            "-timing_effort timing_driven",
            "-congestion_effort medium",
            "-wire_delay_model realistic",
            "-multi_pass 3"
        ],
        "recommendations": [
            "Enable physical synthesis register duplication for high-fanout timing paths.",
            "Set clock uncertainty (set_clock_uncertainty) in .fdc to preserve at least 150ps jitter margin.",
            "Use pds_shell multi-seed exploration if WNS is within -300ps."
        ]
    },
    "congestion_reduction": {
        "description": "Alleviate local routing congestion (hotspots) in high LUT utilization (>80%) designs.",
        "dev_map_flags": [
            "-effort standard",
            "-control_set_merge true",
            "-lut_combining false"
        ],
        "dev_pnr_flags": [
            "-opt_effort high",
            "-timing_effort standard",
            "-congestion_effort high",
            "-hotspot_removal on",
            "-spread_logic true"
        ],
        "recommendations": [
            "Disable aggressive LUT combining in dev_map to avoid dense pin routing around Slices.",
            "Partition large datapath modules into separate Pblocks to enforce spatial spread across chip.",
            "Identify routing congestion level >= 4 in .prr report and pipeline wide muxes / crossbars."
        ]
    },
    "zero_dsp_bnn_flow": {
        "description": "Targeted flow for pure-logic AI accelerators (e.g. BNN / shift-add pipelines) consuming 0 APMs.",
        "dev_map_flags": [
            "-effort high",
            "-infer_carry_chain true",
            "-drm_absorb_registers true"
        ],
        "dev_pnr_flags": [
            "-opt_effort high",
            "-timing_effort timing_driven",
            "-congestion_effort high"
        ],
        "recommendations": [
            "Popcount adder trees generate long vertical carry chains; place adder trees along Slice columns.",
            "Ensure pipeline registers are absorbed directly into DRM / BRAM output latches (DO_REG=1)."
        ]
    }
}

PDS_SHELL_TCL_TEMPLATES = {
    "complete_batch_flow": """# ==============================================================================
# PanGo PDS Automated Batch Tcl Flow (pds_shell)
# Target: PanGo Logos-2 PG2L200H-FBB484
# ==============================================================================

set PROJECT_NAME "pangu_top"
set DEVICE_NAME  "PG2L200H-6FBB484"

# 1. Project Creation & Setup
if {[file exists ${PROJECT_NAME}.pds]} {
    open_project -project ${PROJECT_NAME}.pds
} else {
    create_project -name ${PROJECT_NAME} -device ${DEVICE_NAME} -dir ./build
    add_file -format verilog [glob ./rtl/*.v]
    add_file -format fdc ./constraints/timing_and_pinout.fdc
    set_top_module pangu_gesture_top
}

# 2. Elaboration & Synthesis
compile -top pangu_gesture_top
synthesize -effort high

# 3. Device Mapping (dev_map)
dev_map -effort timing -optimize_drm true -optimize_apm true

# 4. Place and Route (dev_pnr)
dev_pnr -opt_effort high -timing_effort timing_driven -congestion_effort medium

# 5. Timing & Congestion Reports
report_timing -setup -npaths 20 -file ./reports/timing_setup_wns.rpt
report_timing -hold  -npaths 20 -file ./reports/timing_hold_whs.rpt
report_congestion -file ./reports/routing_congestion.rpt

# 6. Bitstream Generation
gen_bitstream -file ./output/${PROJECT_NAME}.sbit

puts "=== PDS Batch Flow Successfully Finished ==="
exit
""",
    "multi_seed_timing_closure": """# ==============================================================================
# PanGo PDS Multi-Seed DSE (Design Space Exploration) Tcl Script
# ==============================================================================
set SEED_LIST [list 1 7 13 42 100]
set BEST_WNS -9999.0
set BEST_SEED 1

foreach seed $SEED_LIST {
    puts "--> Testing PDS P&R with Seed: $seed"
    dev_pnr -opt_effort high -timing_effort timing_driven -seed $seed
    set timing_val [get_timing_metric -wns]
    puts "    Seed $seed Result WNS = $timing_val ns"
    if {$timing_val > $BEST_WNS} {
        set BEST_WNS $timing_val
        set BEST_SEED $seed
    }
    if {$BEST_WNS >= 0.0} {
        puts "--> Timing Closure Achieved with Seed: $seed! Stopping search."
        break
    }
}
puts "--> Best P&R Seed is: $BEST_SEED with WNS: $BEST_WNS ns"
"""
}

def diagnose_mrp_report(mrp_text: str) -> Dict[str, Any]:
    """Analyzes PanGo PDS Device Map (.mrp) report text."""
    findings = []
    actions = []
    lines = mrp_text.splitlines()
    
    lut_pct = None
    drm_pct = None
    apm_pct = None
    iob_unpacked = 0

    for line in lines:
        line_clean = line.strip()
        if "LUT5" in line_clean and "%" in line_clean:
            findings.append(f"Resource finding: {line_clean}")
        if "DRM" in line_clean and "%" in line_clean:
            findings.append(f"Memory finding: {line_clean}")
        if "APM" in line_clean and "%" in line_clean:
            findings.append(f"DSP finding: {line_clean}")
        if "not packed into IOB" in line_clean:
            iob_unpacked += 1

    if iob_unpacked > 0:
        findings.append(f"Found {iob_unpacked} registers failing to pack into IOB.")
        actions.append("Check input/output timing constraints and add `define_attribute {p:pin} {PAP_IOB_REG} {TRUE}` in .fdc.")

    return {
        "report_type": "Device Map (.mrp)",
        "findings": findings,
        "recommended_actions": actions,
        "summary": "MRP report parsed. Check high resource utilization and IOB packing rules."
    }

def diagnose_prr_report(prr_text: str) -> Dict[str, Any]:
    """Analyzes PanGo PDS Place & Route (.prr) report text."""
    findings = []
    actions = []
    lines = prr_text.splitlines()

    has_wns_violation = False
    has_whs_violation = False
    unrouted_count = 0

    for line in lines:
        line_clean = line.strip()
        if "WNS" in line_clean or "Worst Negative Slack" in line_clean:
            findings.append(f"Timing Setup: {line_clean}")
            if "-" in line_clean:
                has_wns_violation = True
        if "WHS" in line_clean or "Worst Hold Slack" in line_clean:
            findings.append(f"Timing Hold: {line_clean}")
            if "-" in line_clean:
                has_whs_violation = True
        if "Unrouted" in line_clean:
            findings.append(f"Routing: {line_clean}")
            unrouted_count += 1

    if has_wns_violation:
        actions.append("Setup timing violated (WNS < 0). Re-run dev_pnr with `-opt_effort high -timing_effort timing_driven`.")
        actions.append("If critical path is logic-dominated (>4 LUT levels), add pipeline stages in RTL.")
        actions.append("If critical path is net-dominated (>60% routing delay), inspect Floorplan and apply Pblock constraint.")

    if has_whs_violation:
        actions.append("Hold timing violated (WHS < 0). Typically caused by clock skew or asynchronous domain transfers.")
        actions.append("Ensure asynchronous clock groups are decoupled using `set_clock_groups -asynchronous` in .fdc.")

    if unrouted_count > 0:
        actions.append(f"Encountered unrouted nets ({unrouted_count}). Increase congestion effort: `dev_pnr -congestion_effort high -hotspot_removal on`.")

    return {
        "report_type": "Place & Route (.prr)",
        "findings": findings,
        "recommended_actions": actions,
        "summary": "PRR analysis complete. Follow recommended actions for timing closure."
    }
