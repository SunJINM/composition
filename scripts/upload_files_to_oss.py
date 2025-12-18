import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from custom_oss_client import CustomOSSClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FileUploader:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.oss_client = CustomOSSClient()
        self.uploaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def get_file_suffix(self, file_path: str) -> str:
        """获取文件后缀名(不含点)"""
        return Path(file_path).suffix.lstrip('.')

    def is_local_path(self, path: str) -> bool:
        """判断是否为本地路径"""
        if not path:
            return False
        # 检查是否为本地文件路径(Windows或Unix路径)
        return (
            path.startswith('/') or
            path.startswith('./') or
            path.startswith('../') or
            (len(path) > 1 and path[1] == ':') or  # Windows路径如 D:\
            not path.startswith('http')
        )

    def upload_local_file(self, local_path: str) -> str:
        """上传本地文件到OSS"""
        try:
            # 检查文件是否存在
            if not os.path.exists(local_path):
                logging.warning(f"文件不存在: {local_path}")
                self.failed_count += 1
                return local_path

            # 读取文件内容
            with open(local_path, 'rb') as f:
                file_content = f.read()

            # 获取文件后缀
            file_suffix = self.get_file_suffix(local_path)

            # 上传文件并获取OSS地址
            oss_url = self.oss_client.upload_file_random_path(
                bytes_content=file_content,
                file_suffix_no_dot=file_suffix
            )

            logging.info(f"成功上传: {local_path} -> {oss_url}")
            self.uploaded_count += 1
            return oss_url

        except Exception as e:
            logging.error(f"上传失败 {local_path}: {e}")
            self.failed_count += 1
            return local_path

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个数据项"""
        # 处理作文答卷图片路径
        if 'essay_image_path' in item:
            image_path = item['essay_image_path']
            if self.is_local_path(image_path):
                logging.info(f"处理图片: {image_path}")
                item['essay_image_path'] = self.upload_local_file(image_path)
            else:
                logging.info(f"跳过远程路径: {image_path}")
                self.skipped_count += 1

        # 处理作文分析报告PDF路径
        if 'analysis_report_path' in item:
            report_path = item['analysis_report_path']
            if self.is_local_path(report_path):
                logging.info(f"处理报告: {report_path}")
                item['analysis_report_path'] = self.upload_local_file(report_path)
            else:
                logging.info(f"跳过远程路径: {report_path}")
                self.skipped_count += 1

        return item

    def process_json(self):
        """处理JSON文件"""
        logging.info(f"开始处理文件: {self.json_path}")

        # 读取JSON文件
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"读取JSON文件失败: {e}")
            return

        # 确保data是列表
        if not isinstance(data, list):
            logging.error("JSON文件格式错误,应该是一个列表")
            return

        # 处理每个数据项
        total_items = len(data)
        logging.info(f"共有 {total_items} 条数据需要处理")

        for index, item in enumerate(data, 1):
            logging.info(f"\n处理进度: {index}/{total_items}")
            data[index - 1] = self.process_item(item)

        # 备份原文件
        backup_path = self.json_path + '.backup'
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"原文件已备份到: {backup_path}")
        except Exception as e:
            logging.error(f"备份文件失败: {e}")
            return

        # 保存更新后的JSON文件
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"\n更新后的文件已保存")
        except Exception as e:
            logging.error(f"保存文件失败: {e}")
            return

        # 输出统计信息
        logging.info(f"\n=== 处理完成 ===")
        logging.info(f"成功上传: {self.uploaded_count} 个文件")
        logging.info(f"上传失败: {self.failed_count} 个文件")
        logging.info(f"跳过处理: {self.skipped_count} 个文件")


def main():
    # JSON文件路径
    json_file_path = r"d:\VSCodeProjects\learn\mifeng\essays_data.json"

    # 创建上传器并执行
    uploader = FileUploader(json_file_path)
    uploader.process_json()


if __name__ == '__main__':
    main()
