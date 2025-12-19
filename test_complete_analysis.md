# 一站式作文批改接口测试文档

## 接口信息
- **端点**: `POST /api/evaluations/complete-analysis`
- **功能**: 一站式作文批改(批次管理+作文保存+AI分析+AI评分)

## 请求参数

### 必填字段
```json
{
  "essay_content": "作文文本内容(必填)"
}
```

### 可选字段
```json
{
  "user_phone": "18348056312",  // 默认值
  "essay_image": null,          // 作文图片路径
  "essay_title": "",            // 作文题目
  "essay_requirement": "",      // 作文要求
  "student_name": null,         // 学生姓名
  "score_system": 40            // 分制(10或40)
}
```

## 响应示例

```json
{
  "success": true,
  "evaluation_id": 123,
  "essay_id": 456,
  "batch_id": 789,
  "total_score": 35,
  "analysis_result": {
    "overall_evaluation": {
      "summary": "...",
      "quality_level": "...",
      "main_strengths": [],
      "main_issues": []
    },
    "requirement_evaluation": [],
    "typos": [],
    "punctuation_errors": [],
    "grammar_errors": [],
    "highlights": [],
    "total_score": 35,
    "evaluation_id": 123
  }
}
```

## 测试用例

### 用例1: 最简请求(只传作文内容)
```bash
curl -X POST "http://localhost:8000/api/evaluations/complete-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_content": "这是一篇测试作文。今天天气真好,我和同学们一起去公园玩。我们看到了很多美丽的花朵,还有可爱的小鸟。"
  }'
```

### 用例2: 完整请求(包含所有字段)
```bash
curl -X POST "http://localhost:8000/api/evaluations/complete-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_content": "这是一篇测试作文...",
    "essay_title": "我的一天",
    "essay_requirement": "记叙文,不少于600字",
    "student_name": "张三",
    "user_phone": "13800138000",
    "score_system": 40
  }'
```

### 用例3: 批次复用测试
```bash
# 第一次提交
curl -X POST "http://localhost:8000/api/evaluations/complete-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_content": "作文内容1...",
    "essay_title": "我的家乡",
    "essay_requirement": "介绍家乡特色"
  }'

# 第二次提交(相同题目和要求,应复用批次)
curl -X POST "http://localhost:8000/api/evaluations/complete-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "essay_content": "作文内容2...",
    "essay_title": "我的家乡",
    "essay_requirement": "介绍家乡特色"
  }'
```

## 核心功能验证

### ✅ 批次智能管理
- 相同题目+要求 → 复用现有批次
- 不同题目/要求 → 创建新批次
- 自动更新批次作文数量

### ✅ 作文数据保存
- 自动统计字数
- 保存图片路径(可选)
- 记录学生姓名(可选)
- 支持10分制/40分制

### ✅ AI分析
- 使用默认分析提示词
- 自动识别错别字、标点错误、语病
- 提取好词好句
- 生成综合评价

### ✅ AI评分
- 使用默认评分提示词
- 基于分析结果评分
- 五维度评分(中心立意、语言表达、篇章结构、文章选材、内容情感)
- 自动转换分制(10分制/40分制)

### ✅ 返回结果
- 批改结果JSON(分析结果)
- 总评分
- evaluation_id(评价ID)
- essay_id(作文ID)
- batch_id(批次ID)

## 数据库变更

### 新增批次记录(如需要)
```sql
INSERT INTO composition_batches (directory_name, essay_title, essay_requirement, essay_count, status)
VALUES ('batch_20241219_123456', '我的家乡', '介绍家乡特色', 1, 1);
```

### 新增作文记录
```sql
INSERT INTO composition_essays (batch_id, student_name, essay_content, word_count, score_system, status)
VALUES (1, '张三', '作文内容...', 625, 40, 1);
```

### 新增评价记录
```sql
INSERT INTO composition_evaluations (essay_id, user_phone, analyze_prompt_id, evaluation_result, is_latest, status)
VALUES (1, '18348056312', 1, '{"overall_evaluation": {...}}', 1, 1);
```

### 新增评分记录
```sql
INSERT INTO composition_scores (evaluation_id, user_phone, score_prompt_id, score_type, total_score, dimension_scores, is_default, status)
VALUES (1, '18348056312', 2, 'ai', 35, '{"theme_and_intent": {...}}', 1, 1);
```

## 注意事项

1. **默认提示词**: 需要确保数据库中存在`prompt_type='analyze'`和`prompt_type='score'`且`is_default=1`的提示词记录
2. **批次复用逻辑**: 基于`essay_title`和`essay_requirement`的完全匹配
3. **分制转换**: 10分制=(百分制分数/100)*10, 40分制=(百分制分数/100)*40
4. **用户手机号**: 默认值为`18348056312`
5. **事务处理**: 所有操作在同一事务中,失败自动回滚

## 错误处理

### 未找到默认提示词
```json
{
  "detail": "未找到默认分析提示词"
}
```

### AI返回格式错误
```json
{
  "detail": "AI返回格式错误: ..."
}
```

### 通用错误
```json
{
  "detail": "作文批改失败: ..."
}
```
