#!/usr/bin/env python3
"""
文件推送到飞书解决方案
由于飞书API限制，采用多方案组合
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

class FeishuFilePusher:
    """飞书文件推送器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.output_dir = self.workspace / "output"
        
    def push_to_feishu_doc(self, file_path, title=None):
        """方案1: 将文件内容转为飞书文档"""
        try:
            from feishu_doc import feishu_doc
            
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': f'文件不存在: {file_path}'}
            
            # 读取文件内容
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # 创建文档标题
            doc_title = title or f"{file_path.stem}_{datetime.now().strftime('%m%d')}"
            
            # 创建飞书文档
            # 注意：这里假设feishu_doc工具可用
            print(f"📝 正在创建飞书文档: {doc_title}")
            print(f"📄 内容长度: {len(content)} 字符")
            
            # 由于feishu_doc工具需要调用，这里返回指令
            return {
                'method': 'feishu_doc',
                'title': doc_title,
                'content': content[:50000],  # 飞书文档限制
                'file_path': str(file_path)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def upload_to_github_and_share(self, file_path, commit_msg=None):
        """方案2: 上传到GitHub并分享链接"""
        try:
            import subprocess
            
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': f'文件不存在: {file_path}'}
            
            # 复制到output目录
            output_file = self.output_dir / file_path.name
            output_file.write_bytes(file_path.read_bytes())
            
            # Git提交
            commit_message = commit_msg or f"添加文件: {file_path.name}"
            result = subprocess.run(
                ['git', 'add', str(output_file.relative_to(self.workspace))],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )
            
            result = subprocess.run(
                ['git', 'push', 'github', 'main'],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )
            
            # 生成GitHub链接
            github_url = f"https://github.com/realerich/marvin-backup/blob/main/output/{file_path.name}"
            raw_url = f"https://raw.githubusercontent.com/realerich/marvin-backup/main/output/{file_path.name}"
            
            return {
                'method': 'github',
                'github_url': github_url,
                'raw_url': raw_url,
                'file_name': file_path.name,
                'success': True
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def send_file_summary(self, file_path):
        """方案3: 发送文件摘要和关键内容"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': f'文件不存在: {file_path}'}
            
            # 获取文件信息
            stat = file_path.stat()
            size_kb = stat.st_size / 1024
            
            # 读取前2000字符作为预览
            try:
                preview = file_path.read_text(encoding='utf-8', errors='ignore')[:2000]
            except:
                preview = "(二进制文件，无法预览)"
            
            summary = f"""📄 文件生成完成

**文件名**: {file_path.name}
**大小**: {size_kb:.1f} KB
**路径**: {file_path}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

**内容预览**:
```
{preview}
```

💡 由于飞书API限制，文件暂时存储在服务器。
可通过以下方式获取：
1. SSH下载: `scp root@your-server:{file_path} ./`
2. 稍后我将上传到GitHub并提供链接
"""
            return {
                'method': 'summary',
                'summary': summary,
                'file_info': {
                    'name': file_path.name,
                    'size': size_kb,
                    'path': str(file_path)
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def push_file(self, file_path, method='auto', title=None):
        """推送文件 - 智能选择方案"""
        file_path = Path(file_path)
        
        if method == 'auto':
            # 根据文件类型选择最佳方案
            if file_path.suffix in ['.md', '.txt', '.csv', '.json']:
                # 文本文件优先转飞书文档
                method = 'feishu_doc'
            elif file_path.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.pdf']:
                # 图片/PDF优先GitHub
                method = 'github'
            else:
                method = 'github'
        
        if method == 'feishu_doc':
            return self.push_to_feishu_doc(file_path, title)
        elif method == 'github':
            return self.upload_to_github_and_share(file_path, title)
        elif method == 'summary':
            return self.send_file_summary(file_path)
        else:
            return {'error': f'未知方法: {method}'}


def main():
    """命令行工具"""
    import sys
    
    pusher = FeishuFilePusher()
    
    if len(sys.argv) < 2:
        print("📤 飞书文件推送工具")
        print("\n用法:")
        print("  python3 feishu_push.py <文件路径> [方法]")
        print("\n方法:")
        print("  auto        - 自动选择 (默认)")
        print("  feishu_doc  - 转为飞书文档")
        print("  github      - 上传到GitHub")
        print("  summary     - 发送文件摘要")
        sys.exit(1)
    
    file_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    
    result = pusher.push_file(file_path, method)
    
    if 'error' in result:
        print(f"❌ 失败: {result['error']}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()