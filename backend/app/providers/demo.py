from datetime import datetime, timedelta
import random

# Demo universe used for fallback and hackathon mode. The real provider is NSE;
# these rows keep the application useful when NSE is unavailable.
STOCKS = [
("RELIANCE","Reliance Industries","Energy","NIFTY OIL & GAS",2912.4),
("ONGC","Oil & Natural Gas Corporation","Energy","NIFTY OIL & GAS",292.5),
("NTPC","NTPC","Power","NIFTY POWER",421.2),
("POWERGRID","Power Grid Corporation","Power","NIFTY POWER",356.4),
("TCS","Tata Consultancy Services","IT","NIFTY IT",4210.5),
("INFY","Infosys","IT","NIFTY IT",1842.3),
("HCLTECH","HCL Technologies","IT","NIFTY IT",1682.5),
("WIPRO","Wipro","IT","NIFTY IT",548.2),
("TECHM","Tech Mahindra","IT","NIFTY IT",1710.8),
("HDFCBANK","HDFC Bank","Private Bank","NIFTY BANK",1718.2),
("ICICIBANK","ICICI Bank","Private Bank","NIFTY BANK",1324.6),
("AXISBANK","Axis Bank","Private Bank","NIFTY BANK",1188.4),
("KOTAKBANK","Kotak Mahindra Bank","Private Bank","NIFTY BANK",2054.1),
("SBIN","State Bank of India","Banking","NIFTY BANK",822.7),
("INDUSINDBK","IndusInd Bank","Private Bank","NIFTY BANK",1455.0),
("ITC","ITC","FMCG","NIFTY FMCG",486.8),
("HINDUNILVR","Hindustan Unilever","FMCG","NIFTY FMCG",2841.7),
("NESTLEIND","Nestle India","FMCG","NIFTY FMCG",2490.0),
("BRITANNIA","Britannia Industries","FMCG","NIFTY FMCG",5750.0),
("BHARTIARTL","Bharti Airtel","Telecom","NIFTY TELECOM",1946.1),
("JINDALSTEL","Jindal Steel & Power","Metals","NIFTY METAL",1018.4),
("TATASTEEL","Tata Steel","Metals","NIFTY METAL",178.9),
("JSWSTEEL","JSW Steel","Metals","NIFTY METAL",1124.2),
("HINDALCO","Hindalco Industries","Metals","NIFTY METAL",755.2),
("MARUTI","Maruti Suzuki","Auto","NIFTY AUTO",15620.0),
("TATAMOTORS","Tata Motors","Auto","NIFTY AUTO",1046.5),
("M&M","Mahindra & Mahindra","Auto","NIFTY AUTO",3250.0),
("BAJAJ-AUTO","Bajaj Auto","Auto","NIFTY AUTO",10420.0),
("SUNPHARMA","Sun Pharmaceutical","Pharma","NIFTY PHARMA",1765.4),
("DRREDDY","Dr. Reddy's Laboratories","Pharma","NIFTY PHARMA",1325.0),
("CIPLA","Cipla","Pharma","NIFTY PHARMA",1568.0),
("DIVISLAB","Divi's Laboratories","Pharma","NIFTY PHARMA",6120.0),
("LT","Larsen & Toubro","Capital Goods","NIFTY INFRA",3862.8),
("ADANIPORTS","Adani Ports","Infrastructure","NIFTY INFRA",1510.3),
("BEL","Bharat Electronics","Defence","NIFTY INDIA DEFENCE",405.0),
("HAL","Hindustan Aeronautics","Defence","NIFTY INDIA DEFENCE",5120.0),
("ULTRACEMCO","UltraTech Cement","Cement","NIFTY INFRA",12350.0),
("GRASIM","Grasim Industries","Cement","NIFTY INFRA",2910.0),
("ASIANPAINT","Asian Paints","Consumer","NIFTY CONSUMPTION",2920.0),
("TITAN","Titan Company","Consumer","NIFTY CONSUMPTION",3950.0),
("TRENT","Trent","Consumer","NIFTY CONSUMPTION",7650.0),
("ADANIENT","Adani Enterprises","Conglomerate","NIFTY 50",2780.0),
("COALINDIA","Coal India","Mining","NIFTY METAL",470.0),
("IOC","Indian Oil Corporation","Energy","NIFTY OIL & GAS",155.0),
("BPCL","Bharat Petroleum","Energy","NIFTY OIL & GAS",375.0),
("EICHERMOT","Eicher Motors","Auto","NIFTY AUTO",6200.0),
("HEROMOTOCO","Hero MotoCorp","Auto","NIFTY AUTO",5700.0),
("BAJFINANCE","Bajaj Finance","NBFC","NIFTY FINANCIAL SERVICES",8200.0),
("BAJAJFINSV","Bajaj Finserv","NBFC","NIFTY FINANCIAL SERVICES",1950.0),
("SHRIRAMFIN","Shriram Finance","NBFC","NIFTY FINANCIAL SERVICES",720.0),
("DLF","DLF","Realty","NIFTY REALTY",820.0),
]
SECTOR_CHANGE={"IT":1.2,"Private Bank":0.7,"Banking":0.5,"Energy":0.9,"FMCG":-0.1,"Telecom":1.0,"Metals":0.6,"Auto":1.4,"Pharma":-0.4,"Capital Goods":0.8,"Infrastructure":0.3,"Power":0.4,"Defence":1.1,"Cement":0.5,"Consumer":0.9,"Conglomerate":0.7,"Mining":0.6,"NBFC":0.8,"Realty":1.0}

