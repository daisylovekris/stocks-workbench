# Safe-read and lock design r10

Schema, Phase C index/manifest, runner and facts use same-FD safe bytes/SHA/JSON. Schema/config identity is rechecked at initial and final lock. Review locks derive only from review_manifest.review_lock_path and are sorted; lock order request → review → official, repeated at final authority recheck.
