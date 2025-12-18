from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import json
import os
from pathlib import Path
from openai import OpenAI
from datetime import datetime

app = FastAPI(title="作文评分系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 文件路径
JSON_FILE_PATH = Path(__file__).parent / "essays_data.json"
PROMPTS_FILE_PATH = Path(__file__).parent / "prompts.json"  # 兼容旧版
ANALYZE_PROMPTS_FILE_PATH = Path(__file__).parent / "analyze_prompts.json"
SCORE_PROMPTS_FILE_PATH = Path(__file__).parent / "score_prompts.json"
ESSAYS_REQUIRE_FILE_PATH = Path(__file__).parent / "essays_require.json"

# OpenAI客户端配置
# OPENAI_CONFIG = {
#     "base_url": "https://ark.cn-beijing.volces.com/api/v3",
#     "api_key": "14ebfc74-500c-46d5-a58b-61ac61341018",
#     "model": "ep-20250904165744-rp7js"
# }

OPENAI_CONFIG = {
    "base_url": "https://api.chatanywhere.tech/v1",
    "api_key": "sk-NoQw51HWNbLknDYrargYnYpZn6znttKWulbFIkXYJIaSolbz",
    "model": "gpt-5.2"
}


class DimensionScore(BaseModel):
    score: float
    max_score: int


class ScoreData(BaseModel):
    total_score: float
    dimensions: Dict[str, DimensionScore]


class UpdateScoreRequest(BaseModel):
    index: int
    score_data: ScoreData


class PromptVersion(BaseModel):
    version: str
    prompt: str
    created_at: str
    is_default: bool = False


class SavePromptRequest(BaseModel):
    prompt: str
    version_name: Optional[str] = None
    type: str = 'score'  # 'analyze' 或 'score'


class AIScoreRequest(BaseModel):
    essay_content: str
    essay_title: Optional[str] = ""
    essay_requirement: Optional[str] = ""
    prompt: str


class AIScoreWithAnalysisRequest(BaseModel):
    essay_content: str
    essay_title: Optional[str] = ""
    essay_requirement: Optional[str] = ""
    prompt: str
    analysis: Optional[Dict] = None  # 分析结果(可选)
    original_score_data: Optional[Dict] = None  # 原始评分数据(用于判断分制)


def load_essays_data():
    """加载作文数据"""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取数据失败: {str(e)}")


def save_essays_data(data):
    """保存作文数据"""
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存数据失败: {str(e)}")


@app.get("/")
async def read_root():
    """返回主页面"""
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/ai-scoring.html")
async def read_ai_scoring():
    """返回AI评分页面"""
    html_file = Path(__file__).parent / "ai-scoring.html"
    if html_file.exists():
        return FileResponse(html_file)
    raise HTTPException(status_code=404, detail="ai-scoring.html not found")


@app.get("/api/essays")
async def get_essays():
    """获取所有作文数据"""
    data = load_essays_data()
    return {"essays": data, "total": len(data)}


@app.get("/api/essays/{index}")
async def get_essay(index: int):
    """获取指定索引的作文数据"""
    data = load_essays_data()
    if 0 <= index < len(data):
        return data[index]
    raise HTTPException(status_code=404, detail="作文数据不存在")


@app.put("/api/essays/{index}/score")
async def update_score(index: int, request: UpdateScoreRequest):
    """更新指定作文的分数"""
    data = load_essays_data()

    if index != request.index:
        raise HTTPException(status_code=400, detail="索引不匹配")

    if 0 <= index < len(data):
        # 更新分数数据
        data[index]["score_data"] = {
            "total_score": request.score_data.total_score,
            "dimensions": {
                dim_name: {
                    "score": dim_data.score,
                    "max_score": dim_data.max_score
                }
                for dim_name, dim_data in request.score_data.dimensions.items()
            }
        }

        # 保存到文件
        save_essays_data(data)

        return {"message": "分数更新成功", "data": data[index]}

    raise HTTPException(status_code=404, detail="作文数据不存在")


@app.get("/api/file/{file_type}/{index}")
async def get_file(file_type: str, index: int):
    """获取文件(图片或PDF) - 支持OSS和本地文件"""
    from fastapi.responses import RedirectResponse

    data = load_essays_data()

    if not (0 <= index < len(data)):
        raise HTTPException(status_code=404, detail="作文数据不存在")

    essay = data[index]

    if file_type == "image":
        file_path = essay.get("essay_image_path")
    elif file_type == "pdf":
        file_path = essay.get("analysis_report_path")
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    if not file_path:
        raise HTTPException(status_code=404, detail="文件路径不存在")

    # 如果是OSS地址(http/https开头),直接重定向
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return RedirectResponse(url=file_path)

    # 如果是本地文件,返回文件内容
    if os.path.exists(file_path):
        return FileResponse(file_path)

    raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")


def load_prompts(prompt_type='score'):
    """加载提示词数据
    Args:
        prompt_type: 'analyze' 或 'score'
    """
    file_path = ANALYZE_PROMPTS_FILE_PATH if prompt_type == 'analyze' else SCORE_PROMPTS_FILE_PATH

    if not file_path.exists():
        # 创建默认提示词
        default_prompt = {
            "prompts": [
                {
                    "version": "v1.0",
                    "prompt": """# 作文评分任务

## 作文要求
{essay_requirement}

## 作文内容
{essay_content}

## 作文字数
本篇作文共 {word_count} 字

## 评分标准

请严格按照以下5个维度的详细标准进行评分：

### 1. 中心立意（满分20分）
- **18-20分（优秀）**：主题鲜明突出，立意深刻新颖，能够透过现象看本质，展现独特思考
- **15-17分（良好）**：主题明确，立意较为深刻，有一定的思想深度
- **12-14分（中等）**：主题基本明确，立意一般，思想较为平淡
- **8-11分（及格）**：主题不够明确，立意较浅，缺乏深度
- **0-7分（不及格）**：主题模糊不清，立意肤浅，偏离题意

### 2. 语言表达（满分25分）
- **22-25分（优秀）**：语言流畅生动，用词精准贴切，修辞手法运用得当，句式灵活多变，表达富有感染力
- **18-21分（良好）**：语言通顺流畅，用词较为准确，有一定的表现力
- **14-17分（中等）**：语言基本通顺，用词基本准确，表达平实
- **10-13分（及格）**：语言不够流畅，用词欠准确，表达能力较弱
- **0-9分（不及格）**：语言不通顺，用词不当，表达混乱

### 3. 篇章结构（满分15分）
- **13-15分（优秀）**：结构严谨完整，层次清晰分明，过渡自然流畅，首尾呼应，详略得当
- **11-12分（良好）**：结构完整，层次较清晰，过渡较自然
- **8-10分（中等）**：结构基本完整，层次基本清楚
- **6-7分（及格）**：结构不够完整，层次不够清晰
- **0-5分（不及格）**：结构混乱，层次不清

### 4. 文章选材（满分15分）
- **13-15分（优秀）**：选材典型新颖，紧扣主题，材料真实充实，角度独特，有说服力
- **11-12分（良好）**：选材较为恰当，能够扣题，材料较为充实
- **8-10分（中等）**：选材基本恰当，基本扣题，材料一般
- **6-7分（及格）**：选材不够恰当，扣题不紧，材料较空洞
- **0-5分（不及格）**：选材不当，偏离主题，材料空泛

### 5. 内容情感（满分25分）
- **22-25分（优秀）**：内容充实具体，情感真挚感人，细节描写生动，能引起共鸣
- **18-21分（良好）**：内容较充实，情感较真实，有一定的感染力
- **14-17分（中等）**：内容基本充实，情感基本真实
- **10-13分（及格）**：内容不够充实，情感不够真实，较为空洞
- **0-9分（不及格）**：内容空洞，情感虚假，缺乏真情实感

## 输出要求

请严格按照以下JSON格式输出评分结果，**不要包含任何markdown标记、代码块标记或其他说明文字**，只输出纯JSON：

{{
  "中心立意": 整数分数,
  "语言表达": 整数分数,
  "篇章结构": 整数分数,
  "文章选材": 整数分数,
  "内容情感": 整数分数
}}

注意：
1. 所有分数必须是整数
2. 每个维度的分数不能超过其满分值
3. 评分要客观公正，严格对照评分标准
4. 只输出JSON，不要有任何其他文字""",
                    "created_at": datetime.now().isoformat(),
                    "is_default": True
                }
            ]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_prompt, f, ensure_ascii=False, indent=2)
        return default_prompt["prompts"]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("prompts", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取提示词失败: {str(e)}")


def save_prompts(prompts, prompt_type='score'):
    """保存提示词数据
    Args:
        prompts: 提示词列表
        prompt_type: 'analyze' 或 'score'
    """
    file_path = ANALYZE_PROMPTS_FILE_PATH if prompt_type == 'analyze' else SCORE_PROMPTS_FILE_PATH
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"prompts": prompts}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存提示词失败: {str(e)}")


@app.get("/api/prompts")
async def get_prompts(type: str = 'score'):
    """获取所有提示词版本
    Args:
        type: 'analyze' 或 'score', 默认为 'score'
    """
    prompts = load_prompts(type)
    return {"prompts": prompts, "type": type}


@app.post("/api/prompts")
async def save_prompt(request: SavePromptRequest):
    """保存新的提示词版本"""
    prompts = load_prompts(request.type)

    # 生成版本号
    if request.version_name:
        version = request.version_name
    else:
        version = f"v{len(prompts) + 1}.0"

    # 创建新提示词
    new_prompt = {
        "version": version,
        "prompt": request.prompt,
        "created_at": datetime.now().isoformat(),
        "is_default": False
    }

    prompts.append(new_prompt)
    save_prompts(prompts, request.type)

    return {"message": "提示词保存成功", "prompt": new_prompt, "type": request.type}


@app.put("/api/prompts/{version}/default")
async def set_default_prompt(version: str, type: str = 'score'):
    """设置默认提示词
    Args:
        version: 提示词版本
        type: 'analyze' 或 'score'
    """
    prompts = load_prompts(type)

    found = False
    for prompt in prompts:
        if prompt["version"] == version:
            prompt["is_default"] = True
            found = True
        else:
            prompt["is_default"] = False

    if not found:
        raise HTTPException(status_code=404, detail="提示词版本不存在")

    save_prompts(prompts, type)
    return {"message": "默认提示词设置成功", "type": type}


@app.delete("/api/prompts/{version}")
async def delete_prompt(version: str, type: str = 'score'):
    """删除提示词版本
    Args:
        version: 提示词版本
        type: 'analyze' 或 'score'
    """
    prompts = load_prompts(type)

    # 不允许删除默认提示词
    for prompt in prompts:
        if prompt["version"] == version and prompt.get("is_default", False):
            raise HTTPException(status_code=400, detail="不能删除默认提示词")

    prompts = [p for p in prompts if p["version"] != version]

    if len(prompts) == len(load_prompts(type)):
        raise HTTPException(status_code=404, detail="提示词版本不存在")

    save_prompts(prompts, type)
    return {"message": "提示词删除成功", "type": type}


@app.get("/api/essays-require")
async def get_essays_require():
    """获取所有作文题目和要求数据"""
    try:
        if not ESSAYS_REQUIRE_FILE_PATH.exists():
            return {"data": []}

        with open(ESSAYS_REQUIRE_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取作文要求数据失败: {str(e)}")


@app.post("/api/ai-analyze")
async def ai_analyze_essay(request: AIScoreRequest):
    """使用AI对作文进行分析(第一步)"""
    try:
        # 统计作文字数（去除空白字符）
        word_count = len(request.essay_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', ''))

        # 创建OpenAI客户端
        client = OpenAI(
            base_url=OPENAI_CONFIG["base_url"],
            api_key=OPENAI_CONFIG["api_key"]
        )

        # 构建完整用户提示词
        user_prompt = request.prompt.format(
            essay_title=request.essay_title or "无题目",
            essay_requirement=request.essay_requirement or "无特定要求",
            essay_content=request.essay_content,
            word_count=word_count
        )

        # 系统提示词
        system_prompt = """你是一位资深的语文教师和作文分析专家，拥有20年的教学经验。

你的职责：
1. 对作文进行全面、客观、细致的分析
2. 准确识别错别字和语病
3. 发现作文的优点和亮点
4. 提出具体可行的改进建议

分析原则：
- 客观公正：基于事实进行分析
- 具体详细：标注位置，给出实例
- 建设性：提供可操作的改进建议
- 鼓励为主：既指出问题也肯定优点

输出规范：
- 必须输出纯JSON格式，不要有任何额外文字
- 不要使用markdown代码块标记
- 严格按照指定的JSON结构输出"""

        # 调用AI接口
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,  # 适度随机性，保证分析的多样性
            max_tokens=4000    # 分析需要更多tokens
        )

        # 提取回复内容
        ai_response = response.choices[0].message.content.strip()

        # 尝试解析JSON
        # 移除可能的markdown代码块标记
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()

        # 解析分析结果
        analysis = json.loads(ai_response)

        # 验证必需字段
        required_fields = ["综合评价", "错别字", "错别字总数", "语病", "语病总数", "优点亮点", "改进建议"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"缺少字段: {field}")

        return {
            "success": True,
            "analysis": analysis,
            "raw_response": ai_response
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI返回格式错误: {str(e)}",
            "raw_response": ai_response if 'ai_response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI分析失败: {str(e)}"
        }


@app.post("/api/ai-score")
async def ai_score_essay(request: AIScoreWithAnalysisRequest):
    """使用AI对作文进行评分(第二步,可选地基于分析结果)"""
    try:
        # 统计作文字数（去除空白字符）
        word_count = len(request.essay_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', ''))

        # 创建OpenAI客户端
        client = OpenAI(
            base_url=OPENAI_CONFIG["base_url"],
            api_key=OPENAI_CONFIG["api_key"]
        )

        # 如果有分析结果,将完整分析结果添加到提示词中
        analysis_context = ""
        if request.analysis:
            analysis_context = f"""

## 作文分析结果(完整)

以下是对本篇作文的详细分析结果,请在评分时充分参考:

### 综合评价
{json.dumps(request.analysis.get("综合评价", {}), ensure_ascii=False, indent=2)}

### 错别字详细列表(共 {request.analysis.get("错别字总数", 0)} 个)
{json.dumps(request.analysis.get("错别字", []), ensure_ascii=False, indent=2)}

### 语病详细列表(共 {request.analysis.get("语病总数", 0)} 处)
{json.dumps(request.analysis.get("语病", []), ensure_ascii=False, indent=2)}

### 优点亮点详细列表(共 {len(request.analysis.get("优点亮点", []))} 处)
{json.dumps(request.analysis.get("优点亮点", []), ensure_ascii=False, indent=2)}

### 改进建议详细列表(共 {len(request.analysis.get("改进建议", []))} 条)
{json.dumps(request.analysis.get("改进建议", []), ensure_ascii=False, indent=2)}

**评分要求**:
- 请充分参考上述分析结果进行评分
- 特别注意错别字和语病数量对"语言表达"维度的影响
- 优点亮点应提升相应维度的分数
- 改进建议指出的问题应在相应维度扣分
"""

        # 构建完整用户提示词
        user_prompt = request.prompt.format(
            essay_title=request.essay_title or "无题目",
            essay_requirement=request.essay_requirement or "无特定要求",
            essay_content=request.essay_content,
            word_count=word_count
        ) + analysis_context

        # 优化的系统提示词
        system_prompt = """你是一位资深的语文教师和作文评分专家，拥有20年的教学经验。

你的职责：
1. 严格按照评分标准对作文进行客观、公正的评价
2. 参考各个分数段的具体标准，给出精准的分数
3. 评分要有区分度，避免集中在某个分数段
4. 既要看到优点，也要发现不足

评分原则：
- 客观性：基于文本内容，不受主观情感影响
- 准确性：严格对照评分标准的每个层次
- 一致性：保持评分尺度的统一和稳定
- 公正性：对所有作文一视同仁

输出规范：
- 必须输出纯JSON格式，不要有任何额外文字
- 不要使用markdown代码块标记
- 分数必须是整数，且在规定范围内"""

        # 调用AI接口
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 降低随机性，提高一致性
        )
        # 提取回复内容
        ai_response = response.choices[0].message.content.strip()

        # 尝试解析JSON
        # 移除可能的markdown代码块标记
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()

        # 解析分数
        scores = json.loads(ai_response)

        # 验证分数格式
        required_dimensions = ["中心立意", "语言表达", "篇章结构", "文章选材", "内容情感"]
        max_scores = {"中心立意": 20, "语言表达": 25, "篇章结构": 15, "文章选材": 15, "内容情感": 25}

        dimensions = {}
        dimensions_sum = 0

        for dim in required_dimensions:
            if dim not in scores:
                raise ValueError(f"缺少维度: {dim}")
            score = float(scores[dim])
            if score < 0 or score > max_scores[dim]:
                raise ValueError(f"维度 {dim} 分数超出范围: {score}")
            dimensions[dim] = {
                "score": score,
                "max_score": max_scores[dim]
            }
            dimensions_sum += score

        # 根据原始评分数据判断分制,计算总分
        use_10_point_scale = False
        if request.original_score_data and "total_score" in request.original_score_data:
            if request.original_score_data["total_score"] <= 10:
                use_10_point_scale = True

        if use_10_point_scale:
            total_score = int((dimensions_sum / 100) * 10)
        else:
            total_score = int((dimensions_sum / 100) * 40)

        return {
            "success": True,
            "score_data": {
                "total_score": total_score,
                "dimensions": dimensions
            },
            "raw_response": ai_response
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI返回格式错误: {str(e)}",
            "raw_response": ai_response
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI评分失败: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
