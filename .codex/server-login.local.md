# EiheiZone 服务器登录速查（本机专用）

> 本文件已加入 `.gitignore`，只用于本机 Codex/开发协作。不要复制到仓库、网盘或聊天中。

## 连接参数

- 用户：`ubuntu`
- 公网地址：`150.109.241.217`
- 标准 SSH 端口：`22`
- 备用 SSH 端口：`2222`
- 私钥：`C:\Users\14805\.ssh\eiheizone.pem`

## PowerShell 登录

```powershell
ssh -i "$env:USERPROFILE\.ssh\eiheizone.pem" ubuntu@150.109.241.217
```

备用端口：

```powershell
ssh -p 2222 -i "$env:USERPROFILE\.ssh\eiheizone.pem" ubuntu@150.109.241.217
```

## 首次连接与退出

- 首次出现 `Are you sure you want to continue connecting?` 时输入 `yes`。
- 成功登录后通常显示 `ubuntu@VM-0-5-ubuntu:~$`。
- 退出服务器：`exit`

## 故障排查

- `Connection timed out`：尝试另一个端口，或检查当前网络、腾讯云防火墙和免密终端。
- `Permission denied`：检查用户、端口、私钥路径以及密钥是否绑定到该实例。
- 密码登录只作为备用方式；密码不记录在本文件中。

## 操作边界

- 使用 `ubuntu` 登录，需要管理员权限时使用 `sudo`，不要直接使用 `root`。
- 仅在用户明确授权的范围内执行服务器命令。
- 不要输出、复制或上传私钥内容；不要把私钥放入项目目录。
