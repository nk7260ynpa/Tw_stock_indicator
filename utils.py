import pandas as pd
import mplfinance as mpf

def ChartTrade(data, trade=pd.DataFrame(), addp=[], v_enable=True):
    data1=data.copy()
    # 如果有交易紀錄，則把交易紀錄與K線彙整
    if trade.shape[0] > 0:
        # 將物件複製出來，不影響原本的交易明細變數
        trade1=trade.copy()
        # 取出進場明細，透過時間索引將資料合併
        buy_order_trade=trade1[["order_day", "order_price"]]
        buy_order_trade=buy_order_trade.set_index("order_day")
        buy_order_trade.columns=['buy_order']
        buy_order_trade=buy_order_trade.drop_duplicates()
        # 取出出場明細，透過時間索引將資料合併
        buy_cover_trade=trade1[["cover_day", "cover_price"]]
        buy_cover_trade=buy_cover_trade.set_index("cover_day")
        buy_cover_trade.columns=['buy_cover']
        buy_cover_trade=buy_cover_trade.drop_duplicates()
        # 將交易紀錄與K線資料彙整
        data1=pd.concat([data1,buy_order_trade,buy_cover_trade],axis=1)
        
        # 將交易紀錄透過副圖的方式繪製
        addp.append(mpf.make_addplot(data1['buy_order']
                        ,type='scatter',color='#FF4500'
                        ,marker='^',markersize=50))
        addp.append(mpf.make_addplot(data1['buy_cover']
                        ,type='scatter',color='#16982B'
                        ,marker='v',markersize=50))
    # 繪製圖表
    mcolor=mpf.make_marketcolors(up='r', down='g', inherit=True)
    mstyle=mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mcolor)
    mpf.plot(data1,addplot=addp,style=mstyle,type='candle',
             volume=v_enable, savefig='Trade.png',
             tight_layout=True, figsize=(24, 8))
    