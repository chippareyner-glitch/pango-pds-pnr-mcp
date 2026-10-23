"""
Command Line Interface (CLI) for PanGo PDS MCP Toolkit.
Supports running the MCP server or performing standalone linting, conversion, and pin checks.
"""

import sys
import argparse
from .server import app, main as run_server
from .knowledge.fdc_syntax import lint_and_diagnose_fdc, convert_xdc_to_pango_fdc
from .knowledge.pinout_pg2l200h import check_pin_legality
from .knowledge.pnr_optimization import PDS_SHELL_TCL_TEMPLATES

def main():
    parser = argparse.ArgumentParser(
        description="PanGo PDS Place & Route (P&R) Expert MCP Toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run (MCP Server)
    subparsers.add_parser("run", help="Run the MCP server over stdio")

    # Command: lint (FDC Linter)
    lint_parser = subparsers.add_parser("lint", help="Lint an FDC constraint file for Vivado XDC errors")
    lint_parser.add_argument("file", help="Path to .fdc file")

    # Command: convert (XDC to FDC)
    conv_parser = subparsers.add_parser("convert", help="Convert Vivado XDC file to PanGo FDC")
    conv_parser.add_argument("file", help="Path to input .xdc file")
    conv_parser.add_argument("-o", "--output", help="Path to output .fdc file (optional)")

    # Command: check-pin (Pin Legality)
    pin_parser = subparsers.add_parser("check-pin", help="Check pin legality on PG2L200H-FBB484")
    pin_parser.add_argument("pin", help="Pin name (e.g. Y12, B10, M2)")
    pin_parser.add_argument("-f", "--function", default="clock_input", help="Desired function (clock_input, dqs_strobe, general_io)")

    # Command: tcl (Generate Tcl)
    tcl_parser = subparsers.add_parser("tcl", help="Output automated pds_shell Tcl script")
    tcl_parser.add_argument("--flow", default="complete_batch_flow", choices=list(PDS_SHELL_TCL_TEMPLATES.keys()))

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        run_server()
    elif args.command == "lint":
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        res = lint_and_diagnose_fdc(content)
        print(f"[*] Total Issues: {res['total_issues']}")
        for iss in res["issues"]:
            print(f"  Line {iss['line_number']}: {iss['problem']}")
            print(f"    Original:   {iss['original_line']}")
            print(f"    Suggestion: {iss['suggestion']}")
        if res["is_valid_pango_fdc"]:
            print("[+] Clean PanGo FDC syntax. Zero syntax errors detected!")
    elif args.command == "convert":
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        converted = convert_xdc_to_pango_fdc(content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(converted)
            print(f"[+] Successfully converted {args.file} -> {args.output}")
        else:
            print(converted)
    elif args.command == "check-pin":
        res = check_pin_legality(args.pin, args.function)
        print(f"Pin: {res.get('pin')} | Legal: {res.get('is_legal')} | Role: {res.get('role')}")
        if "warning" in res:
            print(f"[!] Warning: {res['warning']}")
        if "note" in res:
            print(f"[*] Note: {res['note']}")
    elif args.command == "tcl":
        print(PDS_SHELL_TCL_TEMPLATES[args.flow])

if __name__ == "__main__":
    main()
