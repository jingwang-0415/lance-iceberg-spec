# Lance 接入现有 Iceberg 生态

开发功能规格、4+1 架构视图及接口参考示例。文档日期：2026-10-29。

三种协议共用 OpenSearch 主元数据存储，默认底层系统已支持文档固定版本的 Lance 协议及全部 54 个标准操作。平台侧范围包含共享模型与协议适配、Lance 字段扩展、统一权限校验、外部信息补齐和同步恢复。

## 阅读入口

| 内容 | 文件 |
|---|---|
| 完整功能规格、接口说明与 Java 估算 | [开发功能规格说明书](docs/functional-spec.md) |
| 逻辑、开发、进程、物理和场景视图 | [4+1 架构视图](docs/architecture-4plus1.md) |
| 54 组请求和响应、Arrow 示例载荷 | [接口示例目录](examples/README.md) |
| OpenSearch 新增字段建议 | [Mapping JSON](examples/opensearch-mapping-additions.json) |
| 54 个标准操作的权限点映射 | [权限映射 JSON](examples/authorization-operation-map.json) |
| 按模块统计的生产与测试 Java 行数 | [代码量估算](examples/java-loc-estimates.json) |
| 本地契约与文档检查结果 | [校验结果](examples/validation-report.json) |

## 图形与示例

4+1 文档包含 13 张 Mermaid 图，其中 9 张为执行流程或系统交互图。图形源代码保存在 Markdown 的 Mermaid 围栏代码块中，可直接编辑。

接口示例为参考请求与响应，未连接线上服务执行。Arrow 夹具已完成本地序列化与反序列化检查；如需重新生成，安装 PyArrow 后运行 `python3 examples/prepare_arrow_examples.py`。

OpenSearch Mapping 和外部权限、信息补齐接口均为设计方案，实际接入需结合现有字段及双方接口契约核对。Java 行数是平台侧开发估算，不是现有代码实测。
