#!/usr/bin/env python3
"""
股票盘前简报系统
每个交易日早上8点生成持仓ETF盘前简报
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 用户持仓ETF列表
PORTFOLIO_ETFS = [
    {"name": "港股汽车ETF", "code": "520600", "market": "SH"},
    {"name": "电网ETF", "code": "561380", "market": "SH"},
    {"name": "科创50ETF", "code": "588000", "market": "SH"},
    {"name": "科创创业人工智能ETF", "code": "159140", "market": "SZ"},
    {"name": "机器人50ETF", "code": "159559", "market": "SZ"},
    {"name": "人工智能ETF", "code": "159819", "market": "SZ"},
    {"name": "化工ETF", "code": "159870", "market": "SZ"},
]

class MarketBriefing:
    """市场简报生成器"""
    
    def __init__(self):
        self.etfs = PORTFOLIO_ETFS
    
    def is_trading_day(self):
        """判断今天是否为交易日（简化版，排除周末）"""
        today = datetime.now()
        # 周末休市
        if today.weekday() >= 5:  # 5=周六, 6=周日
            return False
        # 实际需要调用交易日历API排除节假日
        return True
    
    def get_overnight_us_market(self):
        """获取隔夜美股信息"""
        try:
            # 使用akshare获取美股数据
            import akshare as ak
            
            # 获取美股主要指数
            us_sp500 = ak.index_us_sp500()
            us_nasdaq = ak.index_us_nasdaq()
            us_dow = ak.index_us_dow()
            
            # 获取最新数据
            sp500_latest = us_sp500.iloc[-1] if not us_sp500.empty else None
            nasdaq_latest = us_nasdaq.iloc[-1] if not us_nasdaq.empty else None
            
            return {
                "sp500": {
                    "close": float(sp500_latest['close']) if sp500_latest is not None else 0,
                    "change": float(sp500_latest['change']) if sp500_latest is not None else 0,
                },
                "nasdaq": {
                    "close": float(nasdaq_latest['close']) if nasdaq_latest is not None else 0,
                    "change": float(nasdaq_latest['change']) if nasdaq_latest is not None else 0,
                }
            }
        except Exception as e:
            # 如果akshare不可用，返回模拟数据或错误信息
            return {
                "sp500": {"close": 0, "change": 0, "note": f"数据获取失败: {str(e)[:50]}"},
                "nasdaq": {"close": 0, "change": 0, "note": f"数据获取失败: {str(e)[:50]}"},
            }
    
    def get_etf_info(self, etf_code, market):
        """获取单个ETF信息"""
        try:
            # 使用新浪财经API获取实时数据
            if market == "SH":
                symbol = f"sh{etf_code}"
            else:
                symbol = f"sz{etf_code}"
            
            url = f"https://hq.sinajs.cn/list={symbol}"
            headers = {
                'Referer': 'https://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0'
            }
            
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 解析返回数据
            # var hq_str_sh520600="港股汽车ETF,1.245,1.257,1.249,1.257,1.242,1.249,1.250,123456,154321,1.257,1000,1.256,2000..."
            data_str = resp.text.split('"')[1]
            data_parts = data_str.split(',')
            
            if len(data_parts) >= 3:
                name = data_parts[0]
                prev_close = float(data_parts[2])
                current = float(data_parts[3])
                change_pct = (current - prev_close) / prev_close * 100
                
                return {
                    "name": name,
                    "current": current,
                    "prev_close": prev_close,
                    "change_pct": round(change_pct, 2),
                    "open": float(data_parts[1]) if len(data_parts) > 1 else current,
                    "high": float(data_parts[4]) if len(data_parts) > 4 else current,
                    "low": float(data_parts[5]) if len(data_parts) > 5 else current,
                }
        except Exception as e:
            return {
                "name": etf_code,
                "error": str(e)[:50],
                "current": 0,
                "change_pct": 0,
            }
    
    def get_a50_futures(self):
        """获取A50期货（富时中国A50指数期货）"""
        try:
            # A50期货是A股盘前的重要指标
            # 这里使用简化的方式
            return {
                "status": "需要接入期货数据API",
                "note": "建议接入富时A50期货实时数据"
            }
        except:
            return {"status": "数据暂不可用"}
    
    def get_commodity_prices(self):
        """获取大宗商品价格（影响化工ETF等）"""
        commodities = {
            "原油": "影响化工ETF",
            "黄金": "避险资产",
            "铜": "工业景气度",
        }
        return commodities
    
    def generate_briefing(self):
        """生成盘前简报"""
        if not self.is_trading_day():
            return "📅 今日非交易日（周末或节假日），无盘前简报。"
        
        now = datetime.now()
        
        # 1. 获取隔夜美股
        us_market = self.get_overnight_us_market()
        
        # 2. 获取持仓ETF信息
        etf_data = []
        for etf in self.etfs:
            info = self.get_etf_info(etf["code"], etf["market"])
            etf_data.append({
                **etf,
                **info
            })
        
        # 3. 生成简报
        briefing = []
        briefing.append(f"📊 盘前简报 | {now.strftime('%Y年%m月%d日 %A')}")
        briefing.append("=" * 50)
        briefing.append("")
        
        # 隔夜美股
        briefing.append("🌙 隔夜美股")
        briefing.append("-" * 30)
        if "note" in us_market["sp500"]:
            briefing.append(f"  标普500: {us_market['sp500']['note']}")
        else:
            sp_change = us_market["sp500"]["change"]
            nas_change = us_market["nasdaq"]["change"]
            sp_emoji = "📈" if sp_change > 0 else "📉" if sp_change < 0 else "➡️"
            nas_emoji = "📈" if nas_change > 0 else "📉" if nas_change < 0 else "➡️"
            briefing.append(f"  标普500: {sp_emoji} {sp_change:+.2f}")
            briefing.append(f"  纳斯达克: {nas_emoji} {nas_change:+.2f}")
        briefing.append("")
        
        # 持仓ETF状态
        briefing.append("📈 持仓ETF")
        briefing.append("-" * 30)
        
        # 按涨跌幅排序
        etf_data_sorted = sorted(etf_data, 
                                 key=lambda x: x.get("change_pct", 0), 
                                 reverse=True)
        
        total_change = 0
        count = 0
        
        for etf in etf_data_sorted:
            change_pct = etf.get("change_pct", 0)
            if "error" not in etf:
                total_change += change_pct
                count += 1
            
            emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            current = etf.get("current", 0)
            
            briefing.append(f"  {emoji} {etf['name']}")
            briefing.append(f"     价格: {current:.3f}  涨跌: {change_pct:+.2f}%")
        
        # 平均涨跌幅
        if count > 0:
            avg_change = total_change / count
            briefing.append("")
            briefing.append(f"  组合平均: {avg_change:+.2f}%")
        
        briefing.append("")
        
        # 板块热点提示
        briefing.append("🔥 板块热点")
        briefing.append("-" * 30)
        
        # 根据ETF类型给出提示
        sector_notes = []
        for etf in etf_data_sorted[:3]:
            name = etf['name']
            if '机器人' in name or '人工智能' in name:
                sector_notes.append("  • AI/机器人: 关注美股科技股走势")
            if '汽车' in name:
                sector_notes.append("  • 汽车: 关注港股汽车板块")
            if '电网' in name or '化工' in name:
                sector_notes.append("  • 周期股: 关注大宗商品价格")
        
        if sector_notes:
            briefing.extend(list(set(sector_notes)))
        else:
            briefing.append("  • 关注隔夜美股对A股情绪的影响")
        
        briefing.append("")
        briefing.append("=" * 50)
        briefing.append("💡 提示: 9:15-9:25为集合竞价时段")
        
        return "\n".join(briefing)
    
    def save_briefing_to_memory(self, briefing_text):
        """保存简报到记忆系统"""
        try:
            from memory_rds import MemoryRDS
            tool = MemoryRDS()
            content = f"盘前简报 {datetime.now().strftime('%Y-%m-%d')}\n\n{briefing_text[:500]}..."
            tool.add_memory(content, "investment", importance=0.6, source="market_briefing")
        except:
            pass


def main():
    import sys
    
    briefing = MarketBriefing()
    
    if len(sys.argv) < 2:
        # 生成简报
        result = briefing.generate_briefing()
        print(result)
        
        # 保存到记忆
        briefing.save_briefing_to_memory(result)
        
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'now':
        # 立即生成
        result = briefing.generate_briefing()
        print(result)
    
    elif cmd == 'etfs':
        # 显示持仓列表
        print("📋 持仓ETF列表:")
        for etf in PORTFOLIO_ETFS:
            print(f"  {etf['name']} ({etf['code']})")
    
    elif cmd == 'test':
        # 测试单个ETF
        if len(sys.argv) > 2:
            code = sys.argv[2]
            market = "SH" if code.startswith('5') else "SZ"
            result = briefing.get_etf_info(code, market)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"未知命令: {cmd}")
        print("\n用法:")
        print("  python3 market_briefing.py        # 生成盘前简报")
        print("  python3 market_briefing.py now    # 立即生成")
        print("  python3 market_briefing.py etfs   # 显示持仓列表")
        print("  python3 market_briefing.py test <代码>  # 测试单个ETF")

if __name__ == '__main__':
    main()
