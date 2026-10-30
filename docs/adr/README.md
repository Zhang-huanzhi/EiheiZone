# Architecture Decision Records

做迭代计划时先判断这次选择的影响范围。选择会影响多个模块、部署方式、安全或数据边界，或者以后的迭代还得再做一次同样的决定时，在本目录新增 ADR，并从当次迭代文档链接过来。只影响当前功能内部实现的取舍留在迭代文档的短文或简表里，不单独建 ADR。

## 模板结构

```markdown
# ADR-NNNN：决策标题

| 项目 | 内容 |
| --- | --- |
| 状态 | Proposed / Accepted / Superseded |
| 日期 | YYYY-MM-DD |
| 相关迭代 | [迭代名称](../iterations/...) |

## 背景
## 候选方案
## 决策
## 后果
```

## 已记录决策

- [ADR-0001：编码代理的协作约定与 Git 边界](0001-coding-agent-collaboration.md)
- [ADR-0002：非运行时文件不触发生产部署](0002-skip-deploy-for-non-runtime-files.md)