class DemoProvider:
    source = "Demo market data"
    freshness = "demo"
    def stocks(self): return STOCKS
    def quote(self, symbol):
        row=next(r for r in STOCKS if r[0]==symbol.upper()); i=[r[0] for r in STOCKS].index(symbol.upper())
        change=((i * 37) % 83 - 31) / 10
        if symbol.upper() in {"JINDALSTEL","TCS","MARUTI"}: change += 2.5
        rel=1.0 + ((i * 17) % 17) / 10
        if i % 9 == 0: rel += 1.1
        price=round(row[4]*(1+change/100),2)
        reasons=[]
        if rel>=2: reasons.append(f"Volume is {rel:.1f}× the 20-day average")
        if abs(change)>=3: reasons.append(f"Large {change:+.1f}% daily move")
        if change>SECTOR_CHANGE.get(row[2],0)+1: reasons.append("Outperforming its sector")
        if i%4==0: reasons.append("Price is above a recent moving-average level")
        if not reasons: reasons.append("No major anomaly detected")
        return {"price":price,"change_pct":round(change,2),"volume":int(900000+i*137000),"relative_volume":round(rel,2),"sector_change_pct":SECTOR_CHANGE.get(row[2],0),"trend":"Bullish" if change>1 else "Bearish" if change<-1 else "Sideways","attention":"High" if len(reasons)>=2 or abs(change)>=3 else "Medium","reasons":reasons,"source":self.source,"freshness":self.freshness,"fetched_at":datetime.utcnow().isoformat()}
    def history(self,symbol,days=365):
        row=next(r for r in STOCKS if r[0]==symbol.upper()); rng=random.Random(sum(map(ord,symbol.upper()))); price=row[4]*0.82; out=[]
        for d in range(days):
            price*=1+rng.gauss(0.0007,0.018)
            out.append({"date":(datetime.utcnow()-timedelta(days=days-d)).strftime("%Y-%m-%d"),"price":round(price,2),"close":round(price,2),"volume":int(800000+rng.random()*1800000)})
        return out

    def fundamentals(self, symbol):
        row=next(r for r in STOCKS if r[0]==symbol.upper())
        i=[r[0] for r in STOCKS].index(symbol.upper())
        # Deterministic, internally consistent fallback values for the practice/demo environment.
        pe=round(15 + (i*7)%180/10,2)
        eps=round(row[4]/pe,2) if pe else None
        roe=round(10 + (i*13)%180/10,2)
        roce=round(max(8, roe-2.5),2)
        debt=round(0.15 + (i*17)%95/100,2)
        growth=round(-2 + (i*11)%180/10,2)
        margin=round(7 + (i*19)%230/10,2)
        return {
            "market_cap": "Demo estimate", "pe": pe, "eps": eps,
            "dividend_yield": round(0.4 + (i*3)%45/10,2),
            "roe": roe, "roce": roce, "debt_to_equity": debt,
            "revenue_growth": growth, "net_margin": margin,
            "source": "Demo fallback", "freshness": "demo"
        }

    def option_chain(self, symbol):
        row=next(r for r in STOCKS if r[0]==symbol.upper())
        price=row[4]
        step=10 if price < 1000 else 50 if price < 5000 else 100
        atm=round(price/step)*step
        chain=[]
        for n in range(-6,7):
            strike=atm+n*step
            dist=abs(n)
            call_oi=max(1000,int(220000/(1+dist*0.55)+(n<0)*35000))
            put_oi=max(1000,int(220000/(1+dist*0.5)+(n>0)*40000))
            chain.append({
                "strike": strike, "expiry": "Demo expiry",
                "call": {"oi": call_oi,"change_oi": int(call_oi*0.08*(1 if n<=0 else -1)),"volume": int(call_oi*0.32),"iv": round(18+dist*0.7,2),"ltp": round(max(0.5,price-strike+35),2)},
                "put": {"oi": put_oi,"change_oi": int(put_oi*0.07*(1 if n>=0 else -1)),"volume": int(put_oi*0.29),"iv": round(18+dist*0.65,2),"ltp": round(max(0.5,strike-price+35),2)}
            })
        total_call=sum(x["call"]["oi"] for x in chain); total_put=sum(x["put"]["oi"] for x in chain)
        return {"symbol":symbol.upper(),"underlying":round(price,2),"expiry":"Demo expiry","pcr":round(total_put/total_call,2),"chain":chain,"source":"Demo fallback","freshness":"demo"}

    def sector_quote(self, index_name):
        index_name = index_name.upper()
        # Stable demo index levels keep sector cards useful when NSE is unavailable.
        levels = {
            "NIFTY IT": 42350.0, "NIFTY BANK": 56842.3, "NIFTY METAL": 10125.0,
            "NIFTY PHARMA": 21980.0, "NIFTY AUTO": 28150.0, "NIFTY FMCG": 58240.0,
            "NIFTY OIL & GAS": 12850.0, "NIFTY POWER": 7850.0, "NIFTY TELECOM": 4120.0,
            "NIFTY INFRA": 9650.0, "NIFTY INDIA DEFENCE": 8420.0,
            "NIFTY FINANCIAL SERVICES": 27450.0, "NIFTY REALTY": 1120.0,
            "NIFTY CONSUMPTION": 11850.0, "NIFTY 50": 25123.45,
        }
        level = levels.get(index_name)
        if level is None:
            return None
        sector_name = next((r[2] for r in STOCKS if r[3].upper() == index_name), index_name)
        return {"name": index_name, "value": level, "change_pct": SECTOR_CHANGE.get(sector_name, 0.0), "source": "Demo fallback", "freshness": "demo", "fetched_at": datetime.utcnow().isoformat()}

    def market(self): return {"NIFTY 50":{"value":25123.45,"change_pct":0.73,"source":self.source,"freshness":"demo"},"SENSEX":{"value":82110.2,"change_pct":0.61,"source":self.source,"freshness":"demo"},"BANK NIFTY":{"value":56842.3,"change_pct":0.92,"source":self.source,"freshness":"demo"}}
