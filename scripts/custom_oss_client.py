import base64
import datetime
import logging
import time
import string
import random
from typing import Optional
from urllib.parse import urlparse
from botocore.config import Config

import boto3


def generate_random_string(length):
    """生成随机字符串"""
    all_characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choice(all_characters) for _ in range(length))
    return random_string


class CustomOSSClient:
    def __init__(self, bucket_name: Optional[str] = None):
        aws_access_key_id, aws_secret_access_key, endpoint_url, _bucket_name = self.__iniconfig()
        if bucket_name:
            _bucket_name = bucket_name
        self.access_key_id = aws_access_key_id
        self.access_key_secret = aws_secret_access_key
        self.endpoint = endpoint_url
        self.bucket_name = _bucket_name

    def get_client(self):
        config = Config(
            signature_version='s3',
        )
        return boto3.client(
            service_name='s3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            endpoint_url=self.endpoint,
            config=config,
        )

    def upload_file_random_path(self, bytes_content, file_suffix_no_dot="mp3") -> str:
        """上传文件到随机路径"""
        file_name = str(int(round(time.time() * 1000))) + "-" + generate_random_string(6)
        today = datetime.datetime.today()
        year = today.year
        month = today.month
        # 在 S3 中的存储路径
        object_name = f"essays/{year}{month}/{file_name}.{file_suffix_no_dot}"
        return self.upload_file(object_name, bytes_content)

    def upload_file(self, file_path, bytes_content, content_type=None, content_disposition='inline') -> str:
        """上传文件到指定路径

        Args:
            file_path: S3中的文件路径
            bytes_content: 文件内容(字节)
            content_type: MIME类型,如果不指定则根据文件后缀自动判断
            content_disposition: inline(在线预览) 或 attachment(下载)
        """
        s3_client = self.get_client()

        # 如果未指定content_type,根据文件后缀自动判断
        if content_type is None:
            content_type = self._get_content_type(file_path)

        try:
            # 上传文件
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=bytes_content,
                ContentType=content_type,
                ContentDisposition=content_disposition  # inline支持浏览器预览
            )
            logging.info(f"文件已成功上传到 S3 桶 {self.bucket_name},路径为 {file_path}")
            logging.info(f"Content-Type: {content_type}, Content-Disposition: {content_disposition}")
            address = f'{self.endpoint}/{self.bucket_name}/{file_path}'
            return address
        except Exception as e:
            logging.error(f"上传时发生错误: {e}")
            raise

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """根据文件后缀返回Content-Type"""
        content_type_map = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'mp3': 'audio/mpeg',
            'mp4': 'video/mp4',
            'txt': 'text/plain',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'json': 'application/json',
            'xml': 'application/xml',
        }

        suffix = file_path.split('.')[-1].lower()
        return content_type_map.get(suffix, 'application/octet-stream')

    def download_file(self, url):
        """从OSS下载文件"""
        bucket_name, s3_key = self.parse_s3_url(url)
        s3_client = self.get_client()
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            file_content = response['Body'].read()
            logging.info(f"文件内容:{file_content[:100]}...")
            return file_content
        except Exception as e:
            logging.error(f"获取文件失败: {e}")
            raise

    def download_base64_file(self, url):
        """下载文件并转为base64"""
        bytes_content = self.download_file(url)
        return base64.b64encode(bytes_content).decode('utf-8')

    @staticmethod
    def parse_s3_url(url):
        """解析S3 URL"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)

        if len(path_parts) == 2:
            bucket_name = path_parts[0]
            key = path_parts[1]
            return bucket_name, key
        else:
            raise ValueError("Invalid S3 URL format")

    @staticmethod
    def __iniconfig():
        """配置信息"""
        aws_access_key_id = "I0L0MJVLE5XHWJY07L2N"
        aws_secret_access_key = "WmjOlTdUTT1m5lc83O9pAh1FTu2PGKJyamuKGhIO"
        endpoint_url = "https://obs-prod.xxt.cn"
        bucket_name = "ai-chat"
        return aws_access_key_id, aws_secret_access_key, endpoint_url, bucket_name


if __name__ == '__main__':
    oss = CustomOSSClient()
    # 测试上传
    with open(r'test.txt', 'r', encoding='utf-8') as f:
        bytes_content = f.read()
        result = oss.upload_file("test/prompt.txt", bytes(bytes_content, encoding="utf8"))
        print(f"上传结果: {result}")
