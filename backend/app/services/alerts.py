from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Alert, Notification, Stock
from app.providers import provider

def evaluate_user_alerts(db:Session,user_id:int):
    alerts=db.scalars(select(Alert).where(Alert.user_id==user_id,Alert.is_active.is_(True))).all(); fired=[]
    for a in alerts:
        stock=db.get(Stock,a.stock_id)
        if not stock:continue
        q=provider.quote(stock.symbol); price=float(q["price"]); change=float(q.get("change_pct",0));rv=float(q.get("relative_volume",0))
        hit=(a.alert_type=="PRICE_ABOVE" and price>=a.threshold) or (a.alert_type=="PRICE_BELOW" and price<=a.threshold) or (a.alert_type=="PCT_MOVE" and abs(change)>=a.threshold) or (a.alert_type=="VOLUME_SPIKE" and rv>=a.threshold)
        if not hit:continue
        if a.last_triggered_at and datetime.utcnow()-a.last_triggered_at<timedelta(minutes=15):continue
        db.add(Notification(user_id=user_id,stock_id=stock.id,title=f"{stock.symbol}: {a.alert_type.replace('_',' ').title()}",body=f"₹{price:,.2f} · {change:+.2f}% today · volume {rv:.1f}× average",severity="high" if abs(change)>=3 else "medium"))
        a.last_triggered_at=datetime.utcnow();fired.append(stock.symbol)
    db.commit();return fired
