# Sunday Weekly Pipeline v0.1｜设计验证 r6

r5 包保持原样。r6 将 Phase B/C authority 改为与现行实现兼容：Phase C 只由 review index 唯一解析，Phase B 只由已验证 Phase C manifest 的 runner reference 解析并现场复证。虚构 symbol-hash evidence paths 已删除。

唯一 semantic config 是封存 JSON raw bytes，其 SHA 进入 input set/manifest/live revalidation。真实 Phase B/Phase C 实现和规则快照、module map、测试矩阵均在 package SHA 内。

`P1=0`、`P2=0`、`P3=0`、`FOCUSED_CLOSURE_READY=YES`。本 body identity-free。
