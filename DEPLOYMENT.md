# Render 上线部署文档

本项目可以在 Render 上把后端部署为 Python Web Service，把前端部署为 Static Site，
并使用 Neon 免费 Postgres 保存账号和答题记录。仓库根目录的 `render.yaml` 已包含服务配置。

> 注意：Render 免费 Web Service 的本地文件系统是临时的，不能用线上 SQLite 保存账号。
> Render 自带的免费 Postgres 30 天后过期，因此本文使用没有固定 30 天期限的 Neon 免费
> Postgres。免费服务条款和额度仍可能由供应商调整，重要数据应定期导出备份。

## 方案一：使用 Blueprint 一次创建前后端

1. 把整个 `python-quiz-station` 目录提交到 GitHub 仓库，确保 `render.yaml` 位于仓库根目录。
2. 登录 Render，选择 **New > Blueprint**，连接该 GitHub 仓库。
3. Render 会识别两个服务：
   - `python-quiz-api`：FastAPI 免费 Web Service；
   - `python-quiz-web`：Vue 静态站点。
4. 先在 Neon 创建免费 Postgres 项目，复制带密码的连接字符串。Blueprint 会要求填写三个
   `sync: false` 的环境变量：
   - 后端 `DATABASE_URL`：Neon 提供的 Postgres 连接字符串；
   - 后端 `CORS_ORIGINS`：前端完整来源，例如 `https://python-quiz-web.onrender.com`；
   - 前端 `VITE_API_BASE_URL`：后端完整来源，例如 `https://python-quiz-api.onrender.com`。
5. 如果 Render 因服务名占用而修改了子域名，到两个服务的 **Environment** 页面改成实际 URL。
6. 修改前端环境变量后必须重新部署前端，因为 `VITE_*` 变量在构建时写入静态文件。
7. 访问后端 `/health`，应得到 `{"status":"ok"}`；再打开前端完成一道题验证联调。

## 方案二：在控制台分别创建

### 1. 部署后端

先在 Neon 创建免费 **Postgres** 数据库，再创建 **Web Service** 并填写：

| 配置项 | 值 |
| --- | --- |
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Instance Type | Free |

后端环境变量：

```text
DATABASE_URL=postgresql+psycopg://用户名:密码@主机:5432/数据库名
CORS_ORIGINS=https://你的前端域名.onrender.com
JWT_SECRET=使用 openssl rand -hex 32 生成的随机值
TOKEN_EXPIRE_DAYS=30
```

部署完成后记下后端地址，例如 `https://python-quiz-api.onrender.com`。

### 2. 部署前端

创建 **Static Site** 并填写：

| 配置项 | 值 |
| --- | --- |
| Root Directory | `frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |

前端环境变量：

```text
VITE_API_BASE_URL=https://你的后端域名.onrender.com
```

添加 Rewrite 规则，保证直接访问 `/stats`、`/add` 或 `/login` 时仍由 Vue Router 处理：

```text
Source:      /*
Destination: /index.html
Action:      Rewrite
```

前端地址确定后，回到后端把 `CORS_ORIGINS` 改为真实前端地址并重新部署后端。

## 切换到 MySQL

后端已安装 `PyMySQL`。创建可从公网访问的 MySQL 后，把后端环境变量改为：

```text
DATABASE_URL=mysql+pymysql://用户名:密码@主机:3306/数据库名?charset=utf8mb4
```

密码中的 `@`、`:`、`/` 等特殊字符必须进行 URL 编码。数据库需要预先创建，数据表和 10,000 道初始题会在首次启动时自动建立。应用使用 `utf8mb4` 可正常保存中文和代码字符。

## 多个前端域名

预览站、正式站和自定义域名并存时，用英文逗号分隔：

```text
CORS_ORIGINS=https://preview.example.com,https://quiz.example.com
```

不要在域名末尾添加 `/`，也不要把 `*` 与凭据模式混用。

## 免费实例说明

Render 免费 Web Service 长时间没有请求时会休眠，首次访问可能需要等待冷启动。账号数据存放在
Neon Postgres 中，不会因 Render Web Service 休眠或重新部署而丢失。Neon 免费实例会自动休眠，
收到新连接后再唤醒；正式长期使用仍应定期备份，升级或迁移时只需更新 `DATABASE_URL`。
`TOKEN_EXPIRE_DAYS=30` 只表示登录凭证 30 天后需要重新登录，不会删除账号或答题记录。
