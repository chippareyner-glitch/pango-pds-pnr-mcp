"""
Unit Tests for PanGo PDS MCP Server and Knowledge Engine.
"""

import unittest
from pango_pds_mcp.knowledge.pnr_optimization import (
    PNR_STRATEGIES,
    PDS_SHELL_TCL_TEMPLATES,
    diagnose_mrp_report,
    diagnose_prr_report
)
from pango_pds_mcp.knowledge.fdc_syntax import (
    lint_and_diagnose_fdc,
    convert_xdc_to_pango_fdc
)
from pango_pds_mcp.knowledge.physical_constraints import generate_pblock_fdc
from pango_pds_mcp.knowledge.clock_architecture import diagnose_clock_routing
from pango_pds_mcp.knowledge.pinout_pg2l200h import check_pin_legality
from pango_pds_mcp.knowledge.high_speed_interfaces import get_high_speed_pnr_template

class TestPangoPdsMcp(unittest.TestCase):

    def test_pnr_strategies(self):
        self.assertIn("timing_driven_closure", PNR_STRATEGIES)
        self.assertIn("congestion_reduction", PNR_STRATEGIES)
        self.assertIn("zero_dsp_bnn_flow", PNR_STRATEGIES)

    def test_pds_shell_templates(self):
        self.assertIn("complete_batch_flow", PDS_SHELL_TCL_TEMPLATES)
        self.assertIn("dev_map", PDS_SHELL_TCL_TEMPLATES["complete_batch_flow"])
        self.assertIn("dev_pnr", PDS_SHELL_TCL_TEMPLATES["complete_batch_flow"])

    def test_fdc_linter_with_vivado_xdc(self):
        bad_xdc = """
        set_property PACKAGE_PIN Y12 [get_ports clk_50m]
        set_property IOSTANDARD LVCMOS33 [get_ports clk_50m]
        create_clock -name clk_50m -period 20.000 [get_ports clk_50m]
        """
        res = lint_and_diagnose_fdc(bad_xdc)
        self.assertFalse(res["is_valid_pango_fdc"])
        self.assertEqual(res["total_issues"], 2)
        self.assertIn("define_attribute {p:clk_50m} {PAP_IO_LOC} {Y12}", res["issues"][0]["suggestion"])

    def test_xdc_to_fdc_conversion(self):
        xdc = "set_property PACKAGE_PIN U14 [get_ports {cam_data[0]}]\nset_property IOSTANDARD LVCMOS33 [get_ports {cam_data[0]}]"
        fdc = convert_xdc_to_pango_fdc(xdc)
        self.assertIn("define_attribute {p:cam_data[0]} {PAP_IO_LOC} {U14}", fdc)
        self.assertIn("define_attribute {p:cam_data[0]} {PAP_IO_STANDARD} {LVCMOS33}", fdc)

    def test_pin_legality_checker(self):
        # Y12 is dedicated GCLK
        res_clk = check_pin_legality("Y12", "clock_input")
        self.assertTrue(res_clk["is_legal"])
        self.assertEqual(res_clk["role"], "Dedicated Global Clock Input")

        # U14 is not dedicated GCLK
        res_bad_clk = check_pin_legality("U14", "clock_input")
        self.assertFalse(res_bad_clk["is_legal"])

        # M2 is dedicated DQS strobe
        res_dqs = check_pin_legality("M2", "dqs_strobe")
        self.assertTrue(res_dqs["is_legal"])

    def test_clock_violation_diagnosis(self):
        err = "ERROR: Clock Routing Rule Violation: Non-clock pin connected directly to GCLK"
        res = diagnose_clock_routing(err)
        self.assertEqual(res["rule_id"], "RULE_CLK_001")
        self.assertIn("PAP_CLOCK_DEDICATED_ROUTE", res["remedies"][1])

    def test_pblock_generation(self):
        pblock = generate_pblock_fdc("pb_test", "u_top/u_child", "SLICE_X10Y10:SLICE_X20Y20")
        self.assertIn("create_pblock pb_test", pblock)
        self.assertIn("add_pblock_range -pblock pb_test {SLICE_X10Y10:SLICE_X20Y20}", pblock)

    def test_report_diagnostics(self):
        fake_mrp = "Resource Report:\nLUT5 Utilization: 85%\nWarning: 4 registers not packed into IOB\n"
        mrp_diag = diagnose_mrp_report(fake_mrp)
        self.assertEqual(mrp_diag["report_type"], "Device Map (.mrp)")
        self.assertTrue(len(mrp_diag["recommended_actions"]) > 0)

        fake_prr = "Routing Report:\nWNS: -0.320 ns\nWHS: 0.050 ns\nUnrouted nets: 0\n"
        prr_diag = diagnose_prr_report(fake_prr)
        self.assertTrue(len(prr_diag["recommended_actions"]) > 0)

if __name__ == "__main__":
    unittest.main()
