from statistics import mean, pstdev

def closes(history): return [float(x.get("close", x.get("price"))) for x in history if x.get("close", x.get("price")) is not None]
def sma(v,p): return round(sum(v[-p:])/p,2) if len(v)>=p else None
def ema(v,p):
    if len(v)<p:return None
    k=2/(p+1); e=sum(v[:p])/p
    for x in v[p:]: e=x*k+e*(1-k)
    return round(e,2)
def rsi(v,p=14):
    if len(v)<=p:return None
    gains=[];losses=[]
    for i in range(1,len(v)):
        d=v[i]-v[i-1];gains.append(max(d,0));losses.append(max(-d,0))
    ag=sum(gains[:p])/p;al=sum(losses[:p])/p
    for i in range(p,len(gains)):
        ag=((ag*(p-1))+gains[i])/p;al=((al*(p-1))+losses[i])/p
    if al==0:return 100.0
    return round(100-(100/(1+ag/al)),2)
def bollinger(v,p=20):
    if len(v)<p:return None
    w=v[-p:];m=mean(w);sd=pstdev(w)
    return {"middle":round(m,2),"upper":round(m+2*sd,2),"lower":round(m-2*sd,2)}
def macd(v):
    e12=ema(v,12);e26=ema(v,26)
    if e12 is None or e26 is None:return None
    return {"macd":round(e12-e26,2),"signal":"N/A","histogram":"N/A"}
def indicators(history):
    v=closes(history); returns=[(v[i]/v[i-1]-1)*100 for i in range(1,len(v)) if v[i-1]]
    return {"sma20":sma(v,20),"sma50":sma(v,50),"sma200":sma(v,200),"ema20":ema(v,20),"rsi14":rsi(v),"macd":macd(v),"bollinger":bollinger(v),"volatility":round(pstdev(returns),2) if len(returns)>1 else None}
