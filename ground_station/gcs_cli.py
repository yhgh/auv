#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import requests


def cmd_telemetry(source: str) -> None:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f'telemetry source not found: {source}')
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        print(
            f"depth={data.get('depth_m', 0):.2f}m "
            f"battery={data.get('battery_v', 0):.2f}V "
            f"mode={data.get('mode', 'UNKNOWN')}"
        )


def post_json(endpoint: str, payload: dict) -> None:
    url = f'http://127.0.0.1:8080{endpoint}'
    resp = requests.post(url, json=payload, timeout=2)
    resp.raise_for_status()
    print(resp.text)


def cmd_mission(cmd: str) -> None:
    post_json('/mission', {'cmd': cmd})


def cmd_depth(meters: float) -> None:
    post_json('/depth', {'target_depth': meters})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='AUV Ground Station CLI')
    sub = parser.add_subparsers(dest='subcmd', required=True)

    t = sub.add_parser('telemetry', help='Read telemetry from JSON lines file')
    t.add_argument('--source', required=True, help='Path to telemetry JSON lines file')

    m = sub.add_parser('mission', help='Send mission command')
    m.add_argument('--cmd', required=True, choices=['arm', 'disarm', 'start', 'stop', 'emergency', 'reset'])

    d = sub.add_parser('depth', help='Set target depth in meters')
    d.add_argument('--meters', required=True, type=float)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.subcmd == 'telemetry':
        cmd_telemetry(args.source)
    elif args.subcmd == 'mission':
        cmd_mission(args.cmd)
    elif args.subcmd == 'depth':
        cmd_depth(args.meters)


if __name__ == '__main__':
    main()
