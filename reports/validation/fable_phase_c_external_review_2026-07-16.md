# Fable Phase C 外审原文归档

> 来源：ZenMux / Fable 外审原始文本（以下正文逐字恢复，未改写、未缩写）。
>
> 外审日期：2026-07-16。
>
> 模型：Fable（经 ZenMux UI 发起；原始文本未提供可复核的精确模型版本）。
>
> 恢复方式：ZenMux UI 未回显该次外审正文；从本地 Codex 附件原文恢复。
>
> 日志来源：session `019f7b95-e7b6-7bd1-b34f-3fb87cdd5f04`，附件 `/Users/wongdaisy/.codex/attachments/67c75687-bcad-4125-83f8-13f16b6b3ced/pasted-text.txt`，恢复日期 2026-07-20。

---

外审完成。我通读了tools/run_daily_facts_after_close.py（Phase B runner全文）、tools/official_facts_transaction.py（write_action /部分策略/密封语义）、rules/run_daily_facts_after_close_phase_b_v0.2.md与rules/automation_architecture_v0.1.md，并确认data/daily/现有7个官方事实、运行时目录文件约定为仓库外~/Library/Application Support/Mimo-Lab/stocks-runtime。以下为有关外审结论，未修改任何文件。

总体结论
C阶段的正确形态是：审查清单只能是从官方事实派生出的直观视图，不是事实链的新一环。它应在运行时完全生成（仓库外），以官方SHA身份决定，机器最高推进到ready_for_human_review/ needs_manual_review，approved永远是人工专属。首版不需要LLM。_

对“三、必须回答的架构问题”的直接回答：

放位置：运行时目录runtime_dir/reviews/<trade_date>/<review_id>/，仓库内不落任何文件；人工确认后的归档动作延迟到D阶段。
是否正式属于事实链：不属于。它是派生读模型（读取模型），可以随时从官方+跑步者清单无损重建；事实链仍止于官方事实。
关系关系：官方事实是唯一权威。审核manifest与官方有任何矛盾，结论只有一个——manifest过期作废、重新生成；manifest永远不反向修改官方。
完整事实能否自动批准：不能。机器上限是ready_for_human_review。批准是决策取消验证结果，权限归人。
部分怎样醒目：facts_status=partial原样保留+摘要顶部固定横幅+missing/needs_manual_check原样批量批量上线（禁止改写成散文）+downstream_permissions全false。
人工字段防覆盖：人工决定写入独立文件decisions.jsonl（追加式），机器代码路径中根本不存在写它的函数；manifest一旦有对应决定就视为不可变。
第一版LLM：不引入。确定性模板足够，见下文。
审核生成失败是否影响官方：表单影响。官方在B阶段写入已完成提交；审核生成失败只是本身非零退出+可用--rebuild-from-official补偿重建。
上线全面项：见“P1风险”一个，共 6 项。
推迟事项：见“推迟事项”上文。
架构推荐
定位：人工确认前位于运行时，确认后才归档（归档本身推迟到D阶段）。理由：

审查清单每笔交易日至少生成一次，内容含run_id、时间等每次不同的字段。仓库仓库git status每天都会出现新的噪声，直接违背现有密封纪律（seal_check.py设计里“分阶段集合必须等于预期清单”）和测试矩阵里“Git工作树路径集合不变”的要求。
它可以从官方字节+运行程序清单确定性重建，丢失无害，属于天然运行时产物，与阶段A/B的候选/清单/警报同层。
只有经过人工approved的审核才具有归档价值；那是一个显着式人工触发的仓库包装动作，属于D阶段的“受控归档”工具，不属于C阶段。
目录布局（沿用现有运行时约​​定）：

文本

<runtime_dir>/reviews/<trade_date>/<review_id>/
    review_manifest.json      # 机器生成，原子写入
    review_summary.md         # 确定性模板渲染
    decisions.jsonl           # 只有人工命令追加，机器只读
<runtime_dir>/reviews/<trade_date>/review_index.jsonl   # 追加式索引，最后一条有效条目 = active review
<runtime_dir>/locks/review_<sha(symbol_date)>.lock      # flock，复用 runner_lock 模式
运行链（你给建议的链）：读取跑步者清单→在官方事实锁内重读官方字节并自算SHA→交叉核补充（清单里的official_sha256_after必须等于自算值）→对官方字节重跑vrc.assert_facts_pack_valid→派生状态→原子写摘要→原子写清单→索引边界（索引是最终提交标记，修改阶段B“清单是最终提交标记”的对应）→退出，等待人工。_

权威关系与人工边界
输入边界（问题2）：review manifest只允许读取——



