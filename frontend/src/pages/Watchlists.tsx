import {useEffect,useState} from 'react';
import {Plus,Trash2,Star,StickyNote,RefreshCw} from 'lucide-react';
import Panel from '../components/Panel';
import StockSearch from '../components/StockSearch';
import {api,json} from '../lib/api';

export default function Watchlists({onStock}:{onStock:(s:string)=>void}){
 const [lists,setLists]=useState<any[]>([]);
 const [selected,setSelected]=useState<number>();
 const load=()=>api('/watchlists').then(x=>{setLists(x);setSelected((current)=>current&&x.some((w:any)=>w.id===current)?current:x[0]?.id)});
 useEffect(()=>{load()},[]);
 const w=lists.find(x=>x.id===selected)||lists[0];
 const create=async()=>{const name=prompt('Watchlist name');if(!name)return;await api('/watchlists',json({name,is_default:!lists.length}));load()};
 const add=async(sym:string)=>{if(!w)return;try{await api(`/watchlists/${w.id}/stocks`,json({symbol:sym}));await load()}catch(e:any){alert(e.message)}};
 const note=async(sym:string,old:string|null)=>{const n=prompt('Note',old||'');if(n===null)return;await api(`/watchlists/${w.id}/stocks/${sym}`,{method:'PATCH',body:JSON.stringify({note:n})});load()};
 return <div className="space-y-6">
  <header className="topbar"><div><div className="eyebrow">YOUR MARKET STATE</div><h1 className="page-title">Watchlists</h1><p className="muted">Search any company without knowing its ticker. Add it to your list and keep its market context in one place.</p></div><button className="secondary-btn" onClick={create}><Plus size={16}/> New list</button></header>
  <div className="watchlist-search-panel"><div className="eyebrow">FIND A STOCK</div><h2>Search the market</h2><p className="muted">Try “Jindal Steel”, “Airtel”, “metal”, “HDFC” or an NSE symbol.</p><StockSearch onAdd={add}/></div>
  <div className="grid lg:grid-cols-[240px_1fr] gap-5">
   <Panel title="Lists"><div className="space-y-2 mt-4">{lists.map(x=><button key={x.id} onClick={()=>setSelected(x.id)} className={`list-btn ${w?.id===x.id?'selected':''}`}><span>{x.name}</span>{x.is_default&&<span className="badge">Default</span>}</button>)}</div></Panel>
   {w&&<div className="space-y-5"><Panel><div className="flex justify-between items-center"><div><h2 className="text-2xl font-bold">{w.name}</h2><p className="muted text-sm">{w.items.length} stocks · health {w.health.score}/100</p></div><button className="secondary-btn" onClick={async()=>{await api(`/watchlists/${w.id}/review`,{method:'POST'});load()}}><RefreshCw size={15}/> Review now</button></div><div className="health-mini"><span>Momentum {w.health.momentum}</span><span>Stability {w.health.stability}</span><span>Breadth {w.health.breadth}%</span></div></Panel>
    <Panel title="Holdings"><div className="table-wrap"><table><thead><tr><th>Stock</th><th>Price</th><th>Today</th><th>Sector</th><th>Relative vol.</th><th>Actions</th></tr></thead><tbody>{w.items.map((x:any)=><tr key={x.symbol}><td className="cursor-pointer" onClick={()=>onStock(x.symbol)}><b>{x.symbol}</b><span className="block muted text-xs">{x.name}</span></td><td>₹{x.price.toLocaleString('en-IN')}</td><td className={x.change_pct>=0?'green':'red'}>{x.change_pct>=0?'+':''}{x.change_pct}%</td><td><span className="sector-cell">{x.sector}<small>{x.sector_index}</small></span></td><td>{x.relative_volume==null?'N/A':`${x.relative_volume}×`}</td><td><div className="flex gap-2"><button className="icon-btn" title="Pin" onClick={()=>api(`/watchlists/${w.id}/stocks/${x.symbol}/pin`,{method:'POST'}).then(load)}><Star size={15} className={x.pinned?'fill-current amber':''}/></button><button className="icon-btn" title="Note" onClick={()=>note(x.symbol,x.note)}><StickyNote size={15}/></button><button className="icon-btn" title="Remove" onClick={()=>api(`/watchlists/${w.id}/stocks/${x.symbol}`,{method:'DELETE'}).then(load)}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div></Panel>
   </div>}
  </div>
 </div>
}
