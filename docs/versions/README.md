# 版本归档

`docs/versions/` 只保存已封箱的历史版本。归档后物理冻结：不随后续功能回填，不重写正文；只允许修复失效的相对路径。新工作记录在 `docs/tasks/`，规则见 `docs/standards/branching-and-tasks.md`。

- `v1.0`–`v1.4` 属于早期历史资产，保持原有目录和版本内 `_附件_/` 结构，予以物理冻结。
- `v1.5` 尚未封箱；已完成但未归档的任务仍留在 `docs/tasks/`，积累足够后再新建 `versions/v1.5/`。

## 版本列表

| 版本 | 归档入口 | 说明 |
| --- | --- | --- |
| `v1.4` | `docs/versions/v1.4/README.md` | 微信通知、Post 评论、图片编辑清理、部署恢复 |
| `v1.3` | `docs/versions/v1.3/README.md` | 图片预览、加载反馈、慢请求监控、HTTP/3 验证 |
| `v1.2` | `docs/versions/v1.2/README.md` | 性能基线、公网诊断、纯文档变更跳过部署 |
| `v1.1` | `docs/versions/v1.1/README.md` | Post 多图、Family 发帖、QA 时间、SSH 自动部署 |
| `v1.0` | `docs/versions/v1/README.md` | 初始版本需求、设计、计划、测试与发布材料 |

不再新建 `registry.yaml` 或任何与目录内容重复的索引文件。
