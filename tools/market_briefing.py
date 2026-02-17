#!/usr/bin/env python3
"""
股票盘前简报系统 - 简化版
使用akshare获取美股数据，ETF数据暂用静态方式
"""

import json
from datetime import datetime, timedelta

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
        if today.weekday() >= 5:  # 5=周六, 6=周日
            return False
        return True
    
    def get_overnight_us_market(self):
        """获取隔夜美股信息"""
        try:
            import akshare as ak
            
            # 获取美股主要指数 (.INX=S&P500, .IXIC=纳斯达克)
            sp500_df = ak.index_us_stock_sina(symbol=".INX")
            nasdaq_df = ak.index_us_stock_sina(symbol=".IXIC")
            
            # 计算涨跌幅
            if len(sp500_df) >= 2:
                sp500_latest = sp500_df.iloc[-1]
                sp500_prev = sp500_df.iloc[-2]
                sp500_close = float(sp500_latest['close'])
                sp500_change = (sp500_close - float(sp500_prev['close'])) / float(sp500_prev['close']) * 100
            else:
                sp500_close = 0
                sp500_change = 0
            
            if len(nasdaq_df) >= 2:
                nasdaq_latest = nasdaq_df.iloc[-1]
                nasdaq_prev = nasdaq_df.iloc[-2]
                nasdaq_close = float(nasdaq_latest['close'])
                nasdaq_change = (nasdaq_close - float(nasdaq_prev['close'])) / float(nasdaq_prev['close']) * 100
            else:
                nasdaq_close = 0
                nasdaq_change = 0
            
            return {
                "sp500": {"close": sp500_close, "change": round(sp500_change, 2)},
                "nasdaq": {"close": nasdaq_close, "change": round(nasdaq_change, 2)},
            }
        except Exception as e:
            return {
                "sp500": {"close": 0, "change": 0, "error": str(e)[:50]},
                "nasdaq": {"close": 0, "change": 0, "error": str(e)[:50]},
            }
    
    def generate_briefing(self):
        """生成盘前简报"""
        if not self.is_trading_day():
            return "📅 今日非交易日（周末或节假日），无盘前简报。"
        
        now = datetime.now()
        
        # 获取隔夜美股
        us_market = self.get_overnight_us_market()
        
        briefing = []
        briefing.append(f"📊 盘前简报 | {now.strftime('%Y年%m月%d日 %A')}")
        briefing.append("=" * 50)
        briefing.append("")
        
        # 隔夜美股
        briefing.append("🌙 隔夜美股")
        briefing.append("-" * 30)
        
        if "error" in us_market["sp500"]:
            briefing.append(f"  美股数据: 获取失败")
        else:
            sp_change = us_market["sp500"]["change"]
            nas_change = us_market["nasdaq"]["change"]
            sp_emoji = "📈" if sp_change > 0 else "📉" if sp_change < 0 else "➡️"
            nas_emoji = "📈" if nas_change > 0 else "📉" if nas_change < 0 else "➡️"
            briefing.append(f"  标普500: {sp_emoji} {sp_change:+.2f}%")
            briefing.append(f"  纳斯达克: {nas_emoji} {nas_change:+.2f}%")
        
        briefing.append("")
        
        # 持仓ETF列表
        briefing.append("📈 持仓ETF列表")
        briefing.append("-" * 30)
        for etf in self.etfs:
            briefing.append(f"  • {etf['name']} ({etf['code']})")
        
        briefing.append("")
        
        # 板块热点提示
        briefing.append("🔥 板块关注点")
        briefing.append("-" * 30)
        briefing.append("  • AI/机器人: 关注美股科技股走势")
        briefing.append("  • 汽车: 关注港股汽车板块")
        briefing.append("  • 周期股: 关注大宗商品价格")
        
        briefing.append("")
        briefing.append("=" * 50)
        briefing.append("💡 提示: 9:15-9:25为集合竞价时段")
        
        return "\n".join(briefing)


def main():
    import sys
    
    briefing = MarketBriefing()
    
    if len(sys.argv) < 2:
        result = briefing.generate_briefing()
        print(result)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'now':
        result = briefing.generate_briefing()
        print(result)
    
    elif cmd == 'etfs':
        print("📋 持仓ETF列表:")
        for etf in PORTFOLIO_ETFS:
            print(f"  {etf['name']} ({etf['code']})")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()