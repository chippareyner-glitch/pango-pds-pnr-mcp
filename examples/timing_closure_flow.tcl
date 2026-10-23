# ==============================================================================
# PanGo PDS Automated Batch Tcl Flow (pds_shell)
# Target Device: PanGo Logos-2 PG2L200H-6FBB484
# Usage: pds_shell -f timing_closure_flow.tcl
# ==============================================================================

set PROJECT_NAME "pangu_project"
set DEVICE_PART  "PG2L200H-6FBB484"
set TOP_MODULE   "pangu_top"

puts "=========================================================="
puts "  PanGo PDS Automated Place & Route Flow Starting..."
puts "  Device: $DEVICE_PART | Top: $TOP_MODULE"
puts "=========================================================="

# 1. Project Management
if {[file exists ${PROJECT_NAME}.pds]} {
    puts "--> Opening existing project: ${PROJECT_NAME}.pds"
    open_project -project ${PROJECT_NAME}.pds
} else {
    puts "--> Creating new project: ${PROJECT_NAME}"
    create_project -name ${PROJECT_NAME} -device ${DEVICE_PART} -dir ./work
    add_file -format verilog [glob ./rtl/*.v]
    add_file -format fdc ./constraints/pds_constraints.fdc
    set_top_module ${TOP_MODULE}
}

# 2. Elaboration & Synthesis
puts "--> Running RTL Elaboration & Synthesis..."
compile -top ${TOP_MODULE}
synthesize -effort high

# 3. Device Mapping (dev_map)
puts "--> Running Device Mapping (dev_map)..."
dev_map -effort timing -optimize_drm true -optimize_apm true -register_duplication true

# 4. Place & Route (dev_pnr)
puts "--> Running Timing-Driven Place & Route (dev_pnr)..."
dev_pnr -opt_effort high \
        -timing_effort timing_driven \
        -congestion_effort medium \
        -hotspot_removal on \
        -wire_delay_model realistic

# 5. Timing Reports Extraction
puts "--> Generating Timing Analysis Reports..."
file mkdir ./reports
report_timing -setup -npaths 20 -file ./reports/setup_timing.rpt
report_timing -hold  -npaths 20 -file ./reports/hold_timing.rpt
report_congestion -file ./reports/congestion.rpt

# 6. Bitstream Generation
puts "--> Generating FPGA Bitstream (.sbit)..."
file mkdir ./output
gen_bitstream -file ./output/${PROJECT_NAME}.sbit

puts "=========================================================="
puts "  [SUCCESS] PDS P&R Batch Flow Finished Successfully!"
puts "=========================================================="
exit
