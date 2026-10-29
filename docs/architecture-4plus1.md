# Lance 接入现有 Iceberg 生态：4+1 架构视图

> 文档日期：2026-10-29。本文对应[开发功能规格说明书](functional-spec.md)第 17 章，可直接复制各 Mermaid 代码块使用。

<a id="architecture-views"></a>

## 17. 4+1 架构视图与关键流程

本章将前述功能规格整理为逻辑、开发、进程、物理和场景五个视角，流程以第 12—15 章的存储、权限和外部交互规则为准。三种协议共用 OpenSearch 主元数据存储；底层已支持固定 Lance 协议；权限策略和安全属性由外部权威系统提供。

所有图使用 Markdown 的 `mermaid` 围栏代码块，节点、连线和判断条件均可直接编辑。支持 Mermaid 的 Markdown 阅读器可渲染图形；其他阅读器保留图形源代码。可复制的独立文件见 [4+1 架构视图 Markdown](architecture-4plus1.md)。实线表示调用、依赖或流程推进，标注“异步”的连线表示后台处理，不表示必须引入消息中间件。

| 视图 | 回答的问题 | 本章内容 |
|---|---|---|
| [逻辑视图](#view-logical) | 系统有哪些职责与核心对象 | 共享业务服务、元数据对象与外部系统边界 |
| [开发视图](#view-development) | Java 模块如何组织、依赖如何约束 | 协议入口、应用服务、领域模型、接口与实现 |
| [进程视图](#view-process) | 一次操作如何执行、失败后如何处理 | 请求、鉴权、创建、变更、补齐、恢复、批量提交、异步作业与删除 |
| [物理视图](#view-physical) | 服务和存储部署在哪里 | 无状态服务实例、后台任务、OpenSearch 与外部依赖 |
| [场景视图](#view-scenarios) | 上述设计如何支撑真实业务 | 典型使用场景与功能、流程、验收用例对应关系 |

<a id="view-logical"></a>

### 17.1 逻辑视图：职责与共享元数据

三种协议只形成不同的请求与响应视图，业务服务操作相同的对象。Table 元数据与 Table 数据分别管理；Schema、Index、Version、Tag / Branch 等通过稳定表身份关联。下图中的元数据对象均落在同一套主存储体系中，不表示各自独立建库。

```mermaid
flowchart TB
    subgraph protocols["协议入口"]
        lanceEntry["Lance"]
        icebergEntry["Iceberg"]
        gravitinoEntry["Gravitino"]
    end
    protocolAdapter["协议请求与响应适配"]
    identityResolver["名称解析与稳定资源身份"]
    authorizationGate["统一权限校验"]
    subgraph services["统一业务服务"]
        metadataService["元数据管理与生命周期"]
        dataService["Table 数据读写与查询"]
        operationService["操作状态、同步与恢复"]
    end
    subgraph metadata["共享元数据对象"]
        hierarchy["Catalog / Namespace / Table 元数据"]
        tableDetails["Schema / Column / Index / Version"]
        references["Tag / Branch / Materialized View"]
        operationRecords["Transaction / Operation / Checkpoint / Tombstone"]
    end
    mainStore[("OpenSearch 主元数据存储")]
    executionService["已有 Lance 与执行系统"]
    permissionService["外部权限系统：策略与决策"]
    informationService["外部业务系统：展示与安全属性"]
    enrichmentAdapter["展示信息补齐适配"]
    lanceEntry --> protocolAdapter
    icebergEntry --> protocolAdapter
    gravitinoEntry --> protocolAdapter
    protocolAdapter --> identityResolver --> authorizationGate
    authorizationGate --> metadataService
    authorizationGate --> dataService
    authorizationGate --> permissionService
    permissionService -->|"按需取得权威安全属性"| informationService
    metadataService --> hierarchy
    metadataService --> tableDetails
    metadataService --> references
    operationService --> operationRecords
    hierarchy --> mainStore
    tableDetails --> mainStore
    references --> mainStore
    operationRecords --> mainStore
    metadataService -->|"真实 Schema、索引与版本操作"| executionService
    dataService --> executionService
    metadataService --> operationService
    dataService --> operationService
    operationService -.->|"异步补齐"| enrichmentAdapter
    enrichmentAdapter -->|"批量补齐展示字段"| informationService
    enrichmentAdapter -->|"条件更新指定字段"| mainStore
```

权限系统使用稳定 resourceId，业务补齐系统使用同一引用或显式绑定的 externalObjectId。展示字段只影响展示与检索；安全属性通过权限系统参与决策。Lance 的物理事实与平台身份分别有明确来源，不能仅写 OpenSearch 就认为底层数据操作已成功。

<a id="view-development"></a>

### 17.2 开发视图：Java 模块与依赖方向

以下为建议的包或模块边界，可映射到现有工程，无须为每个框框创建独立进程。箭头表示代码依赖；应用服务通过接口调用基础设施，协议入口不直接操作 OpenSearch 或调用外部权限客户端。

```mermaid
flowchart TB
    subgraph entryModules["协议入口模块"]
        lanceApi["lance-api"]
        icebergApi["iceberg-api"]
        gravitinoApi["gravitino-api"]
    end
    protocolMapping["protocol-mapping：参数、类型、状态与响应适配"]
    application["metadata-application：业务用例编排与权限执行点"]
    domain["metadata-domain：公共身份、对象模型与变更规则"]
    authorizationCore["authorization-core：权限点、检查项、决策约束"]
    integrationPorts["integration-ports：存储、执行、鉴权、补齐接口"]
    workers["metadata-workers：对账、资源同步、作业状态跟踪"]
    subgraph implementations["基础设施实现模块"]
        searchRepository["opensearch-repository：Mapping、条件写与实时读取"]
        lanceClient["lance-client：已有标准接口与数据流接入"]
        permissionClient["permission-client：批量决策与资源绑定"]
        enrichmentClient["enrichment-client：业务属性与变化通知"]
    end
    lanceApi --> protocolMapping
    icebergApi --> protocolMapping
    gravitinoApi --> protocolMapping
    protocolMapping --> application
    protocolMapping --> domain
    application --> domain
    application --> authorizationCore
    application --> integrationPorts
    authorizationCore --> integrationPorts
    workers --> application
    workers --> integrationPorts
    integrationPorts --> domain
    searchRepository -.->|"实现接口"| integrationPorts
    lanceClient -.->|"实现接口"| integrationPorts
    permissionClient -.->|"实现接口"| integrationPorts
    enrichmentClient -.->|"实现接口"| integrationPorts
```

协议 DTO 的缺失字段不能转成全量文档覆盖。公共转换、权限执行和恢复框架各实现一次；后台任务复用业务规则，使用明确的服务身份或用户委托。模块拆分不新增功能范围，Java 估算仍对应第 1.5 节及各对象章节。

<a id="view-process"></a>

### 17.3 进程视图：关键执行流程

流程中的“条件写”指携带当前文档并发版本的 OpenSearch 更新；冲突后重新读取和判断，不能取消条件强行覆盖。“待核实”与“失败”不同：结果未知时保留占用和操作状态，通过已有查询能力确认结果后再推进。

<a id="flow-request"></a>

#### 17.3.1 统一请求与读取流程

该流程覆盖三种协议的共同入口。列表先检查父级列表权限，再批量检查候选对象；数据查询及统计按数据读取权限执行。展示信息只在业务响应允许的字段中输出。

```mermaid
flowchart TD
    incoming["收到 Lance / Iceberg / Gravitino 请求"] --> authenticate{"身份认证通过？"}
    authenticate -->|"否"| unauthenticated["按入口协议返回未认证错误"]
    authenticate -->|"是"| normalize["解析协议参数为统一业务命令"]
    normalize --> validate{"参数与协议语义合法？"}
    validate -->|"否"| invalidRequest["返回参数或语义不兼容错误"]
    validate -->|"是"| resolve["解析稳定资源 ID、父级和代次"]
    resolve --> readCurrent["实时读取资源及协调状态<br/>只取得内部定位所需事实"]
    readCurrent --> permissionCheck["执行统一权限流程<br/>见 17.3.2"]
    permissionCheck --> allowed{"全部必要检查允许<br/>且约束可执行？"}
    allowed -->|"否"| denied["返回拒绝或依赖不可用<br/>不输出受保护内容"]
    allowed -->|"是"| requestKind{"操作类型？"}
    requestKind -->|"元数据读取"| metadataRead["读取同一份主元数据<br/>列表按授权范围分页"]
    requestKind -->|"数据查询或统计"| dataRead["将权限过滤和字段限制<br/>下发已有执行系统"]
    requestKind -->|"变更操作"| mutation["进入对应创建或变更流程<br/>见 17.3.3、17.3.4"]
    metadataRead --> verifyRead["复核资源代次、协调状态和读取修订"]
    dataRead --> verifyRead
    verifyRead --> stable{"读取条件仍一致？"}
    stable -->|"否"| boundedRetry["有界重读并重新鉴权<br/>持续冲突则返回冲突"]
    boundedRetry -.->|"允许重试时"| resolve
    stable -->|"是"| optionalDisplay["按响应需要附加已授权展示信息<br/>过期信息异步补齐"]
    optionalDisplay --> serialize["按入口协议序列化结果<br/>平台扩展状态只进入允许的响应"]
    serialize --> response["返回结果并关联审计记录"]
```

列表候选来自 Search，但结果输出前仍核对当前资源状态。批量鉴权和游标遵守第 14.4 节：继续扫描候选以填充授权页，不返回未授权对象数量。

<a id="flow-authorization"></a>

#### 17.3.2 权限系统与安全属性系统交互

一次业务操作展开为全部检查项后统一调用 batchCheck。权限系统取得安全属性并作出决策，平台执行约束；业务系统的展示字段不进入这条放行链路。

```mermaid
sequenceDiagram
    participant application as 统一业务服务
    participant store as OpenSearch
    participant guard as 权限执行器
    participant permission as 外部权限系统
    participant attributes as 安全属性权威系统
    application->>store: 实时读取资源、父级、代次及资源修订
    store-->>application: 当前可信资源事实
    application->>guard: 主体、全部业务动作、资源与作用域
    guard->>guard: 校验权限点目录并展开复合动作
    guard->>permission: batchCheck，携带可信资源上下文
    permission->>permission: 核对资源事实版本和策略
    opt 策略需要外部安全属性
        permission->>attributes: batchGet，指定所需属性和版本要求
        attributes-->>permission: 当前属性及版本，或无法确认
    end
    alt 资源版本或必要属性无法确认
        permission-->>guard: INDETERMINATE
        guard-->>application: 阻止操作，返回依赖不可用
    else 策略明确拒绝任一必要检查
        permission-->>guard: DENY 与 decisionId
        guard-->>application: 阻止操作，返回权限拒绝
    else 全部必要检查允许
        permission-->>guard: ALLOW、版本及结构化约束
        guard->>guard: 验证响应完整、检查项匹配、约束可执行
        alt 响应缺项或约束无法执行
            guard-->>application: 阻止操作，返回明确错误
        else 响应有效
            guard-->>application: 决策上下文与可执行约束
            application->>store: 执行前复核资源代次、修订及占用
            store-->>application: 一致或已变化
            application->>application: 一致则继续；变化则重新解析和鉴权
        end
    end
```

安全属性系统与权限系统可以部署在同一产品内，职责仍分开。权限系统无需回调同一个受保护业务接口；超时、缺项和未知版本均不允许回退到 OpenSearch 中的展示值。

<a id="flow-create"></a>

#### 17.3.3 创建或注册对象与权限资源绑定

适用于 Namespace、Table、物化视图等需要新建平台身份的操作。各对象的底层调用及模式以对应规格为准；存在同名对象时，先按 Create / ExistOk / Overwrite 的语义和附加权限处理。

```mermaid
flowchart TD
    createRequest["完成参数、父级权限及创建模式校验"] --> persistIntent["持久化 Operation<br/>绑定幂等键和输入摘要"]
    persistIntent --> claimName["原子占用规范化名称<br/>登记父级中的在途子操作"]
    claimName --> claimed{"占用成功且父级可创建？"}
    claimed -->|"否"| nameConflict["读取已有占用<br/>按模式处理或返回冲突"]
    claimed -->|"是"| createRecord["创建稳定 ID 的 PROVISIONING 文档<br/>同文档保存权限待绑定与待同步版本"]
    createRecord --> durable{"操作与占用均已确认持久化？"}
    durable -->|"否"| stopBeforeEffect["保持待恢复状态<br/>不调用产生副作用的接口"]
    durable -->|"是"| executeCreate["调用已有底层创建或注册接口"]
    executeCreate --> executionResult{"底层结果？"}
    executionResult -->|"明确失败"| failCreate["记录失败并按已核实状态清理占用<br/>处理已产生的外部资源"]
    executionResult -->|"未知"| verifyCreate["保留待核实状态<br/>查询底层结果，避免重复创建"]
    verifyCreate -.->|"结果确认后继续"| executionResult
    executionResult -->|"成功"| saveFacts["保存已确认事实和待同步版本"]
    saveFacts --> bindResource["向权限系统幂等注册 resourceId<br/>同步父级及资源修订"]
    bindResource --> bindingReady{"当前所需版本已确认？"}
    bindingReady -->|"否"| pendingBinding["保持不可用和待同步<br/>进入 17.3.6 恢复流程"]
    bindingReady -->|"是"| publish["条件更新权限绑定状态与资源可用状态<br/>完成名称登记及 Operation"]
    publish --> publishResult{"本次发布成功？"}
    publishResult -->|"冲突或回写未知"| recoverPublish["重读并恢复本次操作<br/>不重做已成功的底层创建"]
    publishResult -->|"是"| creationDone["返回协议定义的完成结果<br/>异步作业仍单独跟踪"]
```

权限资源存在不代表创建者自动获得全部权限。外部绑定确认之前，普通业务查询不可见；创建者通过经授权的 Operation 查询进度，标准接口不把待绑定状态伪装成完成。

<a id="flow-change"></a>

#### 17.3.4 元数据变更、Schema 变更与跨 Namespace 移动

同一个流程区分平台自身字段更新和需要调用底层的真实变更。跨 Namespace 移动须检查源、目标和继承关系；外部权威安全属性修改走其维护方，不通过普通 properties 更新。

```mermaid
flowchart TD
    changeRequest["将协议 DTO 转为显式字段变更命令"] --> fieldOwnership{"字段归属与操作语义允许？"}
    fieldOwnership -->|"否"| rejectChange["拒绝越界字段或不兼容操作"]
    fieldOwnership -->|"是"| authorizeChange["校验全部动作、源对象及目标父级权限"]
    authorizeChange --> changeAllowed{"全部权限检查通过？"}
    changeAllowed -->|"否"| deniedChange["返回拒绝或依赖不可用<br/>不执行变更"]
    changeAllowed -->|"是"| reserveChange["持久化 Operation 并取得必要占用<br/>关键关系变更先挂起相关访问"]
    reserveChange --> recheck["复核版本、依赖及受影响对象集合"]
    recheck --> needExecution{"需要真实底层操作？"}
    needExecution -->|"否"| mergeChange["按字段归属合并变更<br/>保留未涉及的 Lance 和外部字段"]
    needExecution -->|"是"| invokeExecution["调用已有 Schema、Rename 等接口"]
    invokeExecution --> backendResult{"底层结果？"}
    backendResult -->|"失败"| failedChange["记录失败<br/>按确认事实恢复占用和可见状态"]
    backendResult -->|"未知"| unknownChange["进入结果核实<br/>保留协调状态，禁止盲目重放"]
    unknownChange -.->|"已核实"| backendResult
    backendResult -->|"成功"| actualMetadata["读取真实 Schema 或当前底层事实"]
    actualMetadata --> mergeChange
    mergeChange --> conditionalWrite["条件写主元数据<br/>权限相关事实变化同时写待同步版本"]
    conditionalWrite --> writeResult{"条件写成功？"}
    writeResult -->|"否"| refreshChange["重读并重新合并已确认结果<br/>需要时重新鉴权"]
    refreshChange -.-> mergeChange
    writeResult -->|"是"| bindingNeeded{"本次可用性依赖外部绑定确认？"}
    bindingNeeded -->|"是"| syncBinding["同步新事实并等待当前版本确认<br/>失败转 17.3.6"]
    syncBinding --> bindingConfirmed{"已确认？"}
    bindingConfirmed -->|"否"| remainSuspended["保持协调中并允许查询进度"]
    bindingConfirmed -->|"是"| completeChange["完成名称或父级切换<br/>发布可用状态并完成 Operation"]
    bindingNeeded -->|"否"| completeChange
```

同对象的不同字段更新仍受并发控制保护。对已成功的底层变更，恢复目标是补齐主元数据；对尚未执行的变更，资源修订变化后必须重新鉴权。不能重新调用底层操作来“修复”一次 OpenSearch 写入失败。

<a id="flow-enrichment"></a>

#### 17.3.5 展示信息补齐与降级

展示请求已获得相应业务权限后，可以使用已有补齐结果。后台补齐只更新白名单字段；权限所需的安全属性不走该降级流程。

```mermaid
flowchart TD
    displayNeeded["已授权响应需要展示信息<br/>或后台收到刷新任务"] --> readEnrichment["读取来源绑定、现有值、版本及新鲜度"]
    readEnrichment --> displayFresh{"展示信息仍有效？"}
    displayFresh -->|"是"| useDisplay["使用现有展示字段"]
    displayFresh -->|"否"| staleDisplay["请求可先返回基础信息和已有展示值<br/>平台响应标记 STALE 或 PARTIAL"]
    staleDisplay -->|"异步"| batchFetch["按来源合并资源列表<br/>调用 enrichment:batchGet"]
    batchFetch --> fetchStatus{"逐项返回状态？"}
    fetchStatus -->|"FOUND"| verifyFields["校验来源、绑定、代次及字段白名单<br/>核对版本与 removedFields"]
    fetchStatus -->|"NOT_MODIFIED"| verifyFreshness["核对本地仍是本次请求的已知版本"]
    fetchStatus -->|"NOT_FOUND"| noMatch["标记未匹配并保留平台资源<br/>不据此删除主元数据"]
    fetchStatus -->|"UNAVAILABLE 或超时"| retryDisplay["保留旧值，记录补齐失败<br/>有界退避重试"]
    verifyFields --> applicable{"对象仍有效且结果可应用？"}
    applicable -->|"否"| ignoreEnrichment["忽略过期或越界结果<br/>必要时重新拉取当前值"]
    applicable -->|"是"| patchEnrichment["条件更新该来源的展示字段<br/>同时保存来源版本和获取时间"]
    verifyFreshness -->|"版本一致"| patchFreshness["条件更新获取时间与补齐状态"]
    verifyFreshness -->|"版本已变化"| ignoreEnrichment
    patchEnrichment --> enrichmentWrite{"条件写成功？"}
    patchFreshness --> enrichmentWrite
    enrichmentWrite -->|"是"| displayReady["下一次授权读取可使用新展示值"]
    enrichmentWrite -->|"否"| rereadEnrichment["重读对象与来源版本<br/>重新判断，避免旧结果覆盖新值"]
    rereadEnrichment -.-> batchFetch
```

外部 ownerName 是展示名，不能借补齐修改 ownerId 或组织授权关系。每个来源保存独立版本；不可比较的来源修订号通过重新取当前值判断，不能按字符串大小排序。

<a id="flow-recovery"></a>

#### 17.3.6 权限资源同步与故障恢复

正常提交、外部变化通知、周期扫描和进程重启都可以触发同一恢复流程。待同步标记与资源事实在同一文档中保存，扫描只负责发现任务，处理资格仍通过实时读取及条件写取得。

```mermaid
flowchart TD
    recoveryTrigger["操作完成通知、周期扫描或重启恢复"] --> findPending["发现 resourceSyncRequired 的候选对象"]
    findPending --> loadPending["实时读取资源、代次、当前意图和待同步版本"]
    loadPending --> claimWork{"需要处理且取得执行资格？"}
    claimWork -->|"否"| skipWork["结束本轮或等待其他执行者完成"]
    claimWork -->|"是"| deletionState{"已有明确退休意图？"}
    deletionState -->|"否"| upsertFacts["发送当前资源快照 upsert<br/>幂等键包含资源、代次及版本"]
    deletionState -->|"是"| retireFacts["发送 retire<br/>携带删除代次及资源修订"]
    upsertFacts --> externalAck{"外部确认结果？"}
    retireFacts --> externalAck
    externalAck -->|"超时或不可用"| persistRetry["保留待同步状态<br/>保存错误和下次重试时间"]
    externalAck -->|"契约冲突"| repairRequired["保留受控状态并报告原因<br/>修复输入或绑定后重试"]
    externalAck -->|"确认成功"| rereadPending["重新读取本地最新 desiredRevision 与代次"]
    rereadPending --> sameGeneration{"仍是同一对象代次？"}
    sameGeneration -->|"否"| discardOldAck["忽略旧确认，不影响重建对象"]
    sameGeneration -->|"是"| currentAck{"确认对应当前所需版本？"}
    currentAck -->|"否"| keepPending["保留待同步标记<br/>重新核对或发送最新版本"]
    currentAck -->|"是"| confirmWrite["条件写 acknowledgedRevision<br/>清除本次待同步标记"]
    confirmWrite --> ackWritten{"回写已确认成功？"}
    ackWritten -->|"否"| retryConfirmation["保留恢复任务<br/>重读，必要时幂等重发"]
    ackWritten -->|"是"| publishIfReady["核对底层结果与全部发布条件<br/>激活资源或完成退休"]
    persistRetry -.->|"到期后"| recoveryTrigger
    keepPending -.-> loadPending
    retryConfirmation -.-> loadPending
```

外部成功而平台回写失败只会引起幂等重发，不能生成第二个权限资源。确认回写本身不增加资源事实修订，避免无限同步；较旧确认不能清除更新版本的任务。

<a id="flow-batch"></a>

#### 17.3.7 多表原子提交与主元数据发布

底层原子性由已有 BatchCommitTables 等接口提供。平台负责全量鉴权、参与资源占用和 OpenSearch 主元数据恢复；Bulk 逐项写入完成之前，不发布一个伪完整的业务结果。

```mermaid
flowchart TD
    batchRequest["解析批次并固定所有目标和输入摘要"] --> authorizeBatch["展开每项实际动作并批量鉴权<br/>检查名称、版本、依赖与提交条件"]
    authorizeBatch --> allAuthorized{"全部必要检查通过？"}
    allAuthorized -->|"否"| rejectBatch["整批拒绝，未调用底层提交"]
    allAuthorized -->|"是"| prepareBatch["持久化 Operation<br/>按固定顺序占用全部参与资源"]
    prepareBatch --> prepared{"全部占用且版本复核一致？"}
    prepared -->|"否"| stopBatch["解除可安全释放的占用<br/>重新校验或返回冲突"]
    prepared -->|"是"| atomicCommit["调用已有底层原子批量接口"]
    atomicCommit --> commitResult{"提交结果？"}
    commitResult -->|"明确失败"| batchFailed["记录整批失败<br/>按确认状态恢复占用"]
    commitResult -->|"未知"| verifyBatch["查询底层事务及版本结果<br/>保留全部协调状态"]
    verifyBatch -.->|"已确认"| commitResult
    commitResult -->|"成功"| persistBatch["逐项条件更新已确认的主元数据<br/>必要时完成新资源的权限绑定"]
    persistBatch --> batchMetadataReady{"全部主元数据和绑定已就绪？"}
    batchMetadataReady -->|"否"| resumeBatch["保持协调中并恢复缺失步骤<br/>不重提已成功的批次"]
    resumeBatch -.-> persistBatch
    batchMetadataReady -->|"是"| publishBatch["条件发布 Operation 完成状态"]
    publishBatch --> exposeBatch["解除业务可见性限制<br/>按输入顺序返回各项结果"]
```

参与对象的读取均检查关联 Operation；需要一致的多对象结果时还须复核整个读取集合。协调中可等待或返回明确的暂不可用状态，不能返回部分新值混合部分旧值。

<a id="flow-jobs"></a>

#### 17.3.8 回填、索引构建与物化视图刷新

平台接入已有执行能力并跟踪结果。job_id、transaction_id 和平台 operationId 分别保存；自动刷新仍由已有系统调度，调度时须执行相同的委托和权限检查。

```mermaid
flowchart TD
    jobRequest["用户提交或已有系统触发自动任务"] --> resolveJob["确认源对象、目标对象及请求摘要<br/>解析可信依赖关系"]
    resolveJob --> authorizeJob["检查作业动作、源读取和输出写入权限<br/>确认用户委托或系统任务身份"]
    authorizeJob --> jobReady{"授权和执行约束均可满足？"}
    jobReady -->|"否"| rejectJob["拒绝派发，记录原因"]
    jobReady -->|"是"| persistJob["持久化 Operation 与委托上下文"]
    persistJob --> beforeDispatch["实际派发前复核资源版本和授权"]
    beforeDispatch --> dispatchReady{"仍可执行？"}
    dispatchReady -->|"否"| rejectJob
    dispatchReady -->|"是"| submitJob["调用已有执行接口"]
    submitJob --> accepted{"提交结果？"}
    accepted -->|"失败"| recordFailure["记录失败，保留已确认结果"]
    accepted -->|"未知"| verifySubmission["按执行系统契约核实受理结果<br/>无法确认时不重复派发"]
    accepted -->|"已受理"| bindJob["分别关联 job_id 或 transaction_id<br/>返回协议定义的受理结果"]
    verifySubmission -.->|"确认后"| accepted
    bindJob --> trackJob["通过既有查询契约或事件跟踪状态"]
    trackJob --> jobState{"实际执行状态？"}
    jobState -->|"运行中"| delegationCheck["在支持的检查点核对委托与权限<br/>失效时停止后续可控执行"]
    delegationCheck -.-> trackJob
    jobState -->|"失败或取消"| recordFailure
    jobState -->|"成功"| verifyOutput["核实真实输出版本、Schema 或索引状态"]
    verifyOutput --> persistOutput["条件更新主元数据与最终结果"]
    persistOutput --> outputRecorded{"元数据回写已确认成功？"}
    outputRecorded -->|"否"| retryOutput["保留结果待同步状态<br/>仅恢复元数据，不重做已完成作业"]
    retryOutput -.-> persistOutput
    outputRecorded -->|"是"| readJob["查询作业或读取结果时重新鉴权"]
```

已受理不等于已成功。撤权不被描述为能回滚所有在途底层操作；执行系统无法满足所需委托检查或行列约束时，不启用相应运行配置。

<a id="flow-delete"></a>

#### 17.3.9 注销、物理删除与外部资源退休

注销和物理删除使用不同权限点。Cascade 先确定并保护受影响对象集合，逐项检查权限；删除期间阻止新的子对象创建和受保护业务访问。

```mermaid
flowchart TD
    deleteRequest["解析注销、物理删除或 Cascade 范围"] --> deletionChecks["检查依赖、引用及全部实际动作权限"]
    deletionChecks --> deletionAllowed{"检查通过且范围未变化？"}
    deletionAllowed -->|"否"| rejectDeletion["拒绝操作并返回可公开原因"]
    deletionAllowed -->|"是"| blockAccess["持久化删除意图和 Operation<br/>条件更新为删除协调中"]
    blockAccess --> deleteKind{"实际删除语义？"}
    deleteKind -->|"注销注册"| deregister["调用已有注销接口，保留物理数据"]
    deleteKind -->|"删除表及数据"| purge["调用已有物理删除接口"]
    deregister --> deletionResult{"底层结果？"}
    purge --> deletionResult
    deletionResult -->|"未知"| verifyDeletion["保留受控状态并核实结果"]
    verifyDeletion -.->|"已确认"| deletionResult
    deletionResult -->|"明确失败"| deletionFailed["记录失败；按真实副作用决定恢复或继续协调"]
    deletionResult -->|"成功"| writeTombstone["持久化 Tombstone、删除代次<br/>以及外部退休待同步版本"]
    writeTombstone --> retireResource["按 17.3.6 幂等退休权限资源"]
    retireResource --> retired{"当前代次的退休已确认？"}
    retired -->|"否"| retainTombstone["保留 Tombstone 和重试状态"]
    retired -->|"是"| finishDeletion["完成平台生命周期协调<br/>按规则释放名称并保留删除防护记录"]
    finishDeletion --> retentionWindow["事件与重试有效窗口过去后<br/>清理允许回收的历史记录"]
```

同名重建使用新 ID 或代次。旧补齐响应、旧授权确认和旧删除任务均不能修改新对象；清理前不能删除唯一待同步记录。

<a id="view-physical"></a>

### 17.4 物理视图：部署与故障边界

下图表示逻辑部署关系，实例数量、分片和容量沿用实际环境配置。接口服务与后台任务可共部署，也可分别扩容；持久状态都保存在共享主存储，不依赖单个 JVM 的内存锁或任务队列保证一致性。

```mermaid
flowchart TB
    client["协议客户端与平台调用方"] --> routing["现有接入层与请求路由"]
    subgraph platform["平台部署范围"]
        apiInstances["业务服务实例<br/>三种协议适配与统一权限执行"]
        workerInstances["后台任务实例<br/>恢复、对账、补齐和状态跟踪"]
        serviceConfiguration["现有配置与凭证引用"]
    end
    routing --> apiInstances
    apiInstances --> serviceConfiguration
    workerInstances --> serviceConfiguration
    mainStorage[("OpenSearch 集群<br/>主元数据、Operation、名称占用<br/>Tombstone、待同步状态")]
    existingLance["已有 Lance 服务与执行系统"]
    objectStorage[("已有数据与 Manifest 存储")]
    authorizationSystem["外部权限系统"]
    businessSystem["外部业务与安全属性系统"]
    apiInstances -->|"实时读取与条件写"| mainStorage
    workerInstances -->|"发现任务、取得执行资格与回写"| mainStorage
    apiInstances -->|"标准操作与数据流"| existingLance
    workerInstances -->|"查询已执行结果与状态"| existingLance
    existingLance --> objectStorage
    apiInstances -->|"同步鉴权及必要的资源绑定"| authorizationSystem
    workerInstances -->|"资源绑定与退休"| authorizationSystem
    workerInstances -->|"批量补齐与变化拉取"| businessSystem
    authorizationSystem -->|"权威安全属性"| businessSystem
    businessSystem -.->|"变化通知，可与周期拉取并用"| workerInstances
```

| 故障边界 | 对业务的影响与恢复方式 |
|---|---|
| 业务实例退出 | 其他实例依据持久 Operation 恢复；不能靠进程内状态推定底层失败 |
| 后台实例退出或重复执行 | 条件占用、幂等外部接口及版本确认避免重复副作用 |
| OpenSearch 不可用 | 无法确认资源和写入意图时阻止新副作用；已执行操作恢复后核实并补齐主元数据 |
| 权限或安全属性系统不可用 | 受保护访问不能放行；已有执行中的任务按委托及执行系统契约处理 |
| 展示补齐系统不可用 | 权限已通过的请求可以返回基础信息和已有展示值，后台重试 |
| Lance 操作超时 | 保留结果未知状态，通过真实查询核实，不立即重做修改操作 |

<a id="view-scenarios"></a>

### 17.5 场景视图：用例驱动的“+1”

场景视图将调用者、业务目标、关键流程和验收用例串联起来，用来核对前四个视图能否共同完成需求。

```mermaid
flowchart LR
    metadataUser["元数据使用者"] --> sharedRead["从任一协议读取同一对象"]
    metadataUser --> searchScenario["仅检索和查看有权对象"]
    developerUser["开发与管理人员"] --> createScenario["创建或注册并完成权限绑定"]
    developerUser --> changeScenario["演进 Schema、改名或移动对象"]
    developerUser --> dataScenario["在授权范围内读写和查询数据"]
    developerUser --> jobScenario["构建索引、回填或刷新视图"]
    developerUser --> deleteScenario["注销或删除并退休外部资源"]
    externalProvider["外部信息维护方"] --> enrichmentScenario["更新展示信息和安全属性"]
    recoveryWorker["后台恢复任务"] --> recoveryScenario["修复中断、漏事件与确认丢失"]
    sharedRead --> unifiedRules["共享身份与统一业务规则"]
    createScenario --> unifiedRules
    changeScenario --> unifiedRules
    dataScenario --> unifiedRules
    jobScenario --> unifiedRules
    deleteScenario --> unifiedRules
    searchScenario --> consistentAuthorization["一致的权限决策与执行约束"]
    unifiedRules --> consistentAuthorization
    enrichmentScenario --> fieldOwnership["字段归属、可信版本与失败处理"]
    recoveryScenario --> recoverableState["可恢复的操作与同步状态"]
```

| 场景 | 关键流程 | 需要验证的结果 | 对应验收 |
|---|---|---|---|
| 同一表从三种协议访问 | [统一请求](#flow-request)、[统一鉴权](#flow-authorization) | 定位相同对象 ID，同一动作使用相同权限点，响应符合入口协议 | AT-02、AT-26、AT-28 |
| 列表搜索中混有无权对象 | [统一请求](#flow-request)、[统一鉴权](#flow-authorization) | 无越权结果、数量或统计泄漏，授权分页可以继续 | AT-24、AT-33 |
| 创建成功但权限绑定暂时失败 | [对象创建](#flow-create)、[同步恢复](#flow-recovery) | 对象保持受控，恢复后激活，不重复创建底层表 | AT-07、AT-31、AT-32 |
| 旧协议更新公共字段 | [元数据变更](#flow-change) | Lance 扩展字段保留，条件冲突不覆盖其他已生效修改 | AT-12、AT-26、AT-27 |
| 跨 Namespace 移动并发生继承变化 | [元数据变更](#flow-change)、[统一鉴权](#flow-authorization) | 校验源和目标，外部确认新关系前不按旧关系继续访问 | AT-10、AT-28、AT-31 |
| 展示信息超时或权限属性缺失 | [展示补齐](#flow-enrichment)、[权限交互](#flow-authorization) | 前者允许授权后的降级展示，后者阻止操作 | AT-29、AT-30 |
| 原子提交成功但主元数据只写入部分 | [批量提交](#flow-batch)、[同步恢复](#flow-recovery) | 不暴露伪完整结果，恢复缺失记录，不重新提交底层事务 | AT-08、AT-21、AT-34 |
| 后台作业排队期间权限变化 | [异步作业](#flow-jobs) | 派发前重新鉴权，受理与完成分开，不能借服务账号越权 | AT-13、AT-20、AT-28 |
| 删除重建后收到旧事件或旧确认 | [注销删除](#flow-delete)、[同步恢复](#flow-recovery) | 对象 ID 与代次隔离，旧对象不复活，新对象不被修改 | AT-23、AT-31、AT-32 |

上述流程与对象章节共同作为实现和联调依据。图中的外部交互仍按第 15 章自定义契约实施，不能将其当作 Lance 标准路由；图中的状态和示例名称也不改变既有 54 个标准接口的请求与响应模型。
