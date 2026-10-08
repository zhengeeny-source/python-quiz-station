# 微信小程序开发与发布

`miniprogram/` 是独立的 uni-app + Vue 3 + Vite 前端，编译后生成原生微信小程序文件。
它不会替换现有网站，两端共用以下后端：

```text
https://python-quiz-api.onrender.com
```

账号、答题记录、10,000 道题和新增题目都会同步到同一个 Neon PostgreSQL 数据库。

## 已实现页面

- 刷题：支持选择题、判断题、填空题、代码块、自动判题与解析；
- 统计：本轮统计、账号累计统计和最近答题记录；
- 账号：用户名密码注册、登录和退出；
- 录题：新增选择题、判断题或填空题。

## 1. 安装与编译

建议使用 Node.js 20.19 或更高版本：

```bash
cd miniprogram
npm install
npm run dev:mp-weixin
```

开发输出目录：

```text
miniprogram/dist/dev/mp-weixin
```

生产构建：

```bash
npm run build:mp-weixin
```

生产输出目录：

```text
miniprogram/dist/build/mp-weixin
```

## 2. 填写微信小程序 AppID

打开 `miniprogram/src/manifest.json`，把 `mp-weixin.appid` 从空字符串改为微信公众平台提供的
AppID：

```json
{
  "mp-weixin": {
    "appid": "wx你的AppID"
  }
}
```

AppID 不属于服务器密钥，可以提交到仓库。`AppSecret` 不需要放入当前小程序，也不要提交到
GitHub；当前版本继续使用已有的用户名密码登录。

## 3. 配置服务器域名

在微信公众平台的小程序后台进入 **开发管理 → 开发设置 → 服务器域名**，把下面地址添加为
`request` 合法域名：

```text
https://python-quiz-api.onrender.com
```

只填写域名，不要追加 `/api`，也不要保留结尾斜杠。域名必须通过 HTTPS 访问。

`manifest.json` 中的 `urlCheck: false` 仅方便开发者工具本地调试；正式体验版和正式版仍应在
微信后台配置合法域名。

如果以后更换后端，复制 `.env.example` 为 `.env` 并修改：

```text
VITE_API_BASE_URL=https://新的后端域名
```

## 4. 微信开发者工具预览

1. 安装并打开微信开发者工具；
2. 选择 **导入项目**；
3. 项目目录选择 `miniprogram/dist/dev/mp-weixin`；
4. 选择前面准备的小程序 AppID；
5. 点击编译，然后依次测试注册、答题、统计和重新打开后的记录恢复；
6. 点击 **预览**，使用管理员微信扫码在手机真机测试。

Render 免费后端长时间无人访问会休眠，首次请求可能需要等待几十秒，小程序端请求超时已设置为
60 秒。Neon 数据库存放账号和进度，不会因 Render 休眠而丢失。

## 5. 上传和发布

1. 运行 `npm run build:mp-weixin`；
2. 在微信开发者工具中导入或切换到 `dist/build/mp-weixin`；
3. 点击 **上传**，填写版本号和项目备注；
4. 在微信公众平台把该版本选为体验版进行真机验收；
5. 确认隐私指引、服务类目和页面内容后提交审核；
6. 审核通过后点击发布。

提交审核、管理员扫码和最终发布必须由小程序账号管理员完成。

## 6. 当前登录方式

小程序和网站使用同一套用户名密码，密码只以 Argon2 哈希保存在后端。以后需要“微信一键登录”
时，需要新增 `wx.login`、后端换取 OpenID 和账号绑定接口；这不是当前版本上线的必要条件。