允许来源	内容
官方事实文件（锁内重读）	bytes、自算 SHA、run.status、missing、needs_manual_check、quote 字段、source refs
runner manifest.json（schema校验后）	run_id、write_action、、、official_sha256_before/aftervalidator partial_write_policy、摘要、模式、原因
现场重跑的验证器	validator_result（不仅仅是信任体现里的历史记录）
禁止来源：generator stdout/stderr 文本（只能作为证明路径引用，不得解析取值）、任何 LLM 自由文本、警报文件（它是清单的降级副本）、环境变量或命令行里的“事实”参数、以及official_sha256_after与当前文件不符的过渡清单。特别是：missing、needs_manual_check、validator_result、write_action、所有 SHA、所有引用数值，必须且只能来自上表三个来源，且缺少 / need_manual_check 到官方文件内的设备参数（runner清单只用于交叉核对）。

人工控制门（问题5）：以下动作C阶段后仍全部人工触发——正式审核文档更新、五张当前卡、索引、每周、git add/ git commit、任何交易判断。机器端为提升人工效率应输出且只输出：一屏review_summary.md（outcome、write_action、SHA交互、validator状态、missing / needs_manual_check翻译清单、来源引用、以及一份待办清单对清单——是“建议你去核对什么”，而不是“我已替你更新什么”）。机器不生成任何可直接粘贴进正式审查的结论段落，这是权限边界的物理保证。

最小图式
schema_version: "review_manifest_v0.1"。字段如下（这是本设计最重要的一条线）：_

机器生成区（machine区，manifest主体）：

schema_version、review_id、run_id（来源 runner manifest；rebuild 模式下为 null）
symbol、trade_date、mode（today_after_close / historical_backfill / rebuild_from_official）
official_path（仓库相对路径，必须相等oft.canonical_official_path推导值）、official_sha256（自算）
facts_status（完整/部分，来自官方的run.status）
write_action、write_reason_code、official_sha256_before（计算自跑步者清单）
validator_result（现场重跑结果+跑者清单记录值的一致性标记）
missing、needs_manual_check（官方内部数据库原样复制，禁止改写）
confirmed_fields（引用核心8字段+已确认的验证字段清单）
unresolved_fields（缺少 ∪ need_manual_check ∪ postcheck 异常，机器派生）
partial_write_policy（测量）
evidence_summary、source_refs（来自官方的quote_verification/来源字段，路径在仓库与运行时内）
generated_at（亚洲/上海 ISO）、generator_version
review_state（机器只能写needs_manual_review / ready_for_ human_review）
downstream_permissions（机器恒定写全{review: false, current_cards: false, index: false, weekly: false, git: false, trading: false}假：）
provenance（rebuilt_from_official 标记、跑步者清单路径、诊断）_
人工专属区（不在manifest内，在decisions.jsonl）：

human_decision（批准/拒绝/重新开放）、human_notes、decided_at、针对的review_id+的决策official_sha256（防止决定被套用内容已变的清单上）。_
review_state的批准/拒绝是派生观点：manifest里永远不出现这两个值，读取方（人或未来D阶段工具）用manifest + Decisions.jsonl合成最终状态。这样机器重写manifest在结构上不可能抹掉人工决定。_

状态机
文本

(生成中，无 index 条目)  = draft，对外不可见，失败即消失
        │ 生成完成
        ▼
 needs_manual_review  ←─ partial / conflict / postcheck 失败 / validator 失败 / rebuild
 ready_for_human_review ←─ complete + validator passed + write_action ∈ {created, identical_noop}
        │ 人工 decisions.jsonl
        ▼
 approved / rejected   （仅人工）
        │ official SHA 变化 → 新 review_id 生成
        ▼
 superseded            （派生：不再是 index 中该 symbol+date 的最新有效条目）
逐项判断：

