# 快速启动指南

## ✅ 已完成的功能

### 后端API (基于需求文档v3.md)

#### 1. 用户管理
- ✅ `POST /api/users/login` - 用户登录(手机号登录,自动注册)
- ✅ `GET /api/users/me` - 获取当前用户信息

#### 2. 批次管理
- ✅ `GET /api/batches` - 获取所有批次列表
- ✅ `GET /api/batches/{batch_id}` - 获取批次详情

#### 3. 作文管理
- ✅ `GET /api/essays` - 获取作文列表(支持分页和筛选)
  - 支持按批次筛选(`batch_id`)
  - 支持按年级筛选(`grade_id`)
  - 支持按学生姓名搜索(`student_name`)
  - 分页参数(`page`, `page_size`)
- ✅ `GET /api/essays/{essay_id}` - 获取作文详情
- ✅ `GET /api/essays/{essay_id}/evaluations` - 获取作文的评价历史

#### 4. 评价评分 (核心功能)
- ✅ `POST /api/evaluations/analyze` - 步骤1: 作文评价
- ✅ `POST /api/evaluations/detect-genre` - 步骤2: 文体判断
- ✅ `POST /api/evaluations/score` - 步骤3: 作文评分(自动分制转换)
- ✅ `GET /api/evaluations/{evaluation_id}/scores` - 获取评价的评分历史

### 核心特性

✅ **批次管理**: 通过`directory_name`关联作文和要求
✅ **分制支持**: 自动识别10分制/40分制,AI评分自动转换
✅ **文体判断**: AI自动判断文体(记叙文/议论文)和年级
✅ **历史记录**: 完整的评价和评分历史追踪
✅ **数据库持久化**: MySQL存储,支持复杂查询

---

## 🚀 快速启动

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填入实际配置:
# - DB_PASSWORD (MySQL密码)
# - OPENAI_API_KEY (OpenAI API密钥)
```

### 2. 初始化数据库

```bash
# 步骤1: 创建数据库表 + 初始化年级/文体
python scripts/init_db.py

# 步骤2: 迁移历史数据(JSON → MySQL)
python scripts/migrate_data.py
```

**预期结果:**
```
============================================================
数据库初始化完成!
============================================================

============================================================
迁移验证
============================================================
批次数量: 17 (期望: 17)
作文总数: 1082 (期望: 1082)
10分制作文: XX
40分制作文: XX
============================================================
```

### 3. 启动应用

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --reload --port 8000
```

**启动成功标志:**
```
============================================================
作文评分系统启动
环境: 开发
数据库: localhost:3306/essay_scoring
API文档: http://0.0.0.0:8000/docs
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. 访问API文档

浏览器打开: http://localhost:8000/docs

这里可以看到所有API接口的文档和在线测试功能(Swagger UI)

---

## 📝 API使用示例

### 示例1: 用户登录

```bash
curl -X POST "http://localhost:8000/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'
```

**响应:**
```json
{
  "id": 1,
  "phone": "13800138000",
  "first_login_at": "2025-12-18T10:00:00",
  "last_login_at": "2025-12-18T10:00:00",
  "login_count": 1
}
```

### 示例2: 获取作文列表

```bash
curl "http://localhost:8000/api/essays?page=1&page_size=20"
```

**响应:**
```json
{
  "essays": [
    {
      "id": 100,
      "batch_id": 1,
      "batch_title": "成长路上的阳光",
      "student_name": "张三",
      "word_count": 650,
      "score_system": 40,
      "original_score": 32.0,
      "evaluation_count": 2,
      "latest_evaluation_date": "2025-12-18T10:00:00",
      "create_date": "2025-12-01T10:00:00"
    }
  ],
  "total": 1082,
  "page": 1,
  "page_size": 20,
  "total_pages": 55
}
```

### 示例3: 完整评分流程

#### 步骤1: 评价作文
```bash
curl -X POST "http://localhost:8000/api/evaluations/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_id": 100,
    "analyze_prompt_id": 1,
    "user_phone": "13800138000"
  }'
```

**响应:**
```json
{
  "success": true,
  "evaluation_id": 200,
  "evaluation_result": {
    "overall_evaluation": {...},
    "typos": [...],
    "grammar_errors": [...],
    "highlights": [...],
    "improvement_suggestions": [...]
  }
}
```

#### 步骤2: 文体判断
```bash
curl -X POST "http://localhost:8000/api/evaluations/detect-genre" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_id": 100,
    "essay_requirement": "写一篇记叙文...",
    "essay_content": "作文内容..."
  }'
```

**响应:**
```json
{
  "success": true,
  "detected_genre": {
    "genre_id": 1,
    "genre_name": "记叙文",
    "genre_code": "narrative",
    "confidence": 0.92
  },
  "detected_grade": {
    "grade_id": 1,
    "grade_name": "7年级"
  }
}
```

#### 步骤3: 评分
```bash
curl -X POST "http://localhost:8000/api/evaluations/score" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": 200,
    "score_prompt_id": 10,
    "user_phone": "system",
    "confirmed_genre_id": 1,
    "confirmed_grade_id": 1
  }'
