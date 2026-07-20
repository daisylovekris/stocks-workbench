#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  codex-auto.sh [--mini|--general|--heavy|--review|--high|--conservative] [--route-only|--dry-run|--verify-mapping] [--verify-review-log PATH --session-id ID] [prompt...]

Defaults to the mini/light route for small, bounded work. General development
uses Terra, complex implementation uses Sol, and final review uses GPT-5.5.
--high is a deprecated alias for --review.

Flags:
  --route-only              Print the chosen logical route and exit.
  --dry-run                 Print the logical route and command without starting Codex.
  --verify-mapping          Validate both configured routes and print the resolved mapping.
  --verify-review-log PATH  Fail closed unless PATH records this review session as gpt-5.5/high.
  --session-id ID           Required with --verify-review-log; selects the current session record.
  --conservative            Prefer mini after explicit review/heavy checks.

Routing configuration:
  stocks-mini   -> gpt-5.6-luna / low
  general       -> gpt-5.6-terra / medium
  heavy         -> gpt-5.6-sol / high
  stocks-review -> gpt-5.5 / high

Mini and review profiles are required. The launcher fails closed if either is
missing, cannot be parsed, or does not match its model, effort, and service tier.
EOF
}

route="auto"
prompt_parts=()
route_only=false
dry_run=false
verify_mapping=false
verify_review_log=""
session_id=""
conservative="${CODEX_STOCKS_CONSERVATIVE:-false}"
codex_bin="${CODEX_BIN:-codex}"
codex_home="${CODEX_HOME:-$HOME/.codex}"
deprecated_high=false

