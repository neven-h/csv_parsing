from __future__ import annotations

import argparse

from bank_csv_normalizer.convert import convert
from bank_csv_normalizer.normalize.io import load_csv, load_excel
from bank_csv_normalizer.detect import detect_profile


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="banknorm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_detect = sub.add_parser("detect", help="Detect which bank profile matches the CSV")
    p_detect.add_argument("input", help="Path to input CSV")

    p_convert = sub.add_parser("convert", help="Convert bank CSV to canonical import format")
    p_convert.add_argument("input", help="Path to input CSV")
    p_convert.add_argument("--out", required=True, help="Path to output canonical CSV")
    p_convert.add_argument("--report", required=False, help="Path to output JSON report")

    args = parser.parse_args(argv)

    if args.cmd == "detect":
        lr = load_csv(args.input)
        m = detect_profile(lr.df)
        print(f"profile={m.name} confidence={m.confidence:.2f}")
        if m.reasons:
            print("reasons:")
            for r in m.reasons:
                print(f" - {r}")
        return 0

    if args.cmd == "convert":
        rep = convert(args.input, args.out, args.report)
        print(rep.to_json())
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
