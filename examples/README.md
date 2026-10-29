# Lance 接口参考示例

共 54 组，按功能规格说明书中的对象和规格编号组织。请求与响应均为参考数据，未执行线上调用。

**统一前提：默认底层系统已支持功能规格说明书固定版本的 Lance 协议及全部 54 个标准操作。示例用于平台接入，不包含底层协议服务或执行引擎开发；各例前提仅说明对象状态、参数和运行条件。Java 行数估算也仅覆盖平台侧开发。**

Table 示例按表元数据（TB-01 至 TB-11，共 11 个接口）和表数据（DATA-01 至 DATA-08，共 8 个接口）分别归档于功能规格说明书第 4、5 章。三种协议共用 OpenSearch 主元数据存储。共享模型、协议适配与新增字段见第 13 章，统一权限点见第 14 章，外部权限与信息补齐交互见第 15 章；工作量分别计入 `java-loc-estimates.json`，不增加 Lance 标准操作数量。

- `requests/`：每个接口独立的请求示例；路径相对于服务 base URI。
- `responses/`：与请求对应的参考响应。
- `opensearch-mapping-additions.json`：建议新增的 Mapping 字段；未对接现网 Mapping，需与既有字段核对后合并，不是完整建索引请求。
- `authorization-operation-map.json`：54 个标准操作的基础权限与附加校验说明；是设计对照，不是可执行策略。
- `examples.json`：54 个接口的方法、路径、参数、输入、输出及前提，便于转换为测试夹具。
- `fixtures/`：真实 Arrow IPC Stream/File 载荷、Base64 Schema 与解码后的数据说明。
- `prepare_arrow_examples.py`：本地生成 Arrow 数据的脚本，需要 PyArrow；不会连接远程服务。

`.http` 中 `< ../fixtures/...` 表示引用本地二进制文件，不是要发送的文本；使用时由 HTTP 工具读取文件内容作为请求体。JSON 请求和响应保持原始结构，空响应体与空 JSON 对象分别展示。

请求行保留 Lance 层级分隔符 `$`，例如 `/v1/table/lance_catalog$sales$orders/describe`；URL 自身的 `/`、`?`、`&`、`=` 等结构分隔符同样保持原样。参数值中的内容按所在位置及协议需要编码，例如查询参数承载的 JSON 字符串仍进行百分号编码。`examples.json` 的 `route` 是可用于请求的路径，`identifier`、`query` 和 JSON 请求体/响应体保持原始值。接入自动编码的 SDK/URI 构造器时使用原始参数，避免重复编码。若将请求示例转换为 shell 命令，须使用单引号包裹 URL，防止 shell 将 `$` 当作变量展开；单引号不属于请求内容。完整规则见[功能规格说明书 1.6.1](../docs/functional-spec.md)。

Arrow 输入表包含 id、customer_name、price、description、embedding（3 维 float32）、legacy_note。base-data.arrow 含 3 行基础数据，create-empty.arrow 仅含 Schema，insert.arrow 含 2 行新数据，merge.arrow 含 1 行更新和 1 行插入。query-result.arrow 是可解码的参考查询响应。

物化视图的 output_schema 是可解码的 Base64 Arrow Schema；source_query 是协议允许的客户端自定义序列化内容，示例假定既有执行系统可识别 example-query-v1，实际接入使用该系统已有的格式，不新增查询执行器。默认支持 Lance 协议不意味着存在标准 Job 查询路由，作业状态按执行系统既有扩展契约接入。Manifest 路径、作业与事务标识是示例值，实际调用时必须满足对应接口前提。

