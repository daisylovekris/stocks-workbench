#!/usr/bin/env python3
"""Generate a deterministic Phase C review manifest outside the repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from tools import review_manifest as rm
except ModuleNotFoundError:  # pragma: no cover - direct execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import review_manifest as rm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a deterministic review manifest from locked official facts and a Phase B runner manifest"
    )
    parser.add_argument("--symbol", required=True, help="Six-digit A-share symbol")
    parser.add_argument("--date", required=True, dest="trade_date", help="Canonical trade date YYYY-MM-DD")
    parser.add_argument("--runtime-dir", default=str(rm.DEFAULT_RUNTIME_DIR), help="Repository-external runtime root")
    parser.add_argument("--runner-manifest", type=Path, help="Schema-valid Phase B official-write manifest")
    parser.add_argument(
        "--rebuild-from-official",
        action="store_true",
        help="Rebuild from official bytes; runner manifest becomes optional auxiliary evidence",
    )
    return parser


def execute(args: argparse.Namespace) -> rm.ReviewResult:
    if not args.rebuild_from_official and args.runner_manifest is None:
        raise rm.ReviewError("runner_manifest_required", "--runner-manifest is required unless --rebuild-from-official is used")
    return rm.generate_review(
        rm.ReviewOptions(
            runtime_dir=Path(args.runtime_dir),
            symbol=args.symbol,
            trade_date=args.trade_date,
            runner_manifest_path=args.runner_manifest,
            rebuild_from_official=args.rebuild_from_official,
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = execute(args)
    except rm.ReviewError as exc:
        print(
            json.dumps(
                {"status": "failed", "reason_code": exc.reason_code, "message": rm.sanitize_text(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI fails closed with sanitized diagnostics
        print(
            json.dumps(
                {"status": "failed", "reason_code": "review_generation_failed", "message": rm.sanitize_text(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "status": result.status,
                "reason_code": result.reason_code,
                "review_id": result.review_id,
                "review_state": result.review_state,
                "manifest_path": str(result.manifest_path) if result.manifest_path else None,
                "index_path": str(result.index_path) if result.index_path else None,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.status not in {"review_generator_already_active", "official_changed_during_generation"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
