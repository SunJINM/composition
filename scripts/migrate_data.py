"""
数据迁移脚本
从JSON文件迁移数据到MySQL数据库
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.models import Batch, Essay, Prompt, Grade, Genre


def extract_grade_from_text(text):
    """
    从文本中提取年级
    返回grade_id (1=7年级, 2=8年级, 3=9年级)
    """
    if not text:
        return None

    patterns = {
        1: [r'7年级', r'七年级', r'初一'],
        2: [r'8年级', r'八年级', r'初二'],
        3: [r'9年级', r'九年级', r'初三']
    }

    for grade_id, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, text):
                return grade_id

    return None


def migrate_batches(db):
    """
    迁移批次数据
    从 essays_require.json → composition_batches
    """
    print("\n开始迁移批次数据...")

    # 读取JSON文件
    require_file = project_root / "data" / "essays_require.json"
    if not require_file.exists():
        print(f"警告: 文件不存在 {require_file}")
        return 0

    with open(require_file, 'r', encoding='utf-8') as f:
        requirements = json.load(f)

    migrated_count = 0
    for req in requirements:
        directory_name = req.get('directory_name')
        if not directory_name:
            continue

        # 检查是否已存在
        existing = db.query(Batch).filter_by(directory_name=directory_name).first()
        if existing:
            print(f"  批次已存在: {directory_name}")
            continue

        # 提取年级
        essay_requirement = req.get('essay_requirement', '')
        grade_id = extract_grade_from_text(essay_requirement)

        # 创建批次记录
        batch = Batch(
            directory_name=directory_name,
            essay_title=req.get('essay_title', ''),
            essay_requirement=essay_requirement,
            grade_id=grade_id,
            essay_count=0,  # 稍后更新
            status=1
        )

        db.add(batch)
        migrated_count += 1

    db.commit()
    print(f"成功迁移 {migrated_count} 个批次")
    return migrated_count


def migrate_essays(db):
    """
    迁移作文数据
    从 essays_data.json → composition_essays
    """
    print("\n开始迁移作文数据...")

    # 读取JSON文件
    essays_file = project_root / "data" / "essays_data.json"
    if not essays_file.exists():
        print(f"警告: 文件不存在 {essays_file}")
        return 0

    with open(essays_file, 'r', encoding='utf-8') as f:
        essays = json.load(f)

    migrated_count = 0
    skipped_count = 0

    for essay_data in essays:
        # 根据directory_name查找批次
        directory_name = essay_data.get('directory_name')
        if not directory_name:
            skipped_count += 1
            continue

        batch = db.query(Batch).filter_by(directory_name=directory_name).first()
        if not batch:
            print(f"  警告: 批次不存在 {directory_name}")
            skipped_count += 1
            continue

        # 判断分制
        original_score_data = essay_data.get('score_data', {})
        total_score = original_score_data.get('total_score', 0) if original_score_data else 0
        score_system = 10 if total_score and total_score <= 10 else 40

        # 计算字数
        essay_content = essay_data.get('essay_content', '')
        word_count = len(essay_content)

        # 创建作文记录
        essay = Essay(
            batch_id=batch.id,
            student_name=essay_data.get('student_name'),
            essay_content=essay_content,
            essay_image_path=essay_data.get('essay_image_path'),
            analysis_report_path=essay_data.get('analysis_report_path'),
            word_count=word_count,
            score_system=score_system,
            original_score=total_score,
            original_score_data=json.dumps(original_score_data, ensure_ascii=False) if original_score_data else None,
            status=1
        )

        db.add(essay)
        migrated_count += 1

    db.commit()
    print(f"成功迁移 {migrated_count} 篇作文")
    if skipped_count > 0:
        print(f"跳过 {skipped_count} 篇作文(批次不存在)")

    return migrated_count


def update_batch_essay_count(db):
    """更新每个批次的作文数量"""
    print("\n更新批次作文数量...")

    batches = db.query(Batch).all()
    for batch in batches:
        essay_count = db.query(Essay).filter_by(batch_id=batch.id).count()
        batch.essay_count = essay_count

    db.commit()
    print(f"成功更新 {len(batches)} 个批次的作文数量")


def migrate_prompts(db):
    """
    迁移提示词数据
    从 analyze_prompts.json 和 score_prompts.json → composition_prompts
    """
    print("\n开始迁移提示词数据...")

    # 默认分配到7年级+记叙文
    default_grade_id = 1  # 7年级
    default_genre_id = 1  # 记叙文

    migrated_count = 0

    # 1. 迁移评价提示词
    analyze_file = project_root / "data" / "analyze_prompts.json"
    if analyze_file.exists():
        with open(analyze_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for prompt_data in data.get('prompts', []):
            prompt = Prompt(
                grade_id=default_grade_id,
                genre_id=default_genre_id,
                prompt_type='analyze',
                version_name=prompt_data.get('version', 'v1.0'),
                prompt_content=prompt_data.get('prompt', ''),
                is_default=1 if prompt_data.get('is_default', False) else 0,
                status=1
            )
            db.add(prompt)
            migrated_count += 1

    # 2. 迁移评分提示词
    score_file = project_root / "data" / "score_prompts.json"
    if score_file.exists():
        with open(score_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for prompt_data in data.get('prompts', []):
            prompt = Prompt(
                grade_id=default_grade_id,
                genre_id=default_genre_id,
                prompt_type='score',
                version_name=prompt_data.get('version', 'v1.0'),
                prompt_content=prompt_data.get('prompt', ''),
                is_default=1 if prompt_data.get('is_default', False) else 0,
                status=1
            )
            db.add(prompt)
            migrated_count += 1

    db.commit()
    print(f"成功迁移 {migrated_count} 条提示词")
    return migrated_count


def verify_migration(db):
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("迁移验证")
    print("=" * 60)

    # 检查批次数量
    batch_count = db.query(Batch).count()
    print(f"批次数量: {batch_count} (期望: 17)")

    # 检查作文总数
    essay_count = db.query(Essay).count()
    print(f"作文总数: {essay_count} (期望: 1082)")

    # 检查分制分布
    score_10 = db.query(Essay).filter_by(score_system=10).count()
    score_40 = db.query(Essay).filter_by(score_system=40).count()
    print(f"10分制作文: {score_10}")
    print(f"40分制作文: {score_40}")

    # 检查提示词数量
    prompt_count = db.query(Prompt).count()
    analyze_count = db.query(Prompt).filter_by(prompt_type='analyze').count()
    score_count = db.query(Prompt).filter_by(prompt_type='score').count()
    print(f"提示词总数: {prompt_count}")
    print(f"  评价提示词: {analyze_count}")
    print(f"  评分提示词: {score_count}")

    # 显示每个批次的作文数量
    print("\n各批次作文数量:")
    batches = db.query(Batch).all()
    for batch in batches[:5]:  # 只显示前5个
        print(f"  {batch.directory_name[:20]}...: {batch.essay_count}篇")
    if len(batches) > 5:
        print(f"  ... 还有 {len(batches) - 5} 个批次")


def main():
    """主函数"""
    print("=" * 60)
    print("作文评分系统 - 数据迁移")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1. 迁移批次
        migrate_batches(db)

        # 2. 迁移作文
        migrate_essays(db)

        # 3. 更新批次作文数量
        update_batch_essay_count(db)

        # 4. 迁移提示词
        migrate_prompts(db)

        # 5. 验证迁移结果
        verify_migration(db)

        print("\n" + "=" * 60)
        print("数据迁移完成!")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"\n数据迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
