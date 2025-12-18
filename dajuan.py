import requests
import os
import re
from urllib.parse import urlparse, parse_qs

def download_papers(api_url):
    """
    根据API URL下载所有学生的作文答卷
    
    参数:
        api_url: 完整的paper_list API请求地址
    """
    # 1. 从URL中提取homework_id和token
    parsed_url = urlparse(api_url)
    params = parse_qs(parsed_url.query)
    
    homework_id = params.get('homework_id', ['unknown'])[0]
    token = params.get('token', [''])[0]
    
    # 2. 创建目录
    output_dir = homework_id
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 3. 获取试卷列表
    response = requests.get(api_url)
    data = response.json()
    
    if data['ret'] != 0:
        print(f"获取试卷列表失败: {data.get('err', '未知错误')}")
        return
    
    detail_list = data['data']['detail_list']
    total = len(detail_list)
    
    print(f"共找到 {total} 份答卷，开始下载...")
    
    # 4. 下载每个学生的图片
    for idx, student in enumerate(detail_list, 1):
        child_name = student['child_name']
        
        if not student.get('media') or len(student['media']) == 0:
            print(f"[{idx}/{total}] {child_name} - 没有图片")
            continue
        
        # 获取图片URL
        image_url = student['media'][0]['url']
        
        # 构建下载链接
        download_url = f"https://xy-api.mifengjiaoyu.com/teach/download_file?token={token}&file_name={image_url}&link={image_url}&angle=0"
        
        # 文件名
        filename = f"{child_name}作文答卷.jpg"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 下载图片
            img_response = requests.get(download_url)
            if img_response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                print(f"[{idx}/{total}] {child_name} - 下载成功")
            else:
                print(f"[{idx}/{total}] {child_name} - 下载失败 (状态码: {img_response.status_code})")
        except Exception as e:
            print(f"[{idx}/{total}] {child_name} - 下载出错: {str(e)}")
    
    print(f"\n下载完成！文件保存在目录: {output_dir}")

if __name__ == "__main__":
    # 使用示例
    api_url = input("请输入完整的API请求地址: ").strip()
    download_papers(api_url)