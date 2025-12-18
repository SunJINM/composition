import json
import os
from pathlib import Path

def convert_abs_to_rel_path(abs_path: str, base_dir: str) -> str:
    """
    将绝对路径转换为相对路径，并统一路径分隔符为 /
    :param abs_path: 原始绝对路径
    :param base_dir: 基准目录（相对路径的根目录）
    :return: 兼容跨平台的相对路径
    """
    # 统一解析路径（自动处理 Windows/Linux 分隔符）
    abs_path_obj = Path(abs_path)
    base_dir_obj = Path(base_dir).resolve()
    
    # 计算相对路径
    rel_path_obj = abs_path_obj.relative_to(base_dir_obj)
    
    # 转换为字符串，统一使用 / 作为分隔符（跨平台兼容）
    rel_path = str(rel_path_obj).replace(os.sep, '/')
    return rel_path

def process_essay_data(json_file_path: str, base_dir: str):
    """
    处理作文数据 JSON 文件，替换路径为相对路径
    :param json_file_path: essays_data.json 文件路径
    :param base_dir: 基准目录（原始绝对路径的根目录）
    """
    # 读取 JSON 文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        essay_data = json.load(f)
    
    # 遍历每个学生数据，替换路径
    for student in essay_data:
        # 处理作文图片路径
        if 'essay_image_path' in student and student['essay_image_path']:
            student['essay_image_path'] = convert_abs_to_rel_path(
                student['essay_image_path'], base_dir
            )
        # 处理分析报告路径
        if 'analysis_report_path' in student and student['analysis_report_path']:
            student['analysis_report_path'] = convert_abs_to_rel_path(
                student['analysis_report_path'], base_dir
            )
    
    # 将修改后的数据写回 JSON 文件（也可另存为新文件）
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(essay_data, f, ensure_ascii=False, indent=2)
    
    print(f"路径转换完成！已修改 {json_file_path}")
    print("转换规则：")
    print(f"  基准目录：{base_dir}")
    print(f"  路径分隔符：统一为 /（兼容 Windows/Linux）")

if __name__ == "__main__":
    # -------------------------- 配置项 --------------------------
    # JSON 文件路径（当前脚本同目录下的 essays_data.json）
    JSON_FILE = "essays_data.json"
    # 原始绝对路径的基准目录（根据你的实际路径修改！）
    # 示例：原始路径是 D:\WorkProjects\learn\mifeng\蜜蜂家校答卷&分析报告\...
    #      基准目录就是 D:\WorkProjects\learn\mifeng\蜜蜂家校答卷&分析报告
    BASE_DIR = r"D:\WorkProjects\learn\mifeng"
    # -------------------------------------------------------------

    # 验证文件和目录存在性
    if not os.path.exists(JSON_FILE):
        raise FileNotFoundError(f"未找到 JSON 文件：{JSON_FILE}")
    if not os.path.exists(BASE_DIR):
        raise NotADirectoryError(f"基准目录不存在：{BASE_DIR}")
    
    # 执行路径转换
    process_essay_data(JSON_FILE, BASE_DIR)