import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from pdf2image import convert_from_path
import requests
from PIL import Image
import io


class EssayExtractor:
    """学生作文提取器"""

    def __init__(
        self,
        base_dir: str = "蜜蜂家校答卷&分析报告",
        output_json: str = "essays_data.json",
        poppler_path: Optional[str] = None
    ):
        """
        初始化提取器

        Args:
            base_dir: 数据根目录
            output_json: 输出JSON文件路径
            poppler_path: Poppler bin目录路径(Windows需要)
        """
        self.base_dir = Path(base_dir)
        self.output_json = output_json
        self.poppler_path = poppler_path

        # 视觉模型配置
        self.api_config = {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model_name": "ep-20251025164648-d66ns",  # doubao-seed-1.6-vision
            "api_key": "14ebfc74-500c-46d5-a58b-61ac61341018"
        }

        self.results: List[Dict] = []
        self.processed_set: set = set()  # 记录已处理的(目录名, 学生名)

        # 加载已有进度
        self._load_progress()

    def _load_progress(self) -> None:
        """加载已有的处理进度"""
        if os.path.exists(self.output_json):
            try:
                with open(self.output_json, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)

                # 构建已处理集合
                for item in self.results:
                    dir_name = item.get("directory_name", "")
                    student_name = item.get("student_name", "")
                    if dir_name and student_name:
                        self.processed_set.add((dir_name, student_name))

                print(f"📥 加载已有进度: {len(self.results)} 份作文")
            except Exception as e:
                print(f"⚠️ 加载进度失败: {e}, 将从头开始")
                self.results = []
                self.processed_set = set()

    def _save_single_result(self, result: Dict) -> None:
        """保存单个结果到JSON文件"""
        self.results.append(result)

        # 立即写入文件
        try:
            with open(self.output_json, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"    ⚠️ 保存失败: {e}")

    def image_to_base64(self, image_path: str) -> str:
        """将图片转换为base64编码"""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def call_vision_model(self, image_path: str, prompt: str) -> str:
        """
        调用视觉模型

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            模型返回的文本
        """
        # 将图片转为base64
        image_base64 = self.image_to_base64(image_path)

        # 构建请求
        url = f"{self.api_config['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_config['api_key']}"
        }

        payload = {
            "model": self.api_config["model_name"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "extra_body": {
                "thinking": {
                    "type": "enabled"  # 使用深度思考能力
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  ⚠️ 调用视觉模型失败: {e}")
            return ""

    def extract_essay_content(self, essay_image_path: str) -> str:
        """
        从作文答卷图片提取作文内容

        Args:
            essay_image_path: 作文答卷图片路径

        Returns:
            提取的作文内容
        """
        prompt = """请提取图片中的学生作文内容。要求：
1. 完整提取所有文字内容，不要遗漏
2. 保留原始内容，不要进行任何纠正、改写或优化
3. 按照原文的段落结构输出
4. 如果有标题，请包含标题
5. 只输出作文正文内容，不要添加任何说明或注释"""

        return self.call_vision_model(essay_image_path, prompt)

    def extract_score_from_report(self, report_pdf_path: str) -> Optional[Dict]:
        """
        从分析报告PDF提取分数(包括总分和5个维度分数)

        Args:
            report_pdf_path: 分析报告PDF路径

        Returns:
            提取的分数字典,提取失败返回None
            格式: {
                "total_score": 总分,
                "dimensions": {
                    "中心立意": {"score": 得分, "max_score": 20},
                    "语言表达": {"score": 得分, "max_score": 25},
                    "篇章结构": {"score": 得分, "max_score": 15},
                    "文章选材": {"score": 得分, "max_score": 15},
                    "内容情感": {"score": 得分, "max_score": 25}
                }
            }
        """
        # 固定的各维度最高分
        MAX_SCORES = {
            "中心立意": 20,
            "语言表达": 25,
            "篇章结构": 15,
            "文章选材": 15,
            "内容情感": 25
        }

        try:
            # 将PDF转换为图片(转换所有页)
            images = convert_from_path(
                pdf_path=str(report_pdf_path),
                dpi=300,
                poppler_path=self.poppler_path
            )

            if not images or len(images) < 2:
                print(f"  ⚠️ PDF转图片失败或页数不足")
                return None

            # 取第2张图片(索引为1)
            temp_img_path = "temp_report_page2.jpg"
            if images[1].mode == "RGBA":
                images[1] = images[1].convert("RGB")
            images[1].save(temp_img_path, quality=95)

            # 第一次提取: 只提取总分(红色大字)
            prompt_total = """请从这张作文分析报告图片中提取总分。

要求:
1. 找到图片中最显眼的红色大字数字,这是总分
2. 只输出这个数字,不要包含任何其他文字或符号

禁止：
1. 禁止使用雷达图中的各维度分数进行相加计算。

示例输出:
36"""

            total_score_text = self.call_vision_model(temp_img_path, prompt_total)

            # 解析总分
            try:
                total_score = float(total_score_text.strip())
            except ValueError:
                print(f"  ⚠️ 无法解析总分: {total_score_text}")
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                return None

            # 第二次提取: 只提取各维度分数
            prompt_dimensions = """请从这张作文分析报告图片中提取5个维度的得分。

要求:
1. 从雷达图或评分表中提取以下5个维度的得分:
   - 中心立意
   - 语言表达
   - 篇章结构
   - 文章选材
   - 内容情感

2. 输出格式为JSON字符串(严格按照此格式,不要添加任何其他文字):
{
  "中心立意": 得分数字,
  "语言表达": 得分数字,
  "篇章结构": 得分数字,
  "文章选材": 得分数字,
  "内容情感": 得分数字
}

示例输出:
{
  "中心立意": 16,
  "语言表达": 13,
  "篇章结构": 12,
  "文章选材": 20,
  "内容情感": 19
}

注意: 只输出JSON字符串,不要包含任何解释说明"""

            dimensions_text = self.call_vision_model(temp_img_path, prompt_dimensions)

            # 清理临时文件
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

            # 解析维度分数
            try:
                # 提取JSON部分(去除可能的markdown代码块标记)
                dimensions_text = dimensions_text.strip()
                if dimensions_text.startswith("```"):
                    dimensions_text = dimensions_text.split("```")[1]
                    if dimensions_text.startswith("json"):
                        dimensions_text = dimensions_text[4:]
                dimensions_text = dimensions_text.strip()

                dim_scores = json.loads(dimensions_text)

                # 使用固定的最高分构建维度数据
                dimensions = {}
                for dim_name, max_score in MAX_SCORES.items():
                    score = dim_scores.get(dim_name)
                    if score is None:
                        print(f"  ⚠️ 缺少维度分数: {dim_name}")
                        return None
                    dimensions[dim_name] = {
                        "score": score,
                        "max_score": max_score
                    }

                return {
                    "total_score": total_score,
                    "dimensions": dimensions
                }

            except (json.JSONDecodeError, ValueError) as e:
                print(f"  ⚠️ 无法解析维度分数: {dimensions_text[:100]}... 错误: {e}")
                return None

        except Exception as e:
            print(f"  ⚠️ 处理分析报告失败: {e}")
            return None

    def process_student(self, student_dir: Path) -> None:
        """
        处理单个学生目录

        Args:
            student_dir: 学生目录路径
        """
        dir_name = student_dir.name

        # 检查作文分析报告目录是否存在
        report_dir = student_dir / "作文分析报告"
        if not report_dir.exists():
            print(f"⏭️ 跳过 {dir_name}: 无作文分析报告目录")
            return

        # 获取所有作文答卷图片
        essay_images = list(student_dir.glob("*作文答卷.jpg"))
        if not essay_images:
            print(f"⏭️ 跳过 {dir_name}: 无作文答卷")
            return

        print(f"\n📂 处理目录: {dir_name}")
        print(f"  发现 {len(essay_images)} 份作文答卷")

        for essay_img in essay_images:
            # 提取学生姓名
            student_name = essay_img.stem.replace("作文答卷", "")

            # 检查是否已处理过
            if (dir_name, student_name) in self.processed_set:
                print(f"  ⏭️ 跳过 {student_name}: 已处理过")
                continue

            # 查找对应的分析报告
            report_pdf = report_dir / f"{student_name}作文分析报告.pdf"
            if not report_pdf.exists():
                print(f"  ⏭️ 跳过 {student_name}: 无分析报告")
                continue

            print(f"  ✅ 处理学生: {student_name}")

            # 提取作文内容
            print(f"    🔍 提取作文内容...")
            essay_content = self.extract_essay_content(str(essay_img))

            if not essay_content:
                print(f"    ⚠️ 作文内容提取失败，跳过")
                continue

            # 提取分数
            print(f"    📊 提取分数...")
            score_data = self.extract_score_from_report(str(report_pdf))

            # 记录结果
            result = {
                "directory_name": dir_name,
                "student_name": student_name,
                "essay_image_path": str(essay_img.absolute()),
                "essay_content": essay_content,
                "score_data": score_data,  # 包含总分和维度分数
                "analysis_report_path": str(report_pdf.absolute())
            }

            # 立即保存到文件
            self._save_single_result(result)
            self.processed_set.add((dir_name, student_name))

            # 显示分数信息
            if score_data:
                total = score_data.get("total_score", "未知")
                dimensions = score_data.get("dimensions", {})
                print(f"    💾 完成并保存 - 总分: {total}")

                # 动态显示各维度分数(使用提取的满分)
                dim_info = []
                for dim_name in ["中心立意", "语言表达", "篇章结构", "文章选材", "内容情感"]:
                    dim_data = dimensions.get(dim_name, {})
                    score = dim_data.get('score', '?')
                    max_score = dim_data.get('max_score', '?')
                    dim_info.append(f"{dim_name}{score}/{max_score}")

                print(f"       维度: {' | '.join(dim_info)}")
            else:
                print(f"    💾 完成并保存 - 得分: 未提取到")

    def run(self) -> None:
        """运行提取流程"""
        print("🚀 开始提取学生作文数据...")
        print(f"📁 数据目录: {self.base_dir.absolute()}")

        if not self.base_dir.exists():
            print(f"❌ 错误: 数据目录不存在")
            return

        # 获取所有学生目录
        student_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        print(f"📊 找到 {len(student_dirs)} 个学生目录\n")

        # 处理每个学生目录
        for student_dir in student_dirs:
            try:
                self.process_student(student_dir)
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断，保存当前进度...")
                print(f"📊 已处理 {len(self.results)} 份作文")
                print(f"💾 进度已保存到: {self.output_json}")
                print("💡 下次运行将从中断处继续")
                return
            except Exception as e:
                print(f"❌ 处理目录 {student_dir.name} 时出错: {e}")
                print("⏭️ 继续处理下一个目录...")
                continue

        print(f"\n✅ 完成! 共处理 {len(self.results)} 份作文")
        print(f"📄 结果已保存到: {self.output_json}")


if __name__ == "__main__":
    # Windows用户需指定poppler路径
    POPPLER_PATH = r"D:\software\poppler-25.12.0\Library\bin"

    extractor = EssayExtractor(
        base_dir="蜜蜂家校答卷&分析报告",
        output_json="essays_data.json",
        poppler_path=POPPLER_PATH
    )

    extractor.run()
