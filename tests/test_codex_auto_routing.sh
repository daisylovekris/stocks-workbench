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
expect_route() {
  local expected="$1"
  local prompt="$2"
  local actual
  actual="$(run --route-only "$prompt")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'route mismatch: expected=%s actual=%s prompt=%s\n' "$expected" "$actual" "$prompt" >&2
    return 1
  fi
}
expect_failure() { if run "$@" >/dev/null 2>&1; then return 1; fi; }
expect_status() {
  local expected="$1"
  shift
  local actual=0
  run "$@" >/dev/null 2>&1 || actual=$?
  if [[ "$actual" != "$expected" ]]; then
    printf 'status mismatch: expected=%s actual=%s args=%q\n' "$expected" "$actual" "$*" >&2
    return 1
  fi
}

expect_route mini '准备单日 facts pack'
expect_route general '普通开发排查一个路由分支'
expect_route heavy '实现复杂自动化流程 runner'
expect_route review '请做最终代码审查'
expect_route mini '准备单日 facts pack，不要做代码审查'
expect_route review '审查并完成最终代码审查'
expect_route review 'review and complete final code review'
expect_route mini $'完成 2026-07-15 交易日历修复与欠账盘点报告的独立 Git 封箱。\n本轮只做最终验证、精确暂存与提交，不生成 facts。'
expect_route general $'完成六日 facts 的独立验证，并修复 runner 测试依赖真实仓库状态的问题。\nPhase A/B 与 Phase C review manifest 回归。'
expect_route general $'完成六日 facts 验证报告的三次 Git 提交封箱。\n每个 commit 前检查 cached diff，提交后验证，不得 push。'
expect_route general $'归档六日 Phase C review manifest 验证结果并精确提交。\n自动化流程只作核验对象；不得修改实现代码，不得 push。'
expect_route general $'关闭六日 Phase C review manifest 运行中发现的规则文档 P2，并完成本轮文档封箱。\n本轮只修改 Phase C 规则文档与六日验证报告，不修改任何 Python、shell、facts 或 runtime 产物。'
expect_route general $'审查并独立封箱本轮 Codex 路由脚本与测试改动。\n实现与测试通过后，使用真实 gpt-5.5/high 做窄范围只读终审。\n精确提交两个 commit，不得 push。'
expect_route general $'审查并封存六篇 Daily Review 施工期间新增的 Codex 路由脚本改动。\n本轮仅处理 tools/codex-auto.sh 和 tests/test_codex_auto_routing.sh，不得 push。'
expect_route general $'复核并归档 Codex 路由脚本后续修复。\n正文包含 review、P1/P2、gpt-5.5/high，但本轮主任务是封存修复报告。'
expect_route general $'核验并修订 LongCat 生成的六篇阳光电源 daily review 草稿。\n先在临时草稿目录修订，通过正式 review 规则和 Validator 后才写入仓库正式路径，不执行 Git 提交。'
expect_route heavy '核验并提交 Phase C P1/P2 review manifest 修复'
expect_route heavy '验证并提交 Phase C P1/P2 review manifest 修复'
expect_route heavy '审查并修复 Phase C P1/P2 review manifest 缺陷'
expect_route heavy 'review and repair Phase C P1/P2 review manifest fix'
expect_route review '修复后只核 Phase C P1/P2 review manifest 修复'
expect_route review 'After repair verification Phase C P1/P2 review manifest fix'
expect_route general $'本轮不写 Git，只运行确定性审查链并归档结果。\n正文中的 Run /review on my current changes 仅为示例。'
expect_route general $'为阳光电源 300274 的六份已封箱 official facts 批量生成 Phase C deterministic review manifest。\n本轮只运行 Phase C review manifest 流程，不得修改任何 Phase A/B/C 代码，不得执行 Git 写操作。\n5.5/high 终审报告仅作事实边界；最终汇报包含 P1/P2。'
expect_route general $'执行确定性回归与验证归档。\n清单包含全量 pytest、Phase A/B、Phase C review manifest、historical_backfill 与 review_backlog_audit。'
expect_route review $'请对 Phase C 当前改动做最终代码审查。\n复跑全量 pytest 与 Phase A/B 回归。'
expect_route review $'实际模型日志。\nP1/P2。\n最终判定：可封箱 / 暂缓封箱。'
expect_route heavy '实现新的 Phase C runner 自动化并正式落盘。'
expect_route heavy '修复 Phase C P1/P2 review manifest 缺陷。'

