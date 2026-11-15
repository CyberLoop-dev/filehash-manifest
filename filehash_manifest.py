#!/usr/bin/env python3
"""Create and verify SHA-256 manifests for local files."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def create(root, output):
    root = root.resolve()
    output = output.resolve()
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.resolve() != output:
            files[path.relative_to(root).as_posix()] = digest(path)
    output.write_text(json.dumps({"algorithm": "sha256", "files": files}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(files)} entries to {output}")

def verify(manifest, root):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    failed = 0
    for rel, expected in data.get("files", {}).items():
        path = root / rel
        if not path.is_file():
            print("MISSING", rel); failed += 1
        elif digest(path) != expected:
            print("CHANGED", rel); failed += 1
        else:
            print("OK", rel)
    print(f"Verification failures: {failed}")
    return 1 if failed else 0

def main():
    parser = argparse.ArgumentParser(description="Create or verify SHA-256 file manifests.")
    sub = parser.add_subparsers(dest="command", required=True)
    create_parser = sub.add_parser("create")
    create_parser.add_argument("root", type=Path)
    create_parser.add_argument("-o", "--output", type=Path, default=Path("manifest.json"))
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("manifest", type=Path)
    verify_parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.command == "create":
        create(args.root, args.output)
    else:
        raise SystemExit(verify(args.manifest, args.root))

if __name__ == "__main__":
    main()
