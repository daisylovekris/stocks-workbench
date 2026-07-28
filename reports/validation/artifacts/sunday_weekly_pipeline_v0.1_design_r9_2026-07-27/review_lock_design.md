# Phase C review lock r9

Every Phase C lock path is obtained only by `review_manifest.review_lock_path(runtime_dir, symbol, trade_date)`; SWP never reproduces its hash. Sort returned review lock paths canonically, then acquire: request-key orchestration lock → review locks → official facts locks. The same order is used for snapshot and final authority recheck.
