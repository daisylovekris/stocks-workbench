# Closed contract

`work_status = completed | in_progress | planned | deferred | unknown`; `design_status = not_started | in_progress | frozen_design | deferred | unknown | not_applicable`; `implementation_status = not_started | in_progress | implemented | deferred | unknown | not_applicable`; `validation_status = not_started | in_progress | validated | failed | deferred | unknown | not_applicable`; `closure_status = open | closed | deferred | unknown | not_applicable`.

`completed_scopes` is an array of only `design | implementation | validation | closure | mechanism`; `closure_scope = design | implementation | mechanism | project | not_applicable`; `memory_evidence_status = current | stale | path_missing | implementation_conflict | stale_closure | blocked_data_conflict | adjudication_required | pending_evidence | superseded | unknown`; `evidence_disposition = admitted | excluded_diagnostic | superseded | pending`.