部分官方：一律needs_manual_review，即使是白名单合格部分且已落盘（与B相official_written_partial → needs_manual_review=true扫描对齐）。永远不进ready_for_human_review。
完整事实自动批准：不允许。上限ready_for_human_review。
官方冲突/后写失败：未发明新状态，用needs_manual_review+ write_reason_code（official_conflict/ official_written_postcheck_failed/ official_written_bytes_mismatch）表达，摘要顶部旗帜明示“官方文件当前不可信任/存在冲突，先做人工核验”。
清单但官方存在：--rebuild-from-official模式，锁内读官方、重跑验证器、生成清单，、，run_id=null状态provenance.rebuilt_from_official=true强制needs_manual_review（证据链不完整，机器不猜完成状态——与B期幂等的相同原则一致）。
人工否决后重新生成：被拒绝记录在decisions.jsonl，永不删除。官方SHA未变时重跑是无操作，拒绝持续有效——事实没变不太该轻微再出一份草稿；官方SHA变了才生成新review_id，旧的（覆盖其拒绝）作为保留在各自目录中，索引追加历史新使旧派生为被取代。_
幂等与矩阵
review_id 确定性派生：rev_<symbol>_<trade_date>_<official_sha256前12位>。 相同官方 SHA 重跑 → 算出相同 review_id → 发现存在合法清单且 SHA 一致 → review_already_existsno-op（exit 0）。
官方SHA修改→新review_id，新目录，追加索引；不触碰旧目录任何文件。
取代的是派生状态（索引中非最新），不通过回写旧清单实现——旧清单保持不可变，这同时解决“人工字段防重写”和“历史保留”。
损坏清单：读不出/SHA不符/schema未知 → 不修复不删除，原地留存，索引追加一条invalid诊断边境，按“穷人”处理走重建路径。
阵：per (symbol, trade_date) 的flock复用runner_lock模式；抢不到锁→review_generator_already_active跳过。index用O_APPEND单​​行JSON追加，行内含manifest SHA，损坏行可跳过可跳过。
Historical_backfill 与 Today_after_close 隔离：审核身份由官方 SHA 决定，与模式无关（同一官方只应有一份主动审核）；模式与回填原因记入provenance供审计区分，不参与身份。
人工字段防机器重写：三重保证——(1)人工内容机器从不写的独立文件；(2)存在决定的review_id，其manifest被生成器视为冻结，重写请求直接拒绝；(3)manifest不可变+取代派生化，机器没有任何“更新旧文件”的代码路径。
故障补偿
统一原则：fail-close = 宁可无审核清单，也不能与官方不符或未决事项被淡化的审核清单；且审核层故障永不回退、永不接触官方。

官方写入成功但runner manifest失败（Phase B的official_written_manifest_failed）：这就是Phase C补偿点——--rebuild-from-official用构造stderr中的官方路径+写入后SHA重建review记录，状态needs_manual_review。
官方写后验后失败：正常生成审核清单（这是它最有价值的场景），needs_manual_review+原原因码+横幅警告，下游为假。
审核清单写到一半失败：原子写（tmp + fsync + rename）保证不可行半成品；无索引边界即视为本次未发生，重跑幂等补齐。
Summary成功但manifest失败：写入顺序summary→manifest→index，index才是提交标记；孤儿summary无害，重跑原子覆盖（该review_id尚无人工决策，覆盖合法）。
清单成功但通知失败：阶段C无通知；设计上通知永远排在提交标记之后、失败不改变审核状态。
运行时不可写：沿用prepare_runtime_dir表单，失败关闭非零退出 + 包装stderr；表单回落到往仓库内写。
官方被人工修改：下次运行自算SHA与主动审核不符→旧审核派生被取代，生成新的review_id；如新内容为密封/手动官方，事实来源如实标签，仍needs_manual_review。
审核清单与官方SHA不一致：清单一票作废（stale），官方永远胜出，重新生成；任何下游读取方必须先做此一致性检查再使用清单。
LLM 是否进入首版
不进入。判断依据：C阶段v0.1的总结全部字段（状态、SHA、缺失清单、待办核对项）都是格式化数据的确定性投影，模板渲染即可，引入LLM只增加“部分被措辞软化”推测混入事实“两个新风险面而无信息增量。建议v0.1连--llm开关不留留，缩小审查面。D阶段若引入记述草稿，边界照你列的七条执行（只读已验证字段、不动事实/缺失/验证器、不输出交易、输出必须带源字段与未解决清单），且LLM输出全部独立的narrative_draft.md，绝不会写入review_manifest.json的机器区。

P1 / P2 / P3 风险
P1（上线爆发）：

摘要如何使用自由措辞复述部分/缺失——必须强制“谷歌翻译机逐条上市+顶部横幅”的确定性模板。
机器存在任何写decisions.jsonl或改写旧manifest的代码路径 —— 必须结构性不存在。
review 工件仓库工作树（第一临时文件）—— 必须复用normalize_runtime_dir拒绝运行时在仓库内，并测试断言 Git 路径集合保持。
信任过期运行器清单：manifest记录的official_sha256_after与当前官方自算SHA不一致时仍生成ready_for_human_review——必须降级needs_manual_review或拒绝。
downstream_permissions出现机器写出真实的路径。
来自 stdout / 自由文本解析事实字段。
P2：损坏清单触发无限重建循环（需无效边界重）；无锁周期导致相同review_id双写去；schema_version未做未知版本拒读；重建产物未标出处导致与全农产品产物不一致；validator消息未过sanitize_text。_

P3：index.jsonl 无限增长（按日分文件已填写）； generated_at 时区格式不统一；summary 排版细节；review_id 远端长度取舍。

Phase C v0.1 最小实施清单
文件（4个新增，0个修改现有正式文档）：