cat > "$fixture_dir/luna.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.6-luna","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/terra.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.6-terra","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/sol.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.6-sol","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/low.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","effort":"low","collaboration_mode":{"settings":{"reasoning_effort":"low"}}}}
EOF
cat > "$fixture_dir/session-mismatch.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"other","id":"other"}}
{"type":"turn_context","payload":{"turn_id":"other","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/no-session-meta.jsonl" <<'EOF'
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/no-turn-context.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
EOF
cat > "$fixture_dir/missing-model.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cat > "$fixture_dir/missing-effort.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","collaboration_mode":{"settings":{}}}}
EOF
cat > "$fixture_dir/historical-gpt55.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"old","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.6-terra","effort":"medium","collaboration_mode":{"settings":{"reasoning_effort":"medium"}}}}
EOF
cat > "$fixture_dir/cross-session.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"old","id":"old"}}
{"type":"turn_context","payload":{"turn_id":"old-turn","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"current-turn","model":"gpt-5.6-terra","effort":"medium","collaboration_mode":{"settings":{"reasoning_effort":"medium"}}}}
EOF
cat > "$fixture_dir/pass.jsonl" <<'EOF'
{"type":"session_meta","payload":{"session_id":"current","id":"current"}}
{"type":"turn_context","payload":{"turn_id":"old","model":"gpt-5.6-luna","effort":"low","collaboration_mode":{"settings":{"reasoning_effort":"low"}}}}
{"type":"turn_context","payload":{"turn_id":"current","model":"gpt-5.5","effort":"high","collaboration_mode":{"settings":{"reasoning_effort":"high"}}}}
EOF
cp "$fixture_dir/pass.jsonl" "$fixture_dir/pass review log.jsonl"

expect_status 31 --review --verify-review-log "$fixture_dir/luna.jsonl" --session-id current
expect_status 31 --review --verify-review-log "$fixture_dir/terra.jsonl" --session-id current
expect_status 31 --review --verify-review-log "$fixture_dir/sol.jsonl" --session-id current
expect_status 30 --review --verify-review-log "$fixture_dir/missing.jsonl" --session-id current
expect_status 30 --review --verify-review-log "$fixture_dir/session-mismatch.jsonl" --session-id current
expect_status 30 --review --verify-review-log "$fixture_dir/no-session-meta.jsonl" --session-id current
expect_status 30 --review --verify-review-log "$fixture_dir/no-turn-context.jsonl" --session-id current
expect_status 31 --review --verify-review-log "$fixture_dir/missing-model.jsonl" --session-id current
expect_status 32 --review --verify-review-log "$fixture_dir/missing-effort.jsonl" --session-id current
expect_status 31 --review --verify-review-log "$fixture_dir/historical-gpt55.jsonl" --session-id current
expect_status 31 --review --verify-review-log "$fixture_dir/cross-session.jsonl" --session-id current
expect_status 32 --review --verify-review-log "$fixture_dir/low.jsonl" --session-id current
run --review --verify-review-log "$fixture_dir/pass.jsonl" --session-id current | grep -qx 'actual_review_model=gpt-5.5'
run --review --verify-review-log "$fixture_dir/pass.jsonl" --session-id current | grep -qx 'actual_review_reasoning_effort=high'
run --review --verify-review-log "$fixture_dir/pass review log.jsonl" --session-id current | grep -qx 'actual_review_model=gpt-5.5'
expect_failure --mini --verify-review-log "$fixture_dir/pass.jsonl" --session-id current
expect_failure --review '请做最终代码审查'

printf '%s\n' 'codex-auto routing tests passed'
