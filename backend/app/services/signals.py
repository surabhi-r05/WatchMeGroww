from app.services.analytics import indicators

def detect_signals(symbol,history,quote):
    p=[float(x.get("close",x.get("price"))) for x in history]; vols=[float(x.get("volume",0)) for x in history]
    if not p:return []
    cur=float(quote["price"]); prev=p[-2] if len(p)>1 else cur; ch=float(quote.get("change_pct",0)); avg=sum(vols[-20:])/max(1,len(vols[-20:]));rv=float(quote.get("relative_volume",vols[-1]/avg if avg else 0));ind=indicators(history);out=[]
    def add(t,s,m,e,c):out.append({"symbol":symbol,"type":t,"severity":s,"metrics":m,"explanation":e,"confidence":c})
    if abs(ch)>=3:add("LARGE_PRICE_MOVE","high",{"change_pct":round(ch,2)},f"Price moved {ch:+.2f}% today.",.94)
    if rv>=1.8:add("UNUSUAL_VOLUME","high",{"relative_volume":round(rv,2)},f"Volume is {rv:.1f}× the recent average.",.91)
    sma50=ind["sma50"]
    if sma50 and prev<=sma50<cur:add("MOVING_AVERAGE_CROSS","medium",{"sma50":sma50},"Price crossed above the 50-day moving average.",.88)
    if sma50 and prev>=sma50>cur:add("MOVING_AVERAGE_CROSS","medium",{"sma50":sma50},"Price crossed below the 50-day moving average.",.88)
    if ind["rsi14"] is not None and ind["rsi14"]>=70:add("RSI_HIGH","medium",{"rsi":ind["rsi14"]},"RSI is above 70.",.86)
    if ind["rsi14"] is not None and ind["rsi14"]<=30:add("RSI_LOW","medium",{"rsi":ind["rsi14"]},"RSI is below 30.",.86)
    look=p[-252:]
    if cur>=max(look)*.999:add("52_WEEK_HIGH","high",{"price":round(cur,2)},"Price is at the available 52-week high.",.90)
    if cur<=min(look)*1.001:add("52_WEEK_LOW","high",{"price":round(cur,2)},"Price is at the available 52-week low.",.90)
    if len(p)>=21 and cur>max(p[-21:-1]):add("PRICE_BREAKOUT","high",{"breakout_level":round(max(p[-21:-1]),2)},"Price moved above the recent 20-session high.",.89)
    return out
