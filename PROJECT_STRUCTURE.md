# 作文评分系统 - 项目结构说明

## 目录结构

```
composition/
├── app/                          # 应用主目录
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI应用入口
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   │
│   ├── models/                  # 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型
│   │   ├── grade.py            # 年级模型
│   │   ├── genre.py            # 文体模型
│   │   ├── prompt.py           # 提示词模型
│   │   ├── batch.py            # 批次模型
│   │   ├── essay.py            # 作文模型
│   │   ├── evaluation.py       # 评价模型
│   │   ├── score.py            # 评分模型
│   │   └── feedback.py         # 反馈模型
│   │
│   ├── schemas/                 # Pydantic模式(请求/响应)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── batch.py
│   │   ├── essay.py
│   │   ├── evaluation.py
│   │   ├── score.py
│   │   └── prompt.py
│   │
│   ├── api/                     # API路由
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入
│   │   ├── users.py            # 用户相关API
│   │   ├── batches.py          # 批次相关API
│   │   ├── essays.py           # 作文相关API
│   │   ├── evaluations.py      # 评价相关API
│   │   ├── scores.py           # 评分相关API
│   │   ├── prompts.py          # 提示词相关API
│   │   └── feedbacks.py        # 反馈相关API
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── ai_service.py       # AI服务(调用OpenAI)
│   │   ├── essay_service.py    # 作文业务逻辑
│   │   ├── score_service.py    # 评分业务逻辑
│   │   └── genre_detector.py   # 文体判断服务
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── validators.py       # 验证工具
│       └── converters.py       # 转换工具(分制转换等)
│
├── static/                      # 静态文件
│   ├── css/                    # 样式文件
│   ├── js/                     # JavaScript文件
│   └── images/                 # 图片文件
│
├── templates/                   # HTML模板
│   ├── login.html
│   ├── index.html              # 作文列表页
│   ├── ai-scoring.html         # 评分页面
│   └── prompts-management.html # 提示词管理
│
├── scripts/                     # 脚本工具
│   ├── init_db.py              # 数据库初始化
│   ├── migrate_data.py         # 数据迁移
│   ├── extract_essays.py       # 作文提取(现有)
│   └── upload_to_oss.py        # OSS上传(现有)
│
├── data/                        # 数据文件(迁移前的JSON)
│   ├── essays_data.json
│   ├── essays_require.json
│   ├── analyze_prompts.json
│   └── score_prompts.json
│
├── logs/                        # 日志文件
│   └── app.log
│
├── tests/                       # 测试文件
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
│
├── requirements/                # 需求文档
│   └── 需求分析文档_v3.md
│
├── .env                         # 环境变量(不提交)
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── config.json                  # 配置文件(可选)
├── requirements.txt             # Python依赖
├── README.md                    # 项目说明
└── run.py                       # 启动脚本
```

## 核心设计原则

### 1. 分层架构
- **API层** (api/): 处理HTTP请求和响应
- **服务层** (services/): 业务逻辑处理
- **数据层** (models/): 数据库模型定义
- **模式层** (schemas/): 数据验证和序列化

### 2. 职责分离
- 每个模块只负责单一职责
- 避免循环依赖
- 清晰的调用关系: API → Service → Model

### 3. 可维护性
- 代码按功能模块组织
- 统一的命名规范
- 完善的文档和注释

### 4. 可扩展性
- 易于添加新功能
- 支持多种配置方式
- 模块化设计

## 迁移说明

### 从旧结构到新结构的映射

| 旧文件 | 新位置 | 说明 |
|--------|--------|------|
| server.py | app/main.py + app/api/*.py | 拆分为多个API路由 |
| essays_data.json | data/essays_data.json | 迁移到数据库后归档 |
| essays_require.json | data/essays_require.json | 迁移到数据库后归档 |
| analyze_prompts.json | data/analyze_prompts.json | 迁移到数据库后归档 |
| score_prompts.json | data/score_prompts.json | 迁移到数据库后归档 |
| ai-scoring.html | templates/ai-scoring.html | 移动到templates |
| index.html | templates/index.html | 移动到templates |
| extract_essays.py | scripts/extract_essays.py | 移动到scripts |
| upload_files_to_oss.py | scripts/upload_to_oss.py | 移动到scripts |

## 下一步操作

1. 创建目录结构
2. 配置数据库连接
3. 定义数据库模型
4. 编写数据迁移脚本
5. 重构API接口
6. 测试验证
