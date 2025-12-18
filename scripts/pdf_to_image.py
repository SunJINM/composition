import os
from pdf2image import convert_from_path
from PIL import Image
from typing import List, Optional


def pdf_to_images(
    pdf_path: str,
    output_dir: str = "pdf_images",
    img_format: str = "png",
    dpi: int = 300,
    poppler_path: Optional[str] = None,
    start_page: int = 1,
    end_page: Optional[int] = None
) -> List[str]:
    """
    将PDF文件转换为图片
    
    参数:
        pdf_path: 本地PDF文件路径（绝对/相对路径）
        output_dir: 图片输出目录（默认：pdf_images）
        img_format: 输出图片格式（支持png/jpg/jpeg等，默认png）
        dpi: 图片分辨率（默认300，数值越高越清晰）
        poppler_path: Poppler的bin目录路径（Windows需指定，其他系统可省略）
        start_page: 起始转换页码（默认1）
        end_page: 结束转换页码（默认None，转换全部）
    返回:
        生成的图片文件路径列表
    """
    # 校验PDF文件是否存在
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在：{pdf_path}")
    
    # 校验输出格式
    valid_formats = ["png", "jpg", "jpeg", "bmp", "tiff"]
    if img_format.lower() not in valid_formats:
        raise ValueError(f"不支持的图片格式！支持格式：{valid_formats}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 转换PDF为PIL Image对象列表
        images = convert_from_path(
            pdf_path=pdf_path,
            dpi=dpi,
            poppler_path=poppler_path,
            first_page=start_page,
            last_page=end_page,
            fmt=img_format.lower()
        )
        
        # 保存图片并记录路径
        img_paths = []
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        for idx, img in enumerate(images, start=start_page):
            # 构建图片文件名（例如：test_pdf_1.png）
            img_name = f"{pdf_name}_{idx}.{img_format.lower()}"
            img_path = os.path.join(output_dir, img_name)
            
            # 保存图片（处理JPG格式的RGB转换）
            if img_format.lower() in ["jpg", "jpeg"] and img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(img_path, quality=95)  # JPG质量95（1-100）
            img_paths.append(img_path)
        
        print(f"转换完成！共生成 {len(img_paths)} 张图片，保存至：{output_dir}")
        return img_paths
    
    except Exception as e:
        raise RuntimeError(f"PDF转换失败：{str(e)}")


# 示例调用
if __name__ == "__main__":
    # Windows用户需指定poppler_path（示例路径，需替换为自己的解压路径）
    POPPLER_PATH = r"D:\software\poppler-25.12.0\Library\bin"
    
    try:
        # 转换示例（替换为你的PDF路径）
        image_paths = pdf_to_images(
            pdf_path="班雨鹭作文分析报告.pdf",
            output_dir="my_pdf_images",
            img_format="jpg",
            dpi=300,
            poppler_path=POPPLER_PATH,  # Linux/macOS可注释此行
            start_page=1,
        )
        print("生成的图片路径：", image_paths)
    except Exception as e:
        print(f"错误：{e}")