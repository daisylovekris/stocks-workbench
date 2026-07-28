# Golden candidate derivation

The fully sealed input set is `73f08a768f883e54b0d4eaf76c241a0565c469c8c3bfc89d03eef93ed1200a41`; its ordered raw-SHA ledger is `golden_input_set_300274_2026-07-20_24.json`. The candidate is `golden_candidate_300274_2026-07-26.json`, SHA-256 `4bc7206f8ece09a7311f68fd4079e502b228c05358cccd4d5fd4f9e0ac6a1549`, and AJV draft-2020 validates it.

With Decimal precision=28 and ROUND_HALF_EVEN: week_open=102; week_high=120.45; week_low=99.77; week_close=113.42; weekly_change_pct=`(113.42 / 101.61 - 1) * 100`=`11.6228717645900993996653873`; total_amount=401.2112804; average_amount=80.24225608; average_turnover_rate=4.608; average_volume_ratio=1.076; trading_day_count=5. The prior r10 spelling ending in `...38727` is not repeated: it is incompatible with this explicitly fixed precision/order and r10 remains untouched.

`golden_unresolved_fields_300274_2026-07-20_24.json` contains 20 nonempty entries derived only from the five authoritative Phase C manifests, with trade_date added and `(trade_date,source,field)` sorting.
