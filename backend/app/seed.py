from sqlalchemy import select
from app.db.session import Base,engine,SessionLocal
from app.models import *
from app.providers.demo import STOCKS
from app.core.auth import hash_password

SECTOR_LEADERS = [
    'RELIANCE','TCS','INFY','HDFCBANK','ICICIBANK','SBIN','ITC','BHARTIARTL',
    'JINDALSTEL','TATASTEEL','JSWSTEEL','MARUTI','TATAMOTORS','SUNPHARMA',
    'LT','ADANIPORTS','NTPC','BEL','TITAN','BAJFINANCE','DLF'
]

def ensure_default_watchlist(db, user):
    w=db.scalar(select(Watchlist).where(Watchlist.user_id==user.id,Watchlist.is_default.is_(True)))
    if not w:
        w=Watchlist(user_id=user.id,name='Sector Leaders',is_default=True);db.add(w);db.flush()
    else:
        w.name='Sector Leaders';w.is_default=True
    if not w.groups:
        db.add(WatchlistGroup(watchlist_id=w.id,name='Uncategorized',type='CUSTOM',sort_order=0));db.flush()
    existing={db.get(Stock,it.stock_id).symbol:it for it in w.items if db.get(Stock,it.stock_id)}
    groups={g.name:g for g in w.groups}
    for sym in SECTOR_LEADERS:
        s=db.scalar(select(Stock).where(Stock.symbol==sym))
        if not s: continue
        g=groups.get(s.sector)
        if not g:
            g=WatchlistGroup(watchlist_id=w.id,name=s.sector,type='SECTOR',sort_order=len(groups));db.add(g);db.flush();groups[s.sector]=g
        if sym not in existing:
            db.add(WatchlistItem(watchlist_id=w.id,stock_id=s.id,group_id=g.id,sort_order=len(w.items)))
    db.commit()
    return w

def seed():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        for symbol,name,sector,index_name,price in STOCKS:
            s=db.scalar(select(Stock).where(Stock.symbol==symbol))
            if not s:
                db.add(Stock(symbol=symbol,name=name,sector=sector,sector_index=index_name))
            else:
                s.name=name;s.sector=sector;s.sector_index=index_name;s.exchange='NSE'
        db.commit()

        demo=db.scalar(select(User).where(User.email=='demo@watchmegroww.app'))
        if not demo:
            demo=User(email='demo@watchmegroww.app',password_hash=hash_password('demo1234'))
            db.add(demo);db.flush()
        else:
            # Repair the known hackathon credentials on every startup.
            demo.password_hash=hash_password('demo1234')
        if not demo.preferences:
            db.add(UserPreference(user_id=demo.id,styles='swing,longterm'))
        db.commit()
        ensure_default_watchlist(db,demo)

        admin=db.scalar(select(User).where(User.email=='admin@watchmegroww.app'))
        if not admin:
            db.add(User(email='admin@watchmegroww.app',password_hash=hash_password('admin1234'),is_admin=True));db.commit()
    finally:db.close()

if __name__=='__main__':seed()
