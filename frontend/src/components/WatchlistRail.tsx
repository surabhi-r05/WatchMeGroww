import {useEffect,useState} from 'react';
import {Search,FolderPlus} from 'lucide-react';
import StockSearch from './StockSearch';
import {api,json} from '../lib/api';

export default function WatchlistRail({active,onStock}:{active:string;onStock:(s:string)=>void}){
 const [lists,setLists]=useState<any[]>([]); const [selected,setSelected]=useState<number>(); const [showGroup,setShowGroup]=useState(false); const [groupName,setGroupName]=useState('');
 const load=()=>api('/watchlists').then(x=>{setLists(x);setSelected(c=>c&&x.some((w:any)=>w.id===c)?c:x[0]?.id)}).catch(()=>{});
 useEffect(()=>{load()},[]); const w=lists.find(x=>x.id===selected)||lists[0];
 const add=async(sym:string)=>{if(!w)return;try{await api(`/watchlists/${w.id}/stocks`,json({symbol:sym,group_id:w.groups?.[0]?.id}));await load()}catch{}}
 const createGroup=async()=>{const name=groupName.trim();if(!w||!name)return;await api(`/watchlists/${w.id}/groups`,json({name,type:'CUSTOM'}));setGroupName('');setShowGroup(false);load()};
 return <aside className="watchlist-rail">
   <div className="rail-header"><div><div className="eyebrow">ALWAYS ON</div><h2>Watchlist</h2></div><span className="badge">{w?.items?.length||0}</span></div>
   <div className="rail-search"><StockSearch onAdd={add}/></div>
   <div className="rail-lists">{lists.map(x=><button key={x.id} onClick={()=>setSelected(x.id)} className={`rail-list ${w?.id===x.id?'selected':''}`}>{x.name}<span>{x.items?.length||0}</span></button>)}</div>
   <div className="rail-group-tools"><button onClick={()=>setShowGroup(v=>!v)}><FolderPlus size={14}/> New group</button></div>
   {showGroup&&<div className="rail-group-form"><input autoFocus value={groupName} onChange={e=>setGroupName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&createGroup()} placeholder="Group name"/><button onClick={createGroup}>Add</button></div>}
   <div className="rail-groups">{w?.groups?.map((g:any)=><span key={g.id} className="badge">{g.name}</span>)}</div>
   <div className="rail-holdings">{w?.items?.map((x:any)=><button key={x.symbol} className={`rail-stock ${active===x.symbol?'active':''}`} onClick={()=>onStock(x.symbol)}>
     <span className="rail-stock-main"><b>{x.symbol}</b><small>{x.name}</small><em>{x.sector_index}{x.sector_value!=null?` · ₹${Number(x.sector_value).toLocaleString('en-IN')}`:''}</em></span><span className={x.change_pct>=0?'green':'red'}>{x.change_pct>=0?'+':''}{x.change_pct}%</span>
   </button>)}{!w?.items?.length&&<div className="rail-empty"><Search size={16}/> Search above to add stocks.</div>}</div>
 </aside>
}
