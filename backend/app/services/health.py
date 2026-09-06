from statistics import pstdev

def watchlist_health(changes):
    if not changes:return {"score":0,"momentum":0,"stability":0,"breadth":0}
    momentum_raw=sum(changes)/len(changes); momentum=max(0,min(100,50+momentum_raw*8))
    stability=max(0,min(100,100-(pstdev(changes) if len(changes)>1 else 0)*12))
    breadth=sum(1 for x in changes if x>0)/len(changes)*100
    return {"score":round(momentum*.4+stability*.3+breadth*.3),"momentum":round(momentum),"stability":round(stability),"breadth":round(breadth)}