while (($#)); do
  case "$1" in
    --mini)
      route="mini"
      shift
      ;;
    --review)
      route="review"
      shift
      ;;
    --general)
      route="general"
      shift
      ;;
    --heavy)
      route="heavy"
      shift
      ;;
    --high)
      route="review"
      deprecated_high=true
      shift
      ;;
    --conservative)
      conservative=true
      shift
      ;;
    --route-only)
      route_only=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --verify-mapping)
      verify_mapping=true
      shift
      ;;
    --verify-review-log)
      [[ $# -ge 2 ]] || { printf '%s\n' '--verify-review-log requires a path' >&2; exit 2; }
      verify_review_log="$2"
      shift 2
      ;;
    --session-id)
      [[ $# -ge 2 ]] || { printf '%s\n' '--session-id requires an id' >&2; exit 2; }
      session_id="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      prompt_parts+=("$1")
      shift
      ;;
  esac
done

prompt=""
if ((${#prompt_parts[@]})); then
  prompt="${prompt_parts[*]}"
fi
prompt_lc="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"
prompt_title="$(printf '%s\n' "$prompt_lc" | awk 'NF { print; exit }')"

is_explicit_review_prompt() {
  local text="$1"
  case "$text" in
    *不要做*审查*|*无需*审查*|*不需要*审查*|*禁止*审查*|*不得*审查*|*不要*复查*)
      return 1
      ;;
  esac
  case "$text" in
    *代码审查*|*最终代码审查*|*最终审查*|*终审*|*审查当前改动*|*审阅当前改动*|*复核当前改动*|*窄审*|*复审*|*复查*|*核验*|*只核*|*核这张*|*核矩阵*|*实现审计*|*自动化审计*|*流水线审计*|*仓库审计*)
      return 0
      ;;
  esac
  [[ "$text" =~ (^|[[:space:][:punct:]])/?(code[[:space:]]+review|final[[:space:]]+code[[:space:]]+review|review[[:space:]]+current[[:space:]]+changes|review[[:space:]]+on[[:space:]]+my[[:space:]]+current[[:space:]]+changes|recheck|verification|(implementation|automation|pipeline|repository)[[:space:]_-]+audit)([[:space:][:punct:]]|$) ]]
}

is_primary_heavy_prompt() {
  local text="$1"
  if [[ "$text" =~ ^[[:space:]#\>\*\-]*(实现审计|implementation[[:space:]_-]+audit) ]]; then
    return 1
  fi
  [[ "$text" =~ ^[[:space:]#\>\*\-]*(实现|新增|构建|开发|重构).*(phase[[:space:]_-]*[a-z]|runner|运行器|自动化|流水线|正式|落盘|事务|并发) ]] ||
    [[ "$text" =~ ^[[:space:]#\>\*\-]*(implement|build|develop|refactor|migrate).*(phase[[:space:]_-]*[a-z]|runner|automation|pipeline|transaction|concurr) ]]
}

is_general_completion_prompt() {
  local text="$1"
  [[ "$text" =~ (完成|封箱|归档|提交).*(codex[[:space:]]*路由|路由规则|fable|外审|独立封箱|归档|封箱) ]] ||
    [[ "$text" =~ (codex[[:space:]]*路由|路由规则|fable|外审).*(完成|封箱|归档|提交) ]] ||
    [[ "$text" =~ \b(?:complete|archive|seal|commit)\b.*\b(?:codex[[:space:]_-]*routing|route|fable|external[[:space:]_-]*review)\b ]]
}

# A Phase C P1/P2 repair or its follow-up verification is still
# implementation-grade work even when the prompt says "review" or "read-only".
# Keep this narrow so ordinary final reviews continue to use the 5.5 route.
is_heavy_repair_verification_prompt() {
  local text="$1"
  [[ "$text" =~ phase[[:space:]_-]*c ]] || return 1
  [[ "$text" =~ (p1|p2|p1[[:space:]_-]*/[[:space:]_-]*p2) ]] || return 1
  [[ "$text" =~ (修复|修补|整改|fix|repair|remediat) ]] || return 1
  if [[ "$text" =~ (修完后|修复后|修补后|整改后|after[[:space:]_-]+(fix|repair|remediat)).*(只核|核验|复查|复审|窄审|review|recheck|verification) ]]; then
    return 1
  fi
  [[ "$text" =~ (二次|窄范围|只读核验|核验|复查|再审|second[[:space:]_-]+pass|verification|recheck) ]] ||
    [[ "$text" =~ ^[[:space:]#\>\*\-]*(修复|修补|整改|fix|repair|remediat) ]]
}

if [[ "$route" == "auto" ]]; then
  if is_heavy_repair_verification_prompt "$prompt_title"; then
    route="heavy"
  elif is_explicit_review_prompt "$prompt_title"; then
    route="review"
  elif is_primary_heavy_prompt "$prompt_title"; then
    route="heavy"
  elif is_general_completion_prompt "$prompt_title"; then
    route="general"
  elif is_explicit_review_prompt "$prompt_lc"; then
    route="review"
  elif [[ "$prompt_lc" =~ (多文件.*(修改|实现|施工|重构)|跨文件.*(修改|实现|施工|重构)|(架构|自动化|流水线).*(实现|施工|落地|重构)|(实现|施工|落地|重构).*(架构|自动化|流水线)|复杂(调试|修复|迁移|集成)|(实现|新增|构建).*(runner|运行器|自动化|流水线|生成器|调度器|流程)) ]]; then
    route="heavy"
  elif is_general_completion_prompt "$prompt_lc"; then
    route="general"
  elif [[ "$conservative" == true ]]; then
    route="mini"
  elif [[ "$prompt_lc" =~ (review[[:space:]_-]*route[[:space:]_-]*ok|多[[:space:]-]*card|multi[[:space:]-]*card|current/history|current[[:space:]-]*history|语义迁移|migration|p1/p2|p1[[:space:]-]*p2|架构文档|自动化流程设计|fable|integrat|sync|同步) ]]; then
    route="review"
  elif [[ "$prompt_lc" =~ (常规(开发|修改|排查)|普通(开发|修改|排查)|少量跨文件) ]]; then
    route="general"
  else
    route="mini"
  fi
fi

if [[ "$deprecated_high" == true ]]; then
  printf 'route=high is deprecated; using route=review\n' >&2
fi

load_profile() {
  local profile_name="$1"
  local expected_model="$2"
  local expected_effort="$3"
  local expected_service_tier="$4"
  local profile_path="$codex_home/$profile_name.config.toml"

  if [[ ! -f "$profile_path" ]]; then
    printf 'missing required profile: %s\n' "$profile_path" >&2
    return 1
  fi

  python3 - "$profile_path" "$expected_model" "$expected_effort" "$expected_service_tier" <<'PY'
import pathlib
import sys
import tomllib

path = pathlib.Path(sys.argv[1])
expected_model = sys.argv[2]
expected_effort = sys.argv[3]
expected_service_tier = sys.argv[4]

try:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"failed to parse {path}: {exc}", file=sys.stderr)
    raise SystemExit(1)

model = data.get("model")
effort = data.get("model_reasoning_effort")
service_tier = data.get("service_tier")

if not isinstance(model, str) or not isinstance(effort, str) or not isinstance(service_tier, str):
    print(f"invalid profile fields in {path}", file=sys.stderr)
    raise SystemExit(1)
if model != expected_model or effort != expected_effort or service_tier != expected_service_tier:
    print(
        f"profile mismatch in {path}: expected model={expected_model} reasoning_effort={expected_effort} service_tier={expected_service_tier}, got model={model} reasoning_effort={effort} service_tier={service_tier}",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(model)
print(effort)
PY
}

emit_route_info() {
  local route_name="$1"
  local profile_name="$2"
  local model="$3"
  local reasoning_effort="$4"
  printf 'route=%s\n' "$route_name"
  printf 'profile=%s\n' "$profile_name"
  printf 'model=%s\n' "$model"
  printf 'reasoning_effort=%s\n' "$reasoning_effort"
  printf 'model_switch=true\n'
  printf 'configured=true\n'
}

verify_actual_review_log() {
  local log_path="$1"
  local expected_session_id="$2"
  python3 - "$log_path" "$expected_session_id" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
session_id = sys.argv[2]
if not path.is_file():
    print("review log missing", file=sys.stderr)
    raise SystemExit(30)

matches = []
try:
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("type") != "turn_context":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("turn_id") != session_id:
            continue
        matches.append(payload)
except (OSError, UnicodeError, json.JSONDecodeError):
    print("review log unreadable", file=sys.stderr)
    raise SystemExit(30)

if not matches:
    print("current review session record missing", file=sys.stderr)
    raise SystemExit(30)

current = matches[-1]
model = current.get("model")
settings = current.get("collaboration_mode", {}).get("settings", {})
effort = settings.get("reasoning_effort") or current.get("effort")
if model != "gpt-5.5":
    print("current review session model mismatch", file=sys.stderr)
    raise SystemExit(31)
if effort != "high":
    print("current review session reasoning effort mismatch", file=sys.stderr)
    raise SystemExit(32)
print("actual_review_model=gpt-5.5")
print("actual_review_reasoning_effort=high")
PY
}

mini_info="$(load_profile "stocks-mini" "gpt-5.6-luna" "low" "default")"
review_info="$(load_profile "stocks-review" "gpt-5.5" "high" "default")"

mini_model="${mini_info%%$'\n'*}"
mini_effort="${mini_info#*$'\n'}"
review_model="${review_info%%$'\n'*}"
review_effort="${review_info#*$'\n'}"

if [[ "$mini_model" == "$review_model" ]]; then
  printf 'mini and review routes must resolve to different models\n' >&2
  exit 1
fi

if [[ "$verify_mapping" == true ]]; then
  emit_route_info "mini" "stocks-mini" "$mini_model" "$mini_effort"
  emit_route_info "general" "<direct>" "gpt-5.6-terra" "medium"
  emit_route_info "heavy" "<direct>" "gpt-5.6-sol" "high"
  emit_route_info "review" "stocks-review" "$review_model" "$review_effort"
  exit 0
fi

if [[ "$route" != "mini" && "$route" != "general" && "$route" != "heavy" && "$route" != "review" ]]; then
  printf 'unknown route selected: %s\n' "$route" >&2
  exit 1
fi

selected_profile=""
selected_model=""
selected_effort=""
case "$route" in
  mini)
    selected_profile="stocks-mini"
    selected_model="$mini_model"
    selected_effort="$mini_effort"
    ;;
  general)
    selected_profile=""
    selected_model="gpt-5.6-terra"
    selected_effort="medium"
    ;;
  heavy)
    selected_profile=""
    selected_model="gpt-5.6-sol"
    selected_effort="high"
    ;;
  review)
    selected_profile="stocks-review"
    selected_model="$review_model"
    selected_effort="$review_effort"
    ;;
esac

if [[ -n "$verify_review_log" && "$route" != "review" ]]; then
  printf '%s\n' 'review log verification is only valid for the review route' >&2
  exit 2
fi
if [[ -n "$verify_review_log" && -z "$session_id" ]]; then
  printf '%s\n' '--session-id is required for review log verification' >&2
  exit 2
fi
if [[ "$route" == "review" && "$route_only" == false && "$dry_run" == false && -z "$verify_review_log" ]]; then
  printf '%s\n' 'final review requires --verify-review-log PATH and --session-id ID; refusing unverified review' >&2
  exit 33
fi

command=(env CODEX_ROUTER_BYPASS=1 "$codex_bin")
if [[ -n "$prompt" ]]; then
  command+=(exec)
fi
if [[ -n "$selected_profile" ]]; then
  command+=(--profile "$selected_profile")
else
  command+=(--model "$selected_model")
  command+=(-c "model_reasoning_effort=\"$selected_effort\"")
  command+=(-c 'service_tier="default"')
fi

if [[ "$route_only" == true ]]; then
  printf '%s\n' "$route"
  exit 0
fi

if [[ "$dry_run" == true ]]; then
  emit_route_info "$route" "${selected_profile:-<direct>}" "$selected_model" "$selected_effort"
  if [[ -n "$prompt" ]]; then
    printf 'prompt_preview:\n%s\n' "$prompt"
  else
    printf 'prompt_preview: <interactive>\n'
  fi
  printf 'command:'
  printf ' %q' "${command[@]}"
  if [[ -n "$prompt" ]]; then
    printf ' %q' "$prompt"
  fi
  printf '\n'
  if [[ -n "$verify_review_log" ]]; then
    verify_actual_review_log "$verify_review_log" "$session_id"
  fi
  exit 0
fi

# With no prompt this is the post-run verification form; never open an
# interactive Codex session merely to inspect a completed review log.
if [[ -n "$verify_review_log" && -z "$prompt" ]]; then
  verify_actual_review_log "$verify_review_log" "$session_id"
  exit 0
fi

if [[ -n "$prompt" ]]; then
  "${command[@]}" "$prompt"
else
  "${command[@]}"
fi
if [[ -n "$verify_review_log" ]]; then
  verify_actual_review_log "$verify_review_log" "$session_id"
fi
