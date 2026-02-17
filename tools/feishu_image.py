#!/usr/bin/env python3
"""
图片推送到飞书解决方案
支持上传到飞书文档或云盘
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))


class FeishuImagePusher:
    """飞书图片推送器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.output_dir = self.workspace / "output"
    
    def upload_to_doc(self, image_path, doc_token, caption=""):
        """方案1: 上传图片到飞书文档
        
        注意: 飞书docx API支持在write时通过 ![](url) 语法插入图片
        图片需要先上传到可访问的URL
        """
        try:
            from feishu_doc import feishu_doc
            
            image_path = Path(image_path)
            if not image_path.exists():
                return {'error': f'图片不存在: {image_path}'}
            
            # 先上传到GitHub获取URL
            github_result = self.upload_to_github(image_path)
            if 'error' in github_result:
                return github_result
            
            image_url = github_result['raw_url']
            
            # 在文档中插入图片
            markdown_content = f"""
## 图片: {image_path.stem}

![{caption or image_path.name}]({image_url})

*上传时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
            
            # 追加到文档
            result = feishu_doc(
                action='append',
                doc_token=doc_token,
                content=markdown_content
            )
            
            return {
                'method': 'doc_image',
                'success': True,
                'doc_url': f"https://feishu.cn/docx/{doc_token}",
                'image_url': image_url,
                'result': result
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def upload_to_github(self, image_path, commit_msg=None):
        """方案2: 上传图片到GitHub并返回链接"""
        try:
            import subprocess
            
            image_path = Path(image_path)
            if not image_path.exists():
                return {'error': f'图片不存在: {image_path}'}
            
            # 复制到output目录
            output_file = self.output_dir / image_path.name
            output_file.write_bytes(image_path.read_bytes())
            
            # Git提交
            commit_message = commit_msg or f"添加图片: {image_path.name}"
            
            subprocess.run(
                ['git', 'add', f'output/{image_path.name}'],
                cwd=self.workspace,
                capture_output=True
            )
            
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.workspace,
                capture_output=True
            )
            
            subprocess.run(
                ['git', 'push', 'github', 'main'],
                cwd=self.workspace,
                capture_output=True
            )
            
            # 生成GitHub链接
            github_url = f"https://github.com/realerich/marvin-backup/blob/main/output/{image_path.name}"
            raw_url = f"https://raw.githubusercontent.com/realerich/marvin-backup/main/output/{image_path.name}"
            
            return {
                'method': 'github',
                'github_url': github_url,
                'raw_url': raw_url,
                'markdown': f"![{image_path.name}]({raw_url})",
                'html': f'<img src="{raw_url}" alt="{image_path.name}" />',
                'file_name': image_path.name
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def upload_to_drive(self, image_path, folder_token=None):
        """方案3: 上传到飞书云盘
        
        注意: 需要先将文件夹分享给Bot
        """
        try:
            from feishu_drive import feishu_drive
            
            image_path = Path(image_path)
            if not image_path.exists():
                return {'error': f'图片不存在: {image_path}'}
            
            # 由于feishu_drive工具可能需要文件在特定位置
            # 这里返回操作指引
            return {
                'method': 'drive',
                'note': '需要手动上传到飞书云盘',
                'steps': [
                    '1. 在飞书中创建一个文件夹',
                    '2. 将文件夹分享给Bot',
                    '3. 使用 feishu_drive 工具上传',
                ],
                'alternative': '建议使用GitHub方案',
                'github_url': self.upload_to_github(image_path).get('github_url')
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def push_image(self, image_path, method='auto', doc_token=None):
        """推送图片 - 智能选择方案"""
        image_path = Path(image_path)
        
        # 检查文件类型
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']
        if image_path.suffix.lower() not in valid_extensions:
            return {'error': f'不支持的图片格式: {image_path.suffix}'}
        
        if method == 'auto':
            if doc_token:
                method = 'doc'
            else:
                method = 'github'
        
        if method == 'doc' and doc_token:
            return self.upload_to_doc(image_path, doc_token)
        elif method == 'github':
            return self.upload_to_github(image_path)
        elif method == 'drive':
            return self.upload_to_drive(image_path)
        else:
            return {'error': f'未知方法: {method}'}


def main():
    """命令行工具"""
    import sys
    
    pusher = FeishuImagePusher()
    
    if len(sys.argv) < 2:
        print("🖼️ 飞书图片推送工具")
        print("\n用法:")
        print("  python3 feishu_image.py <图片路径> [方法] [doc_token]")
        print("\n方法:")
        print("  auto    - 自动选择 (默认)")
        print("  github  - 上传到GitHub")
        print("  doc     - 插入到飞书文档 (需要doc_token)")
        print("\n示例:")
        print("  python3 feishu_image.py output/chart.png github")
        print("  python3 feishu_image.py output/chart.png doc WOW4dLOUBoSdEcxsxPRcGEMOnHh")
        sys.exit(1)
    
    image_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    doc_token = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = pusher.push_image(image_path, method, doc_token)
    
    if 'error' in result:
        print(f"❌ 失败: {result['error']}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 输出友好的提示
    if result.get('method') == 'github':
        print(f"\n✅ 图片已上传!")
        print(f"📎 查看链接: {result['github_url']}")
        print(f"📎 直链: {result['raw_url']}")
        print(f"\n💡 Markdown语法: {result['markdown']}")
    elif result.get('method') == 'doc_image':
        print(f"\n✅ 图片已插入文档!")
        print(f"📎 文档链接: {result['doc_url']}")


if __name__ == '__main__':
    main()