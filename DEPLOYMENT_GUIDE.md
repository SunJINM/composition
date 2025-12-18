# 作文评分系统 - 部署指南

## 项目重构说明

本项目已从原来混乱的单文件结构重构为清晰的分层架构:

### 重构前 → 重构后

```
旧结构 (混乱)                    新结构 (清晰)
├── server.py                   ├── app/
├── essays_data.json            │   ├── models/        (数据库模型)
├── ai-scoring.html             │   ├── schemas/       (数据验证)
├── extract_essays.py           │   ├── api/           (API路由)
└── ...                         │   ├── services/      (业务逻辑)
                                │   └── utils/         (工具函数)
                                ├── templates/         (HTML模板)
                                ├── static/            (静态文件)
                                ├── scripts/           (脚本工具)
                                └── data/              (数据文件)
```

### 核心改进

1. **数据持久化**: JSON文件 → MySQL数据库
2. **代码组织**: 单文件 → 分层架构 (API → Service → Model)
3. **配置管理**: 硬编码 → 环境变量 + 配置文件
4. **批次管理**: 新增批次概念,优化数据关联
5. **可维护性**: 模块化设计,职责分离

---

## 快速开始

### 1. 环境准备

#### 1.1 Python环境
```bash
# 确保Python版本 >= 3.8
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 1.2 安装依赖
```bash
pip install -r requirements.txt
```

#### 1.3 MySQL数据库
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE essay_scoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置

#### 2.1 复制环境变量模板
```bash
cp .env.example .env
```

#### 2.2 编辑.env文件
```ini
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_password
DB_NAME=essay_scoring
DB_CHARSET=utf8mb4

# OpenAI配置
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1
OPENAI_API_KEY=your_actual_api_key
OPENAI_MODEL=gpt-4

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=True
```

### 3. 数据库初始化

#### 3.1 创建表结构
```bash
python scripts/init_db.py
```

输出示例:
```
============================================================
作文评分系统 - 数据库初始化
============================================================
开始创建数据库表...
数据库表创建完成!
初始化年级数据...
成功插入 3 条年级数据
初始化文体数据...
成功插入 2 条文体数据
============================================================
数据库初始化完成!
============================================================
```

#### 3.2 迁移历史数据
```bash
python scripts/migrate_data.py
```

输出示例:
```
============================================================
作文评分系统 - 数据迁移
============================================================

开始迁移批次数据...
成功迁移 17 个批次

开始迁移作文数据...
成功迁移 1082 篇作文

更新批次作文数量...
成功更新 17 个批次的作文数量

开始迁移提示词数据...
成功迁移 XX 条提示词

============================================================
迁移验证
============================================================
批次数量: 17 (期望: 17)
作文总数: 1082 (期望: 1082)
10分制作文: XX
40分制作文: XX
============================================================
数据迁移完成!
============================================================
```

### 4. 启动应用

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --reload --port 8000
```

应用将在 http://localhost:8000 启动

---

## 项目结构详解

### 核心目录

```
app/
├── models/          # 数据库模型 (ORM)
│   ├── user.py      # 用户模型
│   ├── batch.py     # 批次模型
│   ├── essay.py     # 作文模型
│   ├── evaluation.py# 评价模型
│   └── score.py     # 评分模型
│
├── schemas/         # Pydantic模式 (数据验证)
│   ├── essay.py     # 作文相关的请求/响应模式
│   └── ...
│
├── api/             # API路由 (控制器)
│   ├── essays.py    # 作文相关API
│   ├── batches.py   # 批次相关API
│   └── ...
│
├── services/        # 业务逻辑层
│   ├── ai_service.py       # AI调用服务
│   ├── essay_service.py    # 作文业务逻辑
│   └── ...
│
└── utils/           # 工具函数
    ├── converters.py       # 分制转换等工具
    └── ...
```

### 数据流向

```
用户请求
    ↓
API层 (api/)         - 接收请求,验证参数
    ↓
服务层 (services/)   - 处理业务逻辑
    ↓
模型层 (models/)     - 数据库操作
    ↓
数据库 (MySQL)
```

---

## 数据库设计

### 核心表关系

```
composition_batches (批次表)
    ↓ (1对多)
composition_essays (作文表)
    ↓ (1对多)
composition_evaluations (评价表)
    ↓ (1对多)
composition_scores (评分表)
```

### 关键字段说明

**作文表 (composition_essays)**
- `batch_id`: 关联批次 (重要!)
- `score_system`: 分制 (10/40)
- `original_score`: 原始评分

**批次表 (composition_batches)**
- `directory_name`: 批次唯一标识
- `essay_title`: 作文题目
- `essay_requirement`: 作文要求
- `essay_count`: 该批次作文数量

---

## 开发指南

### 添加新API

1. 在 `app/schemas/` 创建请求/响应模式
2. 在 `app/services/` 添加业务逻辑
3. 在 `app/api/` 创建路由
4. 在 `app/main.py` 注册路由

### 修改数据库模型

1. 修改 `app/models/` 中的模型
2. 创建迁移脚本 (如需要)
3. 运行迁移更新数据库

### 环境变量管理

- 开发环境: 使用 `.env` 文件
- 生产环境: 使用系统环境变量

---

## 常见问题

### Q1: 数据库连接失败
**A**: 检查 `.env` 文件中的数据库配置是否正确,确保MySQL服务已启动

### Q2: 迁移数据失败
**A**: 确保已正确执行 `init_db.py` 创建表结构,检查JSON文件是否存在于 `data/` 目录

### Q3: 如何查看API文档
**A**: 启动应用后访问 http://localhost:8000/docs (Swagger UI)

### Q4: 原来的JSON文件怎么办
**A**: 迁移后会保留在 `data/` 目录,可作为备份

---

## 下一步计划

- [ ] 完成所有API接口开发
- [ ] 重构前端页面 (作文列表、评分页面)
- [ ] 添加用户登录功能
- [ ] 添加提示词管理页面
- [ ] 完善错误处理和日志
- [ ] 编写单元测试
- [ ] 性能优化 (缓存、分页等)

---

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PyMySQL
- **数据库**: MySQL 8.0+
- **AI**: OpenAI GPT-4
- **配置**: python-dotenv + pydantic-settings
- **开发**: Python 3.8+

---

## 联系方式

如有问题,请查看 `requirements/需求分析文档_v3.md`