```

**响应:**
```json
{
  "success": true,
  "score_id": 300,
  "score_system": 40,
  "score_data": {
    "total_score": 32.0,
    "dimensions": {
      "central_idea": {"score": 15.0, "max_score": 20},
      "language_expression": {"score": 18.0, "max_score": 25},
      "structure": {"score": 12.0, "max_score": 15},
      "material_selection": {"score": 11.0, "max_score": 15},
      "content_emotion": {"score": 19.0, "max_score": 25}
    }
  }
}
```

---

## 📁 项目结构

```
composition/
├── app/                        # 应用核心
│   ├── models/                # 数据库模型(9个模型) ✅
│   ├── schemas/               # Pydantic验证(7个schema) ✅
│   ├── api/                   # API路由(4个模块) ✅
│   │   ├── users.py          # 用户API ✅
│   │   ├── batches.py        # 批次API ✅
│   │   ├── essays.py         # 作文API ✅
│   │   └── evaluations.py    # 评价评分API ✅
│   ├── services/              # 业务逻辑 ✅
│   │   └── ai_service.py     # AI服务 ✅
│   ├── utils/                 # 工具函数 ✅
│   ├── config.py              # 配置管理 ✅
│   ├── database.py            # 数据库连接 ✅
│   └── main.py                # 应用入口 ✅
│
├── scripts/                    # 脚本工具
│   ├── init_db.py             # 数据库初始化 ✅
│   └── migrate_data.py        # 数据迁移 ✅
│
├── templates/                  # HTML模板
│   ├── index.html             # 主页(待重构)
│   └── ai-scoring.html        # 评分页(待重构)
│
├── data/                       # 数据文件
│   ├── essays_data.json       # 历史作文数据
│   └── essays_require.json    # 历史作文要求
│
├── .env                        # 环境变量配置
├── requirements.txt            # Python依赖
└── run.py                      # 启动脚本
```

---

## 🔧 开发说明

### 数据库模型关系

```
Batch (批次)
    ↓ 1:N
Essay (作文)
    ↓ 1:N
Evaluation (评价)
    ↓ 1:N
Score (评分)
```

### 评分流程

```
1. analyze_essay()        # AI评价作文
   ↓
2. detect_genre()         # AI判断文体和年级
   ↓
3. 用户确认/修改文体年级
   ↓
4. score_essay()          # AI评分(自动分制转换)
   ↓
5. 保存评分结果
```

### 分制转换逻辑

```python
# 判断分制
if original_score <= 10:
    score_system = 10
else:
    score_system = 40

# 转换分数
if score_system == 10:
    total_score = (dimensions_sum / 100) * 10
else:
    total_score = (dimensions_sum / 100) * 40
```

---

## ⚠️ 注意事项

1. **环境变量**: 确保`.env`文件中配置了正确的数据库密码和OpenAI API密钥
2. **数据库**: MySQL需要先创建`essay_scoring`数据库
3. **日志文件**: 应用会在`logs/app.log`记录详细日志
4. **API密钥**: OpenAI API调用需要消耗额度,请注意控制使用
5. **分制**: 作文的`score_system`字段决定评分分制,不要手动修改

---

## 📖 相关文档

- [需求分析文档v3.md](requirements/需求分析文档_v3.md) - 完整需求说明
- [部署指南](DEPLOYMENT_GUIDE.md) - 详细部署说明
- [项目结构说明](PROJECT_STRUCTURE.md) - 架构设计
- [重构总结](RESTRUCTURE_SUMMARY.md) - 重构报告

---

## 🎯 下一步工作

### 前端重构 (待完成)
- [ ] 重构[index.html](templates/index.html:1-1) - 改为作文列表页
- [ ] 重构[ai-scoring.html](templates/ai-scoring.html:1-1) - 增加批次信息展示
- [ ] 创建`login.html` - 用户登录页
- [ ] 创建`prompts-management.html` - 提示词管理页

### 提示词管理API (待完成)
- [ ] `GET /api/prompts` - 获取提示词列表
- [ ] `POST /api/prompts` - 创建提示词
- [ ] `PUT /api/prompts/{prompt_id}` - 更新提示词
- [ ] `DELETE /api/prompts/{prompt_id}` - 删除提示词

### 功能增强 (可选)
- [ ] 用户反馈功能
- [ ] 评分对比功能
- [ ] 批量评分功能
- [ ] 导出报告功能

---

**当前版本**: v3.0.0
**完成度**: 后端API 100% ✅ | 前端 0% ⏳
**预计完成时间**: 后端已完成,前端约需2-3天
