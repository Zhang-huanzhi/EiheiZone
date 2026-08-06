# 当前系统架构

| 适用产品版本 | Current / v1.x |
| --- | --- |
| 文档状态 | Active |
| 最后更新 | 2026-08-06 |

本文档只记录当前架构摘要。V1 的完整需求、数据、API 和页面设计保存在 [`versions/v1/02_v1_design.md`](versions/v1/02_v1_design.md)；两者冲突时，以实际代码、Migration 和当前发布记录为准，并在迭代文档中说明变化。

## 1. 运行拓扑

```text
浏览器 / PWA
    |
    v
Caddy（HTTPS 与反向代理）
    |-- 页面请求 --> Next.js / React
    `-- /api/* ---> FastAPI
                         |
                         v
                    PostgreSQL
```

浏览器只访问一个站点 Origin。Caddy 是唯一对公网暴露 `80/443` 的服务；Next.js 负责页面、路由和交互；FastAPI 负责认证、授权、业务规则、事务和全部数据库访问；PostgreSQL 保存业务数据与服务端 Session。

## 2. 代码边界

后端业务模块遵循 `Router -> Service -> Repository`：Router 处理 HTTP 输入和入口权限，Service 负责业务规则与事务，Repository 负责数据访问。前端按 App Router、共享组件和 `src/features/` 领域功能组织，不直接访问数据库。

## 3. 当前安全与数据边界

- Session 保存在 PostgreSQL，浏览器使用 HttpOnly、Secure、SameSite Cookie；
- 修改请求使用签名 Double Submit CSRF；
- 权限在 Router 入口检查，并在 Service 规则和 Repository 查询中再次约束；
- 数据库时间使用 UTC，金额使用精确十进制，主键使用 UUID；
- 开发和测试数据库与生产数据库分离；
- 真实环境变量、家庭数据、数据库备份和签名材料不进入 Git。

## 4. 架构变更

不影响外部契约的局部代码调整不需要修改本文档。角色、权限、核心对象、API、存储、部署形态或跨模块边界变化时，在对应迭代文档记录影响；如果决定会影响多个后续模块，再新增 `adr/` 决策文档。
