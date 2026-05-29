<!-- DOC_META
lifecycle:  long-term
audience:   user
write_when: 新增中文文档或用户指南变更时更新
read_when:  中文用户需要查找文档时读取
delete_when: 不删除
-->
# 中文文档索引

<!-- CODEx_START: chinese_doc_index -->
*Updated: 2026-05-12 12:10*

这份文件只作为中文索引，避免把客户收集、联系方式 enrichment、字段规则、看板使用和备份规则混在一起。

请按任务类型读取对应文档：

- 项目背景、长期目标、当前 Australia 阶段目标：`docs/architecture/project-overview.md`
- 客户发现和线索收集规则：`docs/workflows/lead-collection-workflow.md`
- 联系方式和关键人 KP enrichment 规则：`docs/workflows/lead-enrichment-workflow.md`
- `leads.csv`、`contacts.csv` 字段和状态规则：`docs/architecture/lead-table-fields.md`
- 本地只读看板说明：`docs/guides/dashboard-guide.md`
- 备份、时间戳和安全更新规则：`docs/guides/iteration-setup.md`
- Codex 任务读取规则和优先级规则：`docs/guides/cli-operating-rules.md`
- 重要需求和 CLI/Codex 处理方案记录：`docs/request-solution-log.md`
- 当前进度、下一步和恢复命令：`docs/current-progress.md`

## 当前核心方向

- 当前市场先聚焦 Australia。
- 当前第一阶段客户优先 restaurant / hotel final customers。
- 当前联系目标优先关键人 KP。
- 最强联系路径是 key person email，最好再有 phone。
- 公司邮箱、公司电话和 contact form 是次级联系路径。
- fit-out、design、procurement、FF&E、OS&E、commercial kitchen 公司仍然有价值，但当前 AU 阶段先作为次级方向，除非任务明确要求。

## 重要原则

- 发现公司不等于完成 enrichment。
- `Ready to Contact` 是宽状态，不等于最高优先级外联。
- `Direct Key Contact Found` 的 Australia restaurant / hotel final customer 应优先 review。
- 看板只是只读辅助工具，不是主流程。
- 历史 reports 只记录当时结果，不覆盖当前 active docs。
- 重要项目需求、流程调整、工具策略和备份策略变化应简短记录到 `docs/request-solution-log.md`。
- Codex 可以自动记录发现的问题，并在已经批准的任务范围内自动迭代修复、测试、优化脚本、重生成报告和补充文档。
- Codex 不能在未获明确授权时自动扩大业务范围、开启新的 collection/enrichment 业务迭代、改变质量标准、使用新的高风险访问模式，或做大范围源数据改动。
- 如果任务会改变目标客户、质量标准、外联标准或账号风险，必须先问清楚。

<!-- CODEx_END: chinese_doc_index -->

