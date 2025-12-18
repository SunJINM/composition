# 作文评分系统

一个基于 FastAPI + HTML 的作文批改与分数管理系统。

## 功能特性

✅ 展示作文答卷图片
✅ 在线查看PDF分析报告
✅ 显示提取的作文文本内容
✅ 展示总分和各维度得分
✅ 手动编辑分数并自动保存到JSON文件
✅ 美观的渐变UI设计
✅ 响应式布局支持

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
python server.py
```

服务将在 `http://localhost:8000` 启动

### 3. 访问系统

在浏览器中打开: `http://localhost:8000`

## 使用说明

1. **选择作文**: 使用下拉菜单选择要查看的作文
2. **查看内容**:
   - 左侧显示作文答卷图片和PDF分析报告
   - 右侧显示作文文本内容和分数管理
3. **编辑分数**:
   - 可以修改总分(0-100)
   - 可以修改各维度分数(不超过该维度最大分)
4. **保存分数**: 点击"💾 保存分数"按钮将分数保存到 `essays_data.json`

## API接口

### 获取所有作文
```
GET /api/essays
```

### 获取指定作文
```
GET /api/essays/{index}
```

### 更新作文分数
```
PUT /api/essays/{index}/score
Content-Type: application/json

{
  "index": 0,
  "score_data": {
    "total_score": 85.0,
    "dimensions": {
      "中心立意": {"score": 18, "max_score": 20},
      "语言表达": {"score": 22, "max_score": 25},
      ...
    }
  }
}
```

### 获取文件(图片/PDF)
```
GET /api/file/image/{index}  # 获取作文答卷图片
GET /api/file/pdf/{index}    # 获取分析报告PDF
```

## 项目结构

```
mifeng/
├── server.py              # FastAPI后端服务
├── index.html             # 前端页面
├── essays_data.json       # 作文数据(自动保存)
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: 原生 HTML + CSS + JavaScript
- **数据存储**: JSON文件

## 注意事项

- 确保 `essays_data.json` 文件存在且格式正确
- 确保作文图片和PDF文件路径正确
- 修改分数后记得点击保存按钮
- 服务器运行期间会自动重载代码更改
