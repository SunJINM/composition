"""
FastAPI主应用
整合所有API路由
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.api import users, batches, essays, evaluations, prompts
from app.utils import logger
from app.config import settings

# 创建FastAPI应用实例
app = FastAPI(
    title="作文评分系统API",
    description="基于AI的作文评价和评分系统",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(batches.router, prefix="/api/batches", tags=["批次管理"])
app.include_router(essays.router, prefix="/api/essays", tags=["作文管理"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["评价评分"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["提示词管理"])

# 挂载静态文件目录
project_root = Path(__file__).parent.parent
static_path = project_root / "static"
templates_path = project_root / "templates"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# 首页路由
@app.get("/", summary="首页")
async def index():
    """返回主页HTML"""
    index_file = templates_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "作文评分系统API", "version": "3.0.0"}


# 首页路由 - 兼容 /index.html 访问
@app.get("/index.html", summary="首页(兼容路径)")
async def index_html():
    """返回主页HTML - 兼容直接访问index.html的情况"""
    index_file = templates_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "作文评分系统API", "version": "3.0.0"}


# 登录页面
@app.get("/login.html", summary="登录页面")
async def login_page():
    """返回登录页面HTML"""
    login_file = templates_path / "login.html"
    if login_file.exists():
        return FileResponse(str(login_file))
    return {"error": "页面不存在"}


# AI评分页面
@app.get("/ai-scoring", summary="AI评分页面")
async def ai_scoring_page():
    """返回AI评分页面HTML"""
    scoring_file = templates_path / "ai-scoring.html"
    if scoring_file.exists():
        return FileResponse(str(scoring_file))
    return {"error": "页面不存在"}


# AI评分页面 - 兼容 .html 后缀
@app.get("/ai-scoring.html", summary="AI评分页面(兼容路径)")
async def ai_scoring_page_html():
    """返回AI评分页面HTML - 兼容.html后缀访问"""
    scoring_file = templates_path / "ai-scoring.html"
    if scoring_file.exists():
        return FileResponse(str(scoring_file))
    return {"error": "页面不存在"}


# 提示词管理页面
@app.get("/prompts-management.html", summary="提示词管理页面")
async def prompts_management_page():
    """返回提示词管理页面HTML"""
    prompts_file = templates_path / "prompts-management.html"
    if prompts_file.exists():
        return FileResponse(str(prompts_file))
    return {"error": "页面不存在"}


# 健康检查
@app.get("/health", summary="健康检查")
async def health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "service": "作文评分系统"
    }


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("=" * 60)
    logger.info("作文评分系统启动")
    logger.info(f"环境: {'开发' if settings.APP_DEBUG else '生产'}")
    logger.info(f"数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"API文档: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    logger.info("=" * 60)


# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("作文评分系统关闭")
