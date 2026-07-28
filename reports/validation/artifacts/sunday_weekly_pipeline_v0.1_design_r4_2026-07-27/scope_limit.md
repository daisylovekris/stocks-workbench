# 范围限制 r4

本包仅定义未来 Sunday Weekly Pipeline v0.1 实现的冻结前契约和 focused closure 输入。不实现代码，不修改 facts、Daily Review、weekly、current cards 或 index，不运行 runner，不执行 `git add`、commit、push。

r3 包保持原样。外部 focused closure 必须只读取本 bundle，并由 bundle 外部提供三枚身份 SHA；不读取 r3 或其他外部审查材料。
