#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  codex-auto.sh [--mini|--review|--high|--conservative] [--route-only|--dry-run|--verify-mapping] [prompt...]

Defaults to the mini route for small, bounded work. Use --review to force the
review route when the task needs cross-file synchronization, semantic migration,
or architecture-level thinking. --high is a deprecated alias for --review.

Flags:
  --route-only              Print the chosen logical route and exit.
  --dry-run                 Print the logical route and command without starting Codex.
  --verify-mapping          Validate both configured routes and print the resolved mapping.
  --conservative            Lock the route to mini unless --review is explicit.

Routing configuration:
  stocks-mini   -> gpt-5.4-mini / high
  stocks-review -> gpt-5.5 / high

Profiles are required. The launcher fails closed if a profile is missing,
cannot be parsed, or does not match the expected model and reasoning effort.
EOF
}

route="auto"
prompt_parts=()
route_only=false
dry_run=false
verify_mapping=false
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

is_explicit_review_prompt() {
  local text="$1"
  case "$text" in
    *代码审查*|*最终代码审查*|*最终审查*|*审查当前改动*|*审阅当前改动*|*复核当前改动*)
      return 0
      ;;
  esac
  [[ "$text" =~ (^|[[:space:][:punct:]])/?(code[[:space:]]+review|final[[:space:]]+code[[:space:]]+review|review[[:space:]]+current[[:space:]]+changes|review[[:space:]]+on[[:space:]]+my[[:space:]]+current[[:space:]]+changes)([[:space:][:punct:]]|$) ]]
}

if [[ "$route" == "auto" ]]; then
  if is_explicit_review_prompt "$prompt_lc"; then
    route="review"
  elif [[ "$conservative" == true ]]; then
    route="mini"
  elif [[ "$prompt_lc" =~ (review[[:space:]_-]*route[[:space:]_-]*ok|多[[:space:]-]*card|multi[[:space:]-]*card|current/history|current[[:space:]-]*history|语义迁移|migration|p1/p2|p1[[:space:]-]*p2|架构文档|自动化流程设计|fable|integrat|sync|同步) ]]; then
    route="review"
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
  local profile_path="$codex_home/$profile_name.config.toml"

  if [[ ! -f "$profile_path" ]]; then
    printf 'missing required profile: %s\n' "$profile_path" >&2
    return 1
  fi

  python3 - "$profile_path" "$expected_model" "$expected_effort" <<'PY'
import pathlib
import sys
import tomllib

path = pathlib.Path(sys.argv[1])
expected_model = sys.argv[2]
expected_effort = sys.argv[3]

try:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"failed to parse {path}: {exc}", file=sys.stderr)
    raise SystemExit(1)

model = data.get("model")
effort = data.get("model_reasoning_effort")

if not isinstance(model, str) or not isinstance(effort, str):
    print(f"invalid profile fields in {path}", file=sys.stderr)
    raise SystemExit(1)
if model != expected_model or effort != expected_effort:
    print(
        f"profile mismatch in {path}: expected model={expected_model} reasoning_effort={expected_effort}, got model={model} reasoning_effort={effort}",
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

mini_info="$(load_profile "stocks-mini" "gpt-5.4-mini" "high")"
review_info="$(load_profile "stocks-review" "gpt-5.5" "high")"

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
  emit_route_info "review" "stocks-review" "$review_model" "$review_effort"
  exit 0
fi

if [[ "$route" != "mini" && "$route" != "review" ]]; then
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
  review)
    selected_profile="stocks-review"
    selected_model="$review_model"
    selected_effort="$review_effort"
    ;;
esac

command=("$codex_bin")
if [[ -n "$prompt" ]]; then
  command+=(exec)
fi
command+=(--profile "$selected_profile")

if [[ "$route_only" == true ]]; then
  printf '%s\n' "$route"
  exit 0
fi

if [[ "$dry_run" == true ]]; then
  emit_route_info "$route" "$selected_profile" "$selected_model" "$selected_effort"
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
  exit 0
fi

if [[ -n "$prompt" ]]; then
  exec "${command[@]}" "$prompt"
fi
exec "${command[@]}"