| 编号 | 接口 | 请求 | 参考响应 |
|---|---|---|---|
| NS-01 | CreateNamespace | [创建命名空间](requests/NS-01-CreateNamespace.http) | [响应](responses/NS-01-CreateNamespace.http) |
| NS-02 | ListNamespaces | [列举子命名空间](requests/NS-02-ListNamespaces.http) | [响应](responses/NS-02-ListNamespaces.http) |
| NS-03 | DescribeNamespace | [查询命名空间](requests/NS-03-DescribeNamespace.http) | [响应](responses/NS-03-DescribeNamespace.http) |
| NS-04 | NamespaceExists | [检查命名空间存在性](requests/NS-04-NamespaceExists.http) | [响应](responses/NS-04-NamespaceExists.http) |
| NS-05 | DropNamespace | [删除命名空间](requests/NS-05-DropNamespace.http) | [响应](responses/NS-05-DropNamespace.http) |
| TB-01 | CreateTable | [创建表](requests/TB-01-CreateTable.http) | [响应](responses/TB-01-CreateTable.http) |
| TB-02 | DeclareTable | [声明表](requests/TB-02-DeclareTable.http) | [响应](responses/TB-02-DeclareTable.http) |
| TB-03 | RegisterTable | [注册已有表](requests/TB-03-RegisterTable.http) | [响应](responses/TB-03-RegisterTable.http) |
| TB-04 | ListTables | [列举命名空间下的表](requests/TB-04-ListTables.http) | [响应](responses/TB-04-ListTables.http) |
| TB-05 | ListAllTables | [列举 Catalog 下的表](requests/TB-05-ListAllTables.http) | [响应](responses/TB-05-ListAllTables.http) |
| TB-06 | DescribeTable | [查询表详情](requests/TB-06-DescribeTable.http) | [响应](responses/TB-06-DescribeTable.http) |
| TB-07 | TableExists | [检查表或版本存在性](requests/TB-07-TableExists.http) | [响应](responses/TB-07-TableExists.http) |
| TB-08 | RenameTable | [重命名或调整所属命名空间](requests/TB-08-RenameTable.http) | [响应](responses/TB-08-RenameTable.http) |
| TB-09 | DeregisterTable | [注销表](requests/TB-09-DeregisterTable.http) | [响应](responses/TB-09-DeregisterTable.http) |
| TB-10 | DropTable | [删除表及数据](requests/TB-10-DropTable.http) | [响应](responses/TB-10-DropTable.http) |
| TB-11 | GetTableStats | [查询表统计](requests/TB-11-GetTableStats.http) | [响应](responses/TB-11-GetTableStats.http) |
| DATA-01 | InsertIntoTable | [写入数据](requests/DATA-01-InsertIntoTable.http) | [响应](responses/DATA-01-InsertIntoTable.http) |
| DATA-02 | MergeInsertIntoTable | [合并写入](requests/DATA-02-MergeInsertIntoTable.http) | [响应](responses/DATA-02-MergeInsertIntoTable.http) |
| DATA-03 | UpdateTable | [更新数据行](requests/DATA-03-UpdateTable.http) | [响应](responses/DATA-03-UpdateTable.http) |
| DATA-04 | DeleteFromTable | [删除数据行](requests/DATA-04-DeleteFromTable.http) | [响应](responses/DATA-04-DeleteFromTable.http) |
| DATA-05 | QueryTable | [查询与检索](requests/DATA-05-QueryTable.http) | [响应](responses/DATA-05-QueryTable.http) |
| DATA-06 | CountTableRows | [统计条件命中行数](requests/DATA-06-CountTableRows.http) | [响应](responses/DATA-06-CountTableRows.http) |
| DATA-07 | ExplainTableQueryPlan | [获取查询计划](requests/DATA-07-ExplainTableQueryPlan.http) | [响应](responses/DATA-07-ExplainTableQueryPlan.http) |
| DATA-08 | AnalyzeTableQueryPlan | [执行并分析查询](requests/DATA-08-AnalyzeTableQueryPlan.http) | [响应](responses/DATA-08-AnalyzeTableQueryPlan.http) |
| SC-01 | AlterTableAddColumns | [新增列](requests/SC-01-AlterTableAddColumns.http) | [响应](responses/SC-01-AlterTableAddColumns.http) |
| SC-02 | AlterTableAlterColumns | [修改列](requests/SC-02-AlterTableAlterColumns.http) | [响应](responses/SC-02-AlterTableAlterColumns.http) |
| SC-03 | AlterTableDropColumns | [删除列](requests/SC-03-AlterTableDropColumns.http) | [响应](responses/SC-03-AlterTableDropColumns.http) |
| SC-04 | UpdateFieldMetadata | [更新字段元数据](requests/SC-04-UpdateFieldMetadata.http) | [响应](responses/SC-04-UpdateFieldMetadata.http) |
| SC-05 | UpdateTableSchemaMetadata | [更新 Schema 元数据](requests/SC-05-UpdateTableSchemaMetadata.http) | [响应](responses/SC-05-UpdateTableSchemaMetadata.http) |
| SC-06 | AlterTableBackfillColumns | [回填列](requests/SC-06-AlterTableBackfillColumns.http) | [响应](responses/SC-06-AlterTableBackfillColumns.http) |
| IDX-01 | CreateTableIndex | [创建索引](requests/IDX-01-CreateTableIndex.http) | [响应](responses/IDX-01-CreateTableIndex.http) |
| IDX-02 | CreateTableScalarIndex | [创建标量索引](requests/IDX-02-CreateTableScalarIndex.http) | [响应](responses/IDX-02-CreateTableScalarIndex.http) |
| IDX-03 | ListTableIndices | [列举索引](requests/IDX-03-ListTableIndices.http) | [响应](responses/IDX-03-ListTableIndices.http) |
| IDX-04 | DescribeTableIndexStats | [查询索引统计](requests/IDX-04-DescribeTableIndexStats.http) | [响应](responses/IDX-04-DescribeTableIndexStats.http) |
| IDX-05 | DropTableIndex | [删除索引](requests/IDX-05-DropTableIndex.http) | [响应](responses/IDX-05-DropTableIndex.http) |
| VER-01 | ListTableVersions | [列举表版本](requests/VER-01-ListTableVersions.http) | [响应](responses/VER-01-ListTableVersions.http) |
| VER-02 | DescribeTableVersion | [查询版本详情](requests/VER-02-DescribeTableVersion.http) | [响应](responses/VER-02-DescribeTableVersion.http) |
| VER-03 | CreateTableVersion | [登记版本提交](requests/VER-03-CreateTableVersion.http) | [响应](responses/VER-03-CreateTableVersion.http) |
| VER-04 | BatchCreateTableVersions | [批量登记版本](requests/VER-04-BatchCreateTableVersions.http) | [响应](responses/VER-04-BatchCreateTableVersions.http) |
| VER-05 | BatchDeleteTableVersions | [删除版本记录](requests/VER-05-BatchDeleteTableVersions.http) | [响应](responses/VER-05-BatchDeleteTableVersions.http) |
| VER-06 | RestoreTable | [恢复表版本](requests/VER-06-RestoreTable.http) | [响应](responses/VER-06-RestoreTable.http) |
| REF-01 | ListTableTags | [列举标签](requests/REF-01-ListTableTags.http) | [响应](responses/REF-01-ListTableTags.http) |
| REF-02 | GetTableTagVersion | [解析标签](requests/REF-02-GetTableTagVersion.http) | [响应](responses/REF-02-GetTableTagVersion.http) |
| REF-03 | CreateTableTag | [创建标签](requests/REF-03-CreateTableTag.http) | [响应](responses/REF-03-CreateTableTag.http) |
| REF-04 | UpdateTableTag | [修改标签指向](requests/REF-04-UpdateTableTag.http) | [响应](responses/REF-04-UpdateTableTag.http) |
| REF-05 | DeleteTableTag | [删除标签](requests/REF-05-DeleteTableTag.http) | [响应](responses/REF-05-DeleteTableTag.http) |
| REF-06 | ListTableBranches | [列举分支](requests/REF-06-ListTableBranches.http) | [响应](responses/REF-06-ListTableBranches.http) |
| REF-07 | CreateTableBranch | [创建分支](requests/REF-07-CreateTableBranch.http) | [响应](responses/REF-07-CreateTableBranch.http) |
| REF-08 | DeleteTableBranch | [删除分支](requests/REF-08-DeleteTableBranch.http) | [响应](responses/REF-08-DeleteTableBranch.http) |
| MV-01 | CreateMaterializedView | [创建物化视图](requests/MV-01-CreateMaterializedView.http) | [响应](responses/MV-01-CreateMaterializedView.http) |
| MV-02 | RefreshMaterializedView | [刷新物化视图](requests/MV-02-RefreshMaterializedView.http) | [响应](responses/MV-02-RefreshMaterializedView.http) |
| TX-01 | BatchCommitTables | [原子提交多表元数据操作](requests/TX-01-BatchCommitTables.http) | [响应](responses/TX-01-BatchCommitTables.http) |
| TX-02 | DescribeTransaction | [查询事务状态](requests/TX-02-DescribeTransaction.http) | [响应](responses/TX-02-DescribeTransaction.http) |
| TX-03 | AlterTransaction | [修改事务状态或属性](requests/TX-03-AlterTransaction.http) | [响应](responses/TX-03-AlterTransaction.http) |
