from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import *
from app.schemas.schemas import *
from app.core.auth import current_user, hash_password, verify_password
from app.providers import provider, news_provider
from app.providers.demo import STOCKS
from app.seed import ensure_default_watchlist
from app.providers import NSEProvider
from app.services.analytics import indicators
from app.services.health import watchlist_health
from app.services.signals import detect_signals
from app.services.alerts import evaluate_user_alerts
import json

router=APIRouter(prefix="/api")

def stock_by_symbol(db,symbol):return db.scalar(select(Stock).where(Stock.symbol==symbol.upper()))
def item_for(db,user_id,wid,symbol):
    s=stock_by_symbol(db,symbol)
    if not s:return None,None
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user_id))
    if not w:return None,None
    return w,db.scalar(select(WatchlistItem).where(WatchlistItem.watchlist_id==wid,WatchlistItem.stock_id==s.id))

def quote_with_state(db,user,s):
    q=provider.quote(s.symbol)
    sector=None
    if isinstance(provider, NSEProvider):
        sector=provider.sector_quote(s.sector_index)
        if sector:
            q['sector_change_pct']=sector.get('change_pct')
            q['sector_source']=sector.get('source')
            q['sector_freshness']=sector.get('freshness')
    state=db.scalar(select(UserStockState).where(UserStockState.user_id==user.id,UserStockState.stock_id==s.id));since=None
    if state and state.last_seen_price:since=round((q["price"]/state.last_seen_price-1)*100,2)
    return {"symbol":s.symbol,"name":s.name,"sector":s.sector,"sector_index":s.sector_index,"exchange":s.exchange,**q,"since_last_seen_pct":since,"pinned":False,"note":None}

@router.post('/auth/register')
def register(x:AuthIn,db:Session=Depends(get_db)):
    email=x.email.lower().strip()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Email already registered")
    u=User(email=email,password_hash=hash_password(x.password));db.add(u);db.flush();db.add(UserPreference(user_id=u.id,styles="swing"));db.commit();ensure_default_watchlist(db,u)
    return {"email":u.email}

@router.post('/auth/login')
def login(x:AuthIn,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==x.email.lower().strip()))
    if not u or not verify_password(x.password,u.password_hash):raise HTTPException(401,"Invalid credentials")
    return {"email":u.email,"is_admin":u.is_admin}

@router.get('/me')
def me(user:User=Depends(current_user)):return {"email":user.email,"is_admin":user.is_admin}

@router.get('/stocks/search')
def search(q:str=Query(min_length=1),db:Session=Depends(get_db),user:User=Depends(current_user)):
    q=q.strip();like=f'%{q}%'
    rows=db.scalars(select(Stock).where((Stock.symbol.ilike(like))|(Stock.name.ilike(like))|(Stock.sector.ilike(like))|(Stock.sector_index.ilike(like))).limit(15)).all()
    return [{"symbol":s.symbol,"name":s.name,"sector":s.sector,"sector_index":s.sector_index,"exchange":s.exchange} for s in rows]

