<!-- DOC_META
lifecycle:  long-term
audience:   user
write_when: Dashboard 功能、操作流程变更时更新
read_when:  用户使用 Dashboard 前读取
delete_when: 不删除
-->
# 本地线索补全台使用指南

<!-- CODEx_START: dashboard_guide -->
*Updated: 2026-05-12 00:00*

## 这个工具做什么

`dashboard/index.html` 是一个轻量的人工补全台，用于按国家查看 `data/leads.csv` 和 `data/contacts.csv`，并在页面内补充缺失的公司联系、联系表单和关键人信息。

当前阶段不需要输入方向和城市。主筛选只按国家，方向、城市、客户类型等字段仍可在选中线索后人工补充。

## 正确打开方式

不要直接双击 `dashboard/index.html` 打开。浏览器从 `file://` 打开本地 HTML 时，通常不允许页面自动读取 `../data/leads.csv` 和 `../data/contacts.csv`。

从 PowerShell 运行：

```powershell
cd E:\AI\TestProject-v2
.\scripts\start_dashboard.ps1
```

脚本会启动本地服务器并打开：

```text
http://localhost:8765/dashboard/
```

这样 dashboard 可以自动加载默认 CSV。

如果 8765 端口被占用，可以换端口：

```powershell
.\scripts\start_dashboard.ps1 -Port 8770
```

## 推荐工作流

1. 在右上角填写编辑人名字。
2. 选择国家，例如 `Australia`。
3. 用缺失筛选查看 `缺公司联系或表单`、`缺关键人`、`缺关键人直联`。
4. 在左侧选择公司。
5. 在右侧补充公司字段，并编辑该公司下面的所有联系人。
6. 对常见的 `下一步`、`备注`、`补全备注`，优先使用中文预设选项。
7. 点击 `应用当前修改`。
8. 本轮人工补全结束后导出 `leads.csv` 和 `contacts.csv`，作为最新数据源。

## 联系人编辑

同一家公司如果有多个联系人，补全台会全部列出，每个联系人都可以单独修改：

- 姓名
- 职位
- 部门
- 角色类型
- email
- phone
- LinkedIn
- 来源链接
- 可信度
- 状态
- 优先级
- 备注

新增联系人会自动生成新的 `contact_id`，并关联当前公司的 `lead_id`。

## 修改记录

每次点击 `应用当前修改` 或导出时，工具会写入：

- `last_updated`：当前时间
- `change_note`：编辑人、时间和 dashboard 操作记录

这样下一次 AI 读取 CSV 时，可以直接识别哪些信息是人工更新过的，以及是谁在什么时候改的。

## 重要限制

补全台只解决人工录入和导出，不替代业务判断。它不会自动采集客户、自动 enrichment、发送邮件、登录平台或调用 AI API。

浏览器不能可靠地直接覆盖本地 CSV，所以页面内修改会先保存在当前页面内存中。完成一轮人工补全后，导出 `leads.csv` 和 `contacts.csv`，这两个导出文件就是新的 AI 可读数据源版本。

## 文档编码说明

这份中文说明应保存为 UTF-8。Windows PowerShell 如果未指定编码，可能把无 BOM 的中文 Markdown 显示成乱码；读取中文文档时优先使用：

```powershell
Get-Content -Raw -Encoding UTF8 docs\dashboard-guide.md
```

如果未来再次发现中文文档在默认终端里乱码，应先确认文件是否能用 UTF-8 正常读取，再把问题记录到对应文档和 `docs/request-solution-log.md`，作为后续修订标准。

<!-- CODEx_END: dashboard_guide -->
