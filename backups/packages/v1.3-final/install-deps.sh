#!/bin/bash
# Marvin 工具包依赖安装脚本

set -e

echo "📦 安装系统依赖..."
echo "===================="

# 安装中文字体
if ! dpkg -l | grep -q fonts-wqy-zenhei; then
    echo "安装中文字体..."
    apt-get update && apt-get install -y fonts-wqy-zenhei poppler-utils
else
    echo "✓ 中文字体已安装"
fi

echo ""
echo "🐍 安装Python依赖..."
echo "===================="

# Python依赖
pip3 install     psutil     google-auth     google-auth-oauthlib     google-auth-httplib2     google-api-python-client     pyttsx3     speechrecognition     sentence-transformers     pandas     numpy     matplotlib     plotly     pillow     PyPDF2     reportlab     pdf2image     python-docx     openpyxl     requests     --break-system-packages -q

echo ""
echo "✅ 依赖安装完成!"
