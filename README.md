# Vaultwarden 自动备份脚本

通过 GitHub Actions 实现 Vaultwarden (Bitwarden) 密码库的定时自动备份，并将加密的备份文件发送到指定邮箱。

## ✨ 功能特性

- **定时备份**: 每天 UTC 0 点 (北京时间 8 点) 自动执行
- **手动触发**: 支持随时手动运行备份任务
- **推送触发**: 代码更新时自动执行备份，确保配置生效
- **安全加密**: 备份文件使用 GPG 加密，保障数据安全
- **邮件通知**: 自动发送带备份附件的邮件到指定邮箱
- **时区适配**: 自动使用北京时间生成备份文件名

## 📋 前置条件

1. GitHub 账号及仓库
2. Vaultwarden/Bitwarden 账号
3. 支持 SMTP 的邮箱 (如 QQ、163、Gmail 等)
4. 已获取邮箱 SMTP 授权码

## 🚀 快速开始

### 1. 仓库准备

1. Fork 或克隆本仓库
2. 在 GitHub 仓库中配置 Secrets (Settings → Secrets and variables → Actions → Repository secrets)

### 2. 配置 Secrets

添加以下 Secrets 到你的 GitHub 仓库：

|     密钥名称      |           说明            |                     示例                      |
| :---------------: | :-----------------------: | :-------------------------------------------: |
|    `BW_EMAIL`     |   Vaultwarden 登录邮箱    |              `user@example.com`               |
|   `BW_PASSWORD`   |    Vaultwarden 主密码     |            `your_master_password`             |
|    `BW_SERVER`    |  Vaultwarden 服务器地址   |        `https://vault.yourdomain.com`         |
|   `EMAIL_USER`    |       发件邮箱地址        |             `backup@example.com`              |
| `EMAIL_PASSWORD`  |     邮箱 SMTP 授权码      |            `your_email_auth_code`             |
| `EMAIL_SMTP_HOST` |     邮箱 SMTP 服务器      |                 `smtp.qq.com`                 |
| `EMAIL_SMTP_PORT` |      邮箱 SMTP 端口       |                     `465`                     |
| `EMAIL_RECEIVERS` | 收件邮箱 (多个用逗号分隔) | `receiver1@example.com,receiver2@example.com` |

### 3. 工作流文件

项目已包含 GitHub Actions 配置文件 `.github/workflows/backup.yml`，无需修改即可使用。

### 4. 备份脚本

主备份脚本 `vaultwarden_backup.py` 已配置好所有逻辑，包括：

- 环境变量读取与验证
- Vaultwarden 登录与数据导出
- 备份文件加密
- 邮件发送
- 时区自动适配 (北京时间)

## 🔧 使用说明

### 触发方式

1. **定时触发**: 每天北京时间 8 点自动执行

2. 手动触发

   :

   - 进入仓库 Actions 页面
   - 选择 "Vaultwarden 备份到邮箱" workflow
   - 点击 "Run workflow" 手动执行

   

3. **推送触发**: 代码推送到仓库时自动执行

### 备份文件

- 备份文件格式: JSON
- 文件名格式: `YYYYMMDD_HHMMSS.json` (北京时间)
- 存储位置：邮件附件
- 加密方式: GPG (可选)

## 📝 工作流程详解

1. **环境准备**: 安装 Python 和 Bitwarden CLI
2. **登录 Vaultwarden**: 使用配置的账号密码登录
3. **数据导出**: 导出完整密码库为 JSON 文件
4. **文件加密**: 使用 GPG 加密备份文件
5. **邮件发送**: 将加密文件作为附件发送到指定邮箱
6. **清理工作**: 清理临时文件和登录会话

## ⚠️ 安全建议

1. **定期轮换**: 定期更换 Vaultwarden 主密码和邮箱授权码
2. **最小权限**: 邮箱账号仅开启必要的 SMTP 权限
3. **备份验证**: 定期检查备份邮件，确保备份正常
4. **文件加密**: 建议开启 GPG 加密，防止数据泄露
5. **权限控制**: 限制 GitHub Secrets 的访问权限

## 🐛 故障排除

### 常见问题

1. **时区问题**: 脚本已自动配置为北京时间，无需手动调整
2. **SMTP 连接失败**: 检查邮箱 SMTP 配置和授权码
3. **登录失败**: 验证 Vaultwarden 账号密码和服务器地址
4. **文件过大**: 若密码库较大，可调整邮件大小限制或使用压缩

### 日志查看

1. 进入仓库 Actions 页面
2. 选择最近的运行记录
3. 展开各步骤查看详细日志

## 📄 许可证

本项目基于 MIT 许可证开源，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

------

**注意**: 请确保所有敏感信息都通过 GitHub Secrets 管理，不要直接硬编码在代码中。