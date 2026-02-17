#!/usr/bin/env python3
"""
浏览器自动化增强工具
表单填写、数据抓取、自动化操作
"""

import json
import time
from datetime import datetime
from pathlib import Path

class BrowserAutomation:
    """浏览器自动化"""
    
    @staticmethod
    def fill_form(url, fields, submit_selector=None):
        """
        填写表单
        fields: [{'selector': '#name', 'value': 'John'}, ...]
        """
        script = f"""
        // 导航到页面
        await page.goto('{url}');
        await page.waitForLoadState('networkidle');
        
        // 填写字段
        {chr(10).join([f"await page.fill('{f['selector']}', '{f['value']}');" for f in fields])}
        
        // 提交
        {'await page.click(\'' + submit_selector + '\');' if submit_selector else ''}
        
        // 等待结果
        await page.waitForTimeout(2000);
        """
        return script
    
    @staticmethod
    def scrape_data(url, selectors, wait_for=None):
        """
        抓取数据
        selectors: {'title': 'h1', 'price': '.price', ...}
        """
        script = f"""
        await page.goto('{url}');
        await page.waitForLoadState('networkidle');
        {'await page.waitForSelector(\'' + wait_for + '\');' if wait_for else ''}
        
        const data = await page.evaluate(() => {{
            const result = {{}};
            {chr(10).join([f"result['{k}'] = document.querySelector('{v}')?.innerText || '';" for k, v in selectors.items()])}
            return result;
        }});
        
        return data;
        """
        return script
    
    @staticmethod
    def auto_login(url, username_selector, password_selector, username, password, submit_selector):
        """自动登录"""
        script = f"""
        await page.goto('{url}');
        await page.waitForSelector('{username_selector}');
        
        await page.fill('{username_selector}', '{username}');
        await page.fill('{password_selector}', '{password}');
        await page.click('{submit_selector}');
        
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        """
        return script
    
    @staticmethod
    def monitor_page(url, check_interval=60, alert_condition=None):
        """监控页面变化"""
        script = f"""
        let previousContent = '';
        
        while (true) {{
            await page.goto('{url}');
            await page.waitForLoadState('networkidle');
            
            const currentContent = await page.content();
            
            if (previousContent && currentContent !== previousContent) {{
                console.log('页面已更新!');
                // 发送通知
            }}
            
            previousContent = currentContent;
            await page.waitForTimeout({check_interval * 1000});
        }}
        """
        return script


class DataExtractor:
    """数据提取器"""
    
    @staticmethod
    def extract_table(table_selector):
        """提取表格数据"""
        script = f"""
        const tableData = await page.evaluate((selector) => {{
            const table = document.querySelector(selector);
            if (!table) return [];
            
            const rows = table.querySelectorAll('tr');
            const data = [];
            
            rows.forEach(row => {{
                const rowData = [];
                row.querySelectorAll('td, th').forEach(cell => {{
                    rowData.push(cell.innerText.trim());
                }});
                if (rowData.length > 0) data.push(rowData);
            }});
            
            return data;
        }}, '{table_selector}');
        
        return tableData;
        """
        return script
    
    @staticmethod
    def extract_links(selector='a'):
        """提取所有链接"""
        script = f"""
        const links = await page.evaluate((selector) => {{
            return Array.from(document.querySelectorAll(selector)).map(a => ({{
                text: a.innerText.trim(),
                href: a.href
            }}));
        }}, '{selector}');
        
        return links;
        """
        return script
    
    @staticmethod
    def extract_images(selector='img'):
        """提取所有图片"""
        script = f"""
        const images = await page.evaluate((selector) => {{
            return Array.from(document.querySelectorAll(selector)).map(img => ({{
                src: img.src,
                alt: img.alt,
                width: img.width,
                height: img.height
            }}));
        }}, '{selector}');
        
        return images;
        """
        return script


class AutomationScriptGenerator:
    """自动化脚本生成器"""
    
    @staticmethod
    def generate_daily_check_script(urls):
        """生成每日检查脚本"""
        script_parts = []
        
        for url in urls:
            script_parts.append(f"""
        // 检查 {url}
        try {{
            await page.goto('{url}');
            await page.waitForLoadState('networkidle');
            const screenshot = await page.screenshot({{ fullPage: false }});
            console.log('{url} - OK');
        }} catch (e) {{
            console.error('{url} - Error:', e.message);
        }}
        """)
        
        return "const {{ chromium }} = require('playwright');\n\n(async () => {\n    const browser = await chromium.launch();\n    const page = await browser.newPage();\n    " + "\n".join(script_parts) + "\n    await browser.close();\n})();"
    
    @staticmethod
    def generate_price_monitor_script(url, price_selector, target_price):
        """生成价格监控脚本"""
        return f"""
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('{url}');
    await page.waitForLoadState('networkidle');
    
    const priceText = await page.textContent('{price_selector}');
    const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));
    
    if (price <= {target_price}) {{
        console.log('价格符合条件:', price);
        // 发送通知
    }} else {{
        console.log('当前价格:', price);
    }}
    
    await browser.close();
}})();
        """


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🌐 浏览器自动化增强工具")
        print("\n用法:")
        print("  python3 browser_auto.py form <url> '<JSON字段>' [提交按钮选择器]")
        print("  python3 browser_auto.py scrape <url> '<JSON选择器>'")
        print("  python3 browser_auto.py login <url> <用户名选择器> <密码选择器> <用户名> <密码> <提交选择器>")
        print("  python3 browser_auto.py table <选择器>")
        print("  python3 browser_auto.py links [选择器]")
        print("  python3 browser_auto.py images [选择器]")
        print("\n示例:")
        print("  python3 browser_auto.py form 'https://example.com/login' '[{{\"selector\": \"#user\", \"value\": \"admin\"}}]'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'form':
        url = sys.argv[2]
        fields = json.loads(sys.argv[3])
        submit = sys.argv[4] if len(sys.argv) > 4 else None
        script = BrowserAutomation.fill_form(url, fields, submit)
        print(script)
    
    elif cmd == 'scrape':
        url = sys.argv[2]
        selectors = json.loads(sys.argv[3])
        script = BrowserAutomation.scrape_data(url, selectors)
        print(script)
    
    elif cmd == 'login':
        url = sys.argv[2]
        user_sel = sys.argv[3]
        pass_sel = sys.argv[4]
        user = sys.argv[5]
        passwd = sys.argv[6]
        submit = sys.argv[7]
        script = BrowserAutomation.auto_login(url, user_sel, pass_sel, user, passwd, submit)
        print(script)
    
    elif cmd == 'table':
        selector = sys.argv[2]
        script = DataExtractor.extract_table(selector)
        print(script)
    
    elif cmd == 'links':
        selector = sys.argv[2] if len(sys.argv) > 2 else 'a'
        script = DataExtractor.extract_links(selector)
        print(script)
    
    elif cmd == 'images':
        selector = sys.argv[2] if len(sys.argv) > 2 else 'img'
        script = DataExtractor.extract_images(selector)
        print(script)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
