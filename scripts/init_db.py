"""
数据库初始化脚本
创建所有表并插入初始数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine, Base, SessionLocal
from app.models import Grade, Genre
from datetime import datetime


def create_tables():
    """创建所有数据库表"""
    print("开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成!")


def init_grades():
    """初始化年级数据"""
    print("初始化年级数据...")
    db = SessionLocal()
    try:
        # 检查是否已存在数据
        if db.query(Grade).count() > 0:
            print("年级数据已存在,跳过初始化")
            return

        grades = [
            Grade(
                grade_name='7年级',
                grade_code='grade_7',
                grade_level='初中',
                sort_order=7,
                status=1
            ),
            Grade(
                grade_name='8年级',
                grade_code='grade_8',
                grade_level='初中',
                sort_order=8,
                status=1
            ),
            Grade(
                grade_name='9年级',
                grade_code='grade_9',
                grade_level='初中',
                sort_order=9,
                status=1
            )
        ]

        db.add_all(grades)
        db.commit()
        print(f"成功插入 {len(grades)} 条年级数据")
    except Exception as e:
        db.rollback()
        print(f"初始化年级数据失败: {str(e)}")
        raise
    finally:
        db.close()


def init_genres():
    """初始化文体数据"""
    print("初始化文体数据...")
    db = SessionLocal()
    try:
        # 检查是否已存在数据
        if db.query(Genre).count() > 0:
            print("文体数据已存在,跳过初始化")
            return

        genres = [
            Genre(
                genre_name='记叙文',
                genre_code='narrative',
                description='以记人、叙事、写景、状物为主的文章',
                sort_order=1,
                status=1
            ),
            Genre(
                genre_name='议论文',
                genre_code='argumentative',
                description='以议论为主要表达方式的文章',
                sort_order=2,
                status=1
            )
        ]

        db.add_all(genres)
        db.commit()
        print(f"成功插入 {len(genres)} 条文体数据")
    except Exception as e:
        db.rollback()
        print(f"初始化文体数据失败: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("作文评分系统 - 数据库初始化")
    print("=" * 60)

    try:
        # 1. 创建表
        create_tables()

        # 2. 插入初始数据
        init_grades()
        init_genres()

        print("=" * 60)
        print("数据库初始化完成!")
        print("=" * 60)
    except Exception as e:
        print(f"\n数据库初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
