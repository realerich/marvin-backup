#!/usr/bin/env python3
"""
智能语音工具
语音识别 + 语音合成
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/root/.openclaw/workspace/output/audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class VoiceProcessor:
    """语音处理器"""
    
    @staticmethod
    def text_to_speech(text, lang='zh', output_file=None):
        """文字转语音"""
        try:
            import pyttsx3
            
            if not output_file:
                output_file = OUTPUT_DIR / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            
            engine = pyttsx3.init()
            
            # 设置语速
            engine.setProperty('rate', 150)
            
            # 设置音量
            engine.setProperty('volume', 0.9)
            
            engine.save_to_file(text, str(output_file))
            engine.runAndWait()
            
            return str(output_file)
        
        except Exception as e:
            # 如果pyttsx3失败，使用在线TTS服务
            return VoiceProcessor._online_tts(text, output_file)
    
    @staticmethod
    def _online_tts(text, output_file=None):
        """使用在线TTS服务"""
        import urllib.request
        import urllib.parse
        
        if not output_file:
            output_file = OUTPUT_DIR / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        # 使用Google TTS（无需API Key，但有使用限制）
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl=zh-CN&client=tw-ob"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(output_file, 'wb') as f:
                    f.write(response.read())
            
            return str(output_file)
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def speech_to_text(audio_file, lang='zh-CN'):
        """语音转文字"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            # 使用Google语音识别
            text = recognizer.recognize_google(audio, language=lang)
            return text
        
        except sr.UnknownValueError:
            return "无法识别语音内容"
        except sr.RequestError as e:
            return f"识别服务错误: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def process_voice_message(audio_path):
        """处理语音消息（识别+理解）"""
        # 1. 语音识别
        text = VoiceProcessor.speech_to_text(audio_path)
        
        if text.startswith("Error") or text.startswith("无法"):
            return {
                'success': False,
                'error': text,
                'original_text': None
            }
        
        # 2. 返回识别结果
        return {
            'success': True,
            'text': text,
            'message': f"🎙️ 语音识别结果:\n{text}"
        }


class VoiceReplyGenerator:
    """语音回复生成器"""
    
    @staticmethod
    def generate_reply(text, style='normal'):
        """生成带语音的回复"""
        # 生成语音文件
        audio_file = VoiceProcessor.text_to_speech(text)
        
        return {
            'text': text,
            'audio_file': audio_file,
            'has_voice': not audio_file.startswith("Error")
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🎙️ 智能语音工具")
        print("\n用法:")
        print("  python3 voice_tool.py tts '<文字>' [输出文件]")
        print("  python3 voice_tool.py stt <音频文件>")
        print("  python3 voice_tool.py process <音频文件>")
        print("\n示例:")
        print("  python3 voice_tool.py tts '你好，我是Marvin'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'tts':
        text = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else None
        result = VoiceProcessor.text_to_speech(text, output_file=output)
        if result.startswith("Error"):
            print(f"❌ {result}")
        else:
            print(f"✅ 语音已生成: {result}")
    
    elif cmd == 'stt':
        audio_file = sys.argv[2]
        text = VoiceProcessor.speech_to_text(audio_file)
        print(f"🎙️ 识别结果: {text}")
    
    elif cmd == 'process':
        audio_file = sys.argv[2]
        result = VoiceProcessor.process_voice_message(audio_file)
        if result['success']:
            print(result['message'])
        else:
            print(f"❌ {result['error']}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
