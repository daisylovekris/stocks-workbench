#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
launcher="$repo_root/tools/codex-auto.sh"
fixture_dir="$(mktemp -d)"
trap 'rm -rf "$fixture_dir"' EXIT

mkdir -p "$fixture_dir/codex"
cat > "$fixture_dir/codex/stocks-mini.config.toml" <<'EOF'
model = "gpt-5.6-luna"
model_reasoning_effort = "low"
service_tier = "default"
EOF
cat > "$fixture_dir/codex/stocks-review.config.toml" <<'EOF'
model = "gpt-5.5"
model_reasoning_effort = "high"
service_tier = "default"
EOF

run() { CODEX_HOME="$fixture_dir/codex" "$launcher" "$@"; }
expect_route() { [[ "$(run --route-only "$2")" == "$1" ]]; }
expect_failure() { if run "$@" >/dev/null 2>&1; then return 1; fi; }

expect_route mini '准备单日 facts pack'
expect_route general '普通开发排查一个路由分支'
expect_route heavy '实现复杂自动化流程 runner'
expect_route review '请做最终代码审查'
expect_route mini '准备单日 facts pack，不要做代码审查'

cat > "$fixture_dir/luna.jsonl" <<'EOF'
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.6-luna","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/low.jsonl" <<'EOF'
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","effort":"low","collaboration_mode":{"settings":{"reasoning_effort":"low"}}}}
EOF
cat > "$fixture_dir/pass.jsonl" <<'EOF'
{"type":"turn_context","payload":{"turn_id":"old","model":"gpt-5.6-luna","effort":"low","collaboration_mode":{"settings":{"reasoning_effort":"low"}}}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF

expect_failure --review --verify-review-log "$fixture_dir/luna.jsonl" --session-id current
expect_failure --review --verify-review-log "$fixture_dir/missing.jsonl" --session-id current
expect_failure --review --verify-review-log "$fixture_dir/low.jsonl" --session-id current
run --review --verify-review-log "$fixture_dir/pass.jsonl" --session-id current | grep -qx 'actual_review_model=gpt-5.5'
run --review --verify-review-log "$fixture_dir/pass.jsonl" --session-id current | grep -qx 'actual_review_reasoning_effort=high'
expect_failure --mini --verify-review-log "$fixture_dir/pass.jsonl" --session-id current
expect_failure --review '请做最终代码审查'

printf '%s\n' 'codex-auto routing tests passed'