@router.get('/stocks/{symbol}')
def stock(symbol:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    s=stock_by_symbol(db,symbol)
    if not s:raise HTTPException(404,"Stock not found")
    q=provider.quote(s.symbol)
    if isinstance(provider, NSEProvider):
        sector=provider.sector_quote(s.sector_index)
        if sector: q['sector_change_pct']=sector.get('change_pct');q['sector_source']=sector.get('source');q['sector_freshness']=sector.get('freshness')
    h=provider.history(s.symbol,365);ind=indicators(h)
    state=db.scalar(select(UserStockState).where(UserStockState.user_id==user.id,UserStockState.stock_id==s.id));since=None if not state or not state.last_seen_price else round((q['price']/state.last_seen_price-1)*100,2)
    item=db.scalar(select(WatchlistItem).join(Watchlist).where(Watchlist.user_id==user.id,WatchlistItem.stock_id==s.id))
    news=news_provider.stock_news(s.symbol,s.name,8)
    signals=detect_signals(s.symbol,h,q)
    prices=[x["price"] for x in h]
    options=provider.option_chain(s.symbol) if isinstance(provider, NSEProvider) else {"symbol":s.symbol,"chain":[],"freshness":"demo","source":"Demo"}
    return {"symbol":s.symbol,"name":s.name,"sector":s.sector,"sector_index":s.sector_index,"exchange":s.exchange,**q,"indicators":ind,"support":round(min(prices[-30:]),2),"resistance":round(max(prices[-30:]),2),"fundamentals":provider.fundamentals(s.symbol) if hasattr(provider,"fundamentals") else {"market_cap":"N/A","pe":"N/A","eps":"N/A","dividend_yield":"N/A","roe":"N/A","roce":"N/A","debt_to_equity":"N/A","source":"Unavailable","freshness":"unavailable"},"options":options,"news":news,"signals":signals,"since_last_seen_pct":since,"pinned":bool(item and item.is_pinned),"note":item.note if item else None}

@router.get('/stocks/{symbol}/history')
def history(symbol:str,days:int=365,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if not stock_by_symbol(db,symbol):raise HTTPException(404,"Stock not found")
    return provider.history(symbol,min(max(days,30),365))

@router.post('/stocks/{symbol}/seen')
def seen(symbol:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    s=stock_by_symbol(db,symbol);q=provider.quote(symbol)
    if not s:raise HTTPException(404,"Stock not found")
    st=db.scalar(select(UserStockState).where(UserStockState.user_id==user.id,UserStockState.stock_id==s.id))
    if not st:st=UserStockState(user_id=user.id,stock_id=s.id,);db.add(st)
    st.last_seen_at=datetime.utcnow();st.last_seen_price=q["price"];st.last_seen_volume=q["volume"];db.commit();return {"ok":True,"seen_at":st.last_seen_at.isoformat()}

@router.get('/news')
def market_news(q:str="Indian stock market",limit:int=8,user:User=Depends(current_user)):return news_provider.search(q,limit)

@router.get('/market/overview')
def market(user:User=Depends(current_user)):return provider.market()

@router.get('/market/provider-status')
def provider_status(user:User=Depends(current_user)):
    return provider.status() if hasattr(provider, 'status') else {'provider': 'unknown'}

@router.get('/market/sectors')
def sectors(db:Session=Depends(get_db),user:User=Depends(current_user)):
    result=[]
    seen=set()
    for s in db.scalars(select(Stock)).all():
        if s.sector_index in seen: continue
        seen.add(s.sector_index)
        q=provider.sector_quote(s.sector_index) if isinstance(provider, NSEProvider) else None
        if q:
            result.append({'sector':s.sector,'index':s.sector_index,'change_pct':q.get('change_pct'),'value':q.get('value'),'source':q.get('source'),'freshness':q.get('freshness')})
        else:
            rows=[provider.quote(x.symbol)['change_pct'] for x in db.scalars(select(Stock).where(Stock.sector_index==s.sector_index)).all()]
            result.append({'sector':s.sector,'index':s.sector_index,'change_pct':round(sum(rows)/len(rows),2) if rows else 0,'source':'derived','freshness':'demo'})
    return sorted(result,key=lambda x:x.get('change_pct') or 0,reverse=True)

@router.get('/stocks/{symbol}/options')
def options(symbol:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if not stock_by_symbol(db,symbol): raise HTTPException(404,'Stock not found')
    return provider.option_chain(symbol) if isinstance(provider,NSEProvider) else {'symbol':symbol.upper(),'chain':[],'freshness':'demo','source':'Demo'}

@router.get('/market/movers')
def movers(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=[]
    for s in db.scalars(select(Stock)).all():rows.append({"symbol":s.symbol,"name":s.name,"sector":s.sector,**provider.quote(s.symbol)})
    return {"gainers":sorted(rows,key=lambda x:x['change_pct'],reverse=True)[:6],"losers":sorted(rows,key=lambda x:x['change_pct'])[:6],"active":sorted(rows,key=lambda x:x['relative_volume'],reverse=True)[:6]}

@router.get('/watchlists')
def lists(db:Session=Depends(get_db),user:User=Depends(current_user)):
    result=[]
    for w in db.scalars(select(Watchlist).where(Watchlist.user_id==user.id)).all():
        items=[]
        for it in w.items:
            s=db.get(Stock,it.stock_id);row=quote_with_state(db,user,s);row.update({"id":it.id,"group_id":it.group_id,"pinned":it.is_pinned,"note":it.note,"sort_order":it.sort_order});items.append(row)
        changes=[x['change_pct'] for x in items];health=watchlist_health(changes)
        result.append({"id":w.id,"name":w.name,"is_default":w.is_default,"groups":[{"id":g.id,"name":g.name,"type":g.type} for g in w.groups],"items":items,"health":health})
    return result

@router.post('/watchlists')
def create_list(x:WatchlistCreate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if x.is_default:db.query(Watchlist).filter(Watchlist.user_id==user.id).update({Watchlist.is_default:False})
    w=Watchlist(user_id=user.id,name=x.name.strip(),is_default=x.is_default);db.add(w);db.flush();db.add(WatchlistGroup(watchlist_id=w.id,name='Uncategorized',type='CUSTOM'));db.commit();return {"id":w.id,"name":w.name}

@router.patch('/watchlists/{wid}')
def rename_list(wid:int,x:WatchlistCreate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));
    if not w:raise HTTPException(404,"Watchlist not found")
    if x.is_default:db.query(Watchlist).filter(Watchlist.user_id==user.id).update({Watchlist.is_default:False})
    w.name=x.name.strip();w.is_default=x.is_default;db.commit();return {"ok":True}

@router.delete('/watchlists/{wid}')
def delete_list(wid:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));
    if not w:raise HTTPException(404,"Watchlist not found")
    db.delete(w);db.commit();return {"ok":True}

@router.post('/watchlists/{wid}/groups')
def add_group(wid:int,x:GroupCreate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));
    if not w:raise HTTPException(404,"Watchlist not found")
    g=WatchlistGroup(watchlist_id=wid,name=x.name.strip(),type=x.type,sort_order=len(w.groups));db.add(g);db.commit();return {"id":g.id,"name":g.name}

@router.post('/watchlists/{wid}/stocks')
def add_stock(wid:int,x:StockAdd,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));s=stock_by_symbol(db,x.symbol)
    if not w or not s:raise HTTPException(404,"Watchlist or stock not found")
    if db.scalar(select(WatchlistItem).where(WatchlistItem.watchlist_id==wid,WatchlistItem.stock_id==s.id)):raise HTTPException(409,"Stock already in watchlist")
    gid=x.group_id or (w.groups[0].id if w.groups else None);db.add(WatchlistItem(watchlist_id=wid,stock_id=s.id,group_id=gid,sort_order=len(w.items)));db.commit();return {"ok":True}

@router.delete('/watchlists/{wid}/stocks/{symbol}')
def remove_stock(wid:int,symbol:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w,it=item_for(db,user.id,wid,symbol)
    if not it:raise HTTPException(404,"Stock not found in watchlist")
    db.delete(it);db.commit();return {"ok":True}

@router.patch('/watchlists/{wid}/stocks/{symbol}')
def edit_item(wid:int,symbol:str,x:NoteUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w,it=item_for(db,user.id,wid,symbol)
    if not it:raise HTTPException(404,"Item not found")
    it.note=x.note;db.commit();return {"ok":True}

@router.post('/watchlists/{wid}/stocks/{symbol}/pin')
def pin(wid:int,symbol:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w,it=item_for(db,user.id,wid,symbol)
    if not it:raise HTTPException(404,"Item not found")
    it.is_pinned=not it.is_pinned;db.commit();return {"pinned":it.is_pinned}

@router.post('/watchlists/{wid}/review')
def review(wid:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));
    if not w:raise HTTPException(404,"Watchlist not found")
    now=datetime.utcnow()
    for it in w.items:
        s=db.get(Stock,it.stock_id);q=provider.quote(s.symbol);st=db.scalar(select(UserStockState).where(UserStockState.user_id==user.id,UserStockState.stock_id==s.id))
        if not st:st=UserStockState(user_id=user.id,stock_id=s.id);db.add(st)
        st.last_seen_at=now;st.last_seen_price=q['price'];st.last_seen_volume=q['volume']
    db.commit();return {"ok":True}

@router.get('/watchlists/{wid}/health')
def health(wid:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    w=db.scalar(select(Watchlist).where(Watchlist.id==wid,Watchlist.user_id==user.id));
    if not w:raise HTTPException(404,"Watchlist not found")
    return watchlist_health([provider.quote(db.get(Stock,it.stock_id).symbol)['change_pct'] for it in w.items])

@router.get('/insights')
def insights(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=[]
    for w in db.scalars(select(Watchlist).where(Watchlist.user_id==user.id)).all():
        for it in w.items:
            s=db.get(Stock,it.stock_id);q=provider.quote(s.symbol);h=provider.history(s.symbol,365);signals=detect_signals(s.symbol,h,q);state=db.scalar(select(UserStockState).where(UserStockState.user_id==user.id,UserStockState.stock_id==s.id));since=None if not state or not state.last_seen_price else round((q['price']/state.last_seen_price-1)*100,2)
            if q['attention']!='Low' or (since is not None and abs(since)>=2):rows.append({"watchlist":w.name,"symbol":s.symbol,"name":s.name,"since_last_seen_pct":since,"signals":signals[:3],**q})
    return sorted(rows,key=lambda x:abs(x.get('since_last_seen_pct') or x['change_pct']),reverse=True)[:30]

@router.get('/insights/summary')
def insight_summary(db:Session=Depends(get_db),user:User=Depends(current_user)):
    data=insights(db,user);return {"items":data,"counts":{"high":sum(1 for x in data if x['attention']=='High'),"medium":sum(1 for x in data if x['attention']=='Medium')},"generated_at":datetime.utcnow().isoformat()}

@router.get('/alerts')
def alerts(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [{"id":a.id,"symbol":db.get(Stock,a.stock_id).symbol,"type":a.alert_type,"threshold":a.threshold,"active":a.is_active,"last_triggered_at":a.last_triggered_at.isoformat() if a.last_triggered_at else None} for a in db.scalars(select(Alert).where(Alert.user_id==user.id)).all()]

@router.post('/alerts')
def create_alert(x:AlertCreate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    allowed={"PRICE_ABOVE","PRICE_BELOW","PCT_MOVE","VOLUME_SPIKE"}
    if x.alert_type not in allowed:raise HTTPException(400,"Unsupported alert type")
    s=stock_by_symbol(db,x.symbol)
    if not s:raise HTTPException(404,"Stock not found")
    a=Alert(user_id=user.id,stock_id=s.id,alert_type=x.alert_type,threshold=x.threshold);db.add(a);db.commit();return {"id":a.id}

@router.patch('/alerts/{aid}')
def toggle_alert(aid:int,active:bool,db:Session=Depends(get_db),user:User=Depends(current_user)):
    a=db.scalar(select(Alert).where(Alert.id==aid,Alert.user_id==user.id));
    if not a:raise HTTPException(404,"Alert not found")
    a.is_active=active;db.commit();return {"active":a.is_active}

@router.delete('/alerts/{aid}')
def delete_alert(aid:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    a=db.scalar(select(Alert).where(Alert.id==aid,Alert.user_id==user.id));
    if not a:raise HTTPException(404,"Alert not found")
    db.delete(a);db.commit();return {"ok":True}

@router.post('/alerts/evaluate')
def evaluate(db:Session=Depends(get_db),user:User=Depends(current_user)):return {"triggered":evaluate_user_alerts(db,user.id)}

@router.get('/notifications')
def notifications(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(100)).all()
    return [{"id":n.id,"title":n.title,"body":n.body,"severity":n.severity,"read":bool(n.read_at),"created_at":n.created_at.isoformat()} for n in rows]

@router.post('/notifications/{nid}/read')
def read_notification(nid:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    n=db.scalar(select(Notification).where(Notification.id==nid,Notification.user_id==user.id));
    if not n:raise HTTPException(404,"Notification not found")
    n.read_at=datetime.utcnow();db.commit();return {"ok":True}

@router.post('/notifications/read-all')
def read_all(db:Session=Depends(get_db),user:User=Depends(current_user)):
    db.query(Notification).filter(Notification.user_id==user.id,Notification.read_at.is_(None)).update({Notification.read_at:datetime.utcnow()});db.commit();return {"ok":True}

@router.get('/compare')
def compare(symbols:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    syms=[x.strip().upper() for x in symbols.split(',') if x.strip()][:4];out=[]
    for sym in syms:
        s=stock_by_symbol(db,sym)
        if not s:continue
        h=provider.history(sym,365);q=provider.quote(sym);base=h[0]['price'];out.append({"symbol":sym,"name":s.name,"price":q['price'],"change_pct":q['change_pct'],"normalized":round(q['price']/base*100,2),"rsi":indicators(h)['rsi14'],"relative_volume":q['relative_volume'],"volatility":indicators(h)['volatility']})
    return out

@router.get('/preferences')
def prefs(db:Session=Depends(get_db),user:User=Depends(current_user)):return {"styles":(user.preferences.styles if user.preferences else 'swing').split(',')}
@router.put('/preferences')
def update_prefs(x:PreferenceUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    p=user.preferences or UserPreference(user_id=user.id);p.styles=','.join(x.styles);db.add(p);db.commit();return {"styles":x.styles}

@router.post('/admin/demo/adjust')
def demo_adjust(symbol:str,delta:float,db:Session=Depends(get_db),user:User=Depends(current_user)):return {"ok":True,"message":"Demo provider is deterministic; use this endpoint as the integration hook for a mutable provider."}
