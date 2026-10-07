# Python 刷题小站

一个面向 Python 初学者的前后端分离选择题 Web App。前端使用 Vue 3、Vite 和 Element Plus，
后端使用 FastAPI、SQLAlchemy 和 SQLite；通过环境变量可以切换到 MySQL。

## 已实现功能

- 一次展示一道单选题，选项卡片支持选中、正确绿色、选错红色状态；
- 后端判题后返回正确答案和中文解析，不在抽题接口中提前泄露答案；
- Markdown 题干与 Python 代码块渲染，使用 Highlight.js 高亮；
- 本轮完成题数、答对数、答错数和正确率统计，浏览器会话内保留；
- 10 个新手学习阶段，可选择综合练习或指定阶段，每轮 10/20/50 题；
- 首次启动自动生成并批量写入 10,000 道原创题，每阶段 1,000 道；
- 无登录的简易新增题目页面；
- SQLite 开箱即用，配置 `DATABASE_URL` 后可切换 MySQL；
- CORS、健康检查、API 文档和 Render Blueprint 均已配置。

## 项目结构

```text
python-quiz-station/
├── backend/
│   ├── app/
│   │   ├── routers/questions.py    # RESTful 题目接口
│   │   ├── database.py             # SQLite / MySQL 连接
│   │   ├── models.py               # questions 表
│   │   ├── schemas.py              # Pydantic 校验模型
│   │   ├── question_bank.py        # 10,000 道分阶段题库生成器
│   │   ├── seed.py                 # 空库初始化
│   │   └── main.py                 # FastAPI 入口、CORS、健康检查
│   ├── scripts/                    # 题库审计与 JSON 导出工具
│   ├── tests/                      # API 测试
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── api/                    # Axios 接口封装
│   │   ├── components/             # Markdown 与选项卡片
│   │   ├── stores/                 # 本轮统计状态
│   │   └── views/                  # 刷题、统计、新增题目页
│   └── package.json
├── samples/sample_questions.json   # 测试用样例题
├── DATASET.md                      # 学习路线与题库说明
├── DEPLOYMENT.md                   # Render 部署说明
└── render.yaml                     # Render Blueprint
```

## 环境要求

- Python 3.11 或更高版本；
- Node.js 20.19 或更高版本（Vite 7 要求）；
- npm 10 或更高版本。

## 本地启动后端

macOS / Linux：

```bash
cd python-quiz-station/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell 激活虚拟环境的命令为：

```powershell
.venv\Scripts\Activate.ps1
```

首次启动会在 `backend/python_quiz.db` 建表并生成 10,000 道题。可访问：

- API：<http://127.0.0.1:8000>
- Swagger 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

## 本地启动前端

另开一个终端：

```bash
cd python-quiz-station/frontend
npm install
npm run dev
```

打开 <http://localhost:5173>。本地开发时 Vite 会自动把 `/api` 代理到 `http://127.0.0.1:8000`，
不需要设置前端环境变量。

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/question/random` | 随机题；可选 `stage=1..10` 和 `exclude_ids=1,2,3` |
| POST | `/api/question/check` | 提交 `question_id` 和 `selected_answer`，返回判题与解析 |
| POST | `/api/question/add` | 新增题目 |
| GET | `/api/question/list` | 返回全部公开题目，不包含正确答案 |

判题示例：

```bash
curl -X POST http://127.0.0.1:8000/api/question/check \
  -H 'Content-Type: application/json' \
  -d '{"question_id": 1, "selected_answer": "A"}'
```

新增样例：

```bash
jq '.[0]' samples/sample_questions.json | \
  curl -X POST http://127.0.0.1:8000/api/question/add \
    -H 'Content-Type: application/json' \
    --data-binary @-
```

样例文件是数组，而接口一次接收一道题；上面的 `jq` 命令会取出第一道。也可以直接使用网页录入页。

## 运行测试与构建检查

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/audit_question_bank.py
pytest -q

cd ../frontend
npm run build
```

## 配置说明

后端环境变量参见 `backend/.env.example`：

- `DATABASE_URL`：默认 `sqlite:///./python_quiz.db`；
- `CORS_ORIGINS`：允许访问 API 的前端来源，多个地址用英文逗号分隔。

前端环境变量参见 `frontend/.env.example`：

- `VITE_API_BASE_URL`：生产环境后端来源，例如 `https://api.example.com`，不要附加 `/api`。

完整上线步骤和免费 SQLite 的数据持久化限制见 [DEPLOYMENT.md](./DEPLOYMENT.md)。
题库路线、审计和导出方法见 [DATASET.md](./DATASET.md)。