tools/review_manifest.py—— 库：schema 常量与校验、review_id 派生、输入加载与三方交叉核验（官方字节/运行器清单/现场验证器）、状态派生、原子写、索引追加、sanitize_text复用。
tools/generate_review_manifest.py—— CLI：--symbol --date --runtime-dir，模式--from-run <run_id>/ --latest-run/ --rebuild-from-official，flock、no-op 判定、退出码（0 生成或 no-op，2 需要手动审核，1 失败）。
rules/review_manifest_phase_c_v0.2.md—— 规格与人工操作手册（含人工决策的记录方式；v0.1人工决策可以先由人手工JSONL行，专用CLI追加延迟）。
tests/test_review_manifest.py—— 测试矩阵落地。
实现顺序：schema + review_id → 输入加载与交叉核验（这是安全核心，先做）→ 状态纯派生函数 → 原子写 + 索引提交标记 → CLI + 锁定 + no-op → 重建模式 → 测试补全。不做：LLM、通知、launchd、存档进仓库、新闻抓取、多符号批处理。_

测试矩阵
按你所列的类别逐项对应（逗号为断言要点）：

全部事实→ ready_for_human_review，下游全部错误。
符合条件的部分（official_writing_partial）→ needs_manual_review，缺少在清单和摘要中出现的译文。
ineligiblepart（partial_not_eligible_for_official，无官方写入）→ 生成基于跑步者清单的审查或拒绝？——v0.1 语音：无官方即无审查清单，输出诊断退出2（审查是官方的派生物，其中听觉测试锁死）。
missing / needs_manual_check 非空 → unresolved_fields 并集正确、摘要横幅存在、无任何改写。
Sametime_noop官方 → 正常生成，facts_status=complete。
官方冲突（conflict_blocked）→ needs_manual_review + reason_code 透传。
写入后失败（postcheck_failed / bytes_mismatch）→ 需要人工审核 + 关键。
同 SHA 重跑 → review_already_existsno-op，目录零。
官方 SHA 改变 → 新 review_id、旧边境派生 superseded、旧目录字节不变。
取代派生逻辑：指数多边境时活跃判定正确。
人工字段保护：存在decisions.jsonl时重写被拒绝；机器全流程运行完成decisions.jsonl 字节不变。
并发：双进程抢锁，只有一份清单。
原子写失败注入（更名抛错）→无半成品、无索引入境、非零退出。
运行时不可写→失败关闭，仓库零仓库。
损坏官方（JSON 坏/符号不符）→ 拒绝生成ready状态，诊断退出。
损坏旧清单→无效边境+重建路径，不修改损坏文件。
Historical_backfill → 出处记录模式与原因，review_id 与今天模式对相同 SHA （相同不产生双活动）。
敏感信息过滤：验证器消息含token样式字符串时manifest/summary中为[REDACTED]。
全流程交互sungrow/reviews/、当前卡、指数、周文件字节不变。
全流程前后git status --porcelain路径集合不变（含untracked）。
补充：跑步者清单的official_sha256_after与实际官方不符→强制降级（对应P1第4条）。_
延迟事项
Phase D及以后：approved review 存档进仓库的受控工具（含 seal_check 联动）、人工决策专用 CLI、LLM 叙述草稿层、通知个体、launchd 公告调度、自动审核/当前卡/索引/每周草稿、新闻政策全局核验、现有官方择优覆盖与迁移、多符号批量、review Manifest 的跨日聚合视图。_

给 Sol/high 的施工摘要
Phase C v0.1：新增tools/review_manifest.py（库）+ tools/generate_review_manifest.py（CLI）+规范文档+测试，共4个新文件，不修改任何现有正式文档。审查清单是官方事实的争论派生视图，全部写在运行时reviews/<date>/<review_id>/，仓库工作树零变化。review_id = rev_<symbol>_<date>_<official_sha256:12>，同SHA则重运行无操作，SHA改变新ID、旧的靠追加式索引派生取代，旧文件永不改写。输入只认三样：锁内重读的官方字节（自算 SHA）、schema 校验过的运行程序清单（且其 after-SHA 必须等于自算值，否则降级）、现场重跑的验证器；stdout 与自由文本一律不得作为字段来源。机器状态上限ready_for_human_review（complete + 验证器通过 + 创建/identical_noop），其余一律needs_manual_review；部分的缺失 / need_manual_check逐条进manifest与summary，summary顶部固定横幅，downstream_permissions机器恒写全假。人工批准/拒绝写独立decisions.jsonl，机器视觉，有决策 的清单保存。写入顺序总结→清单→索引追加，索引是提交标记，全部原子写；运行时不可写即失败关闭，表单回落仓库。--rebuild-from-official覆盖官方在而清单/坏的补补场景，结果强制缺needs_manual_review并标出处。v0.1无LLM、无通知、无launchd、无仓库存档。测试必须含带工作树不变断言（正式文档干燥、顶部集合保留git status）和21条方案。
