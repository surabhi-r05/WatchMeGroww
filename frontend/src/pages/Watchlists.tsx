import {useEffect,useMemo,useState} from 'react';
import {Plus,Trash2,Star,StickyNote,RefreshCw,X,FolderPlus} from 'lucide-react';
import Panel from '../components/Panel';
import StockSearch from '../components/StockSearch';
import {api,json} from '../lib/api';

export default function Watchlists({onStock}:{onStock:(s:string)=>void}){
 const [lists,setLists]=useState<any[]>([]); const [selected,setSelected]=useState<number>();
 const [newName,setNewName]=useState(''); const [showCreate,setShowCreate]=useState(false);
 const [groupName,setGroupName]=useState(''); const [showGroup,setShowGroup]=useState(false);
 const [noteFor,setNoteFor]=useState<string|null>(null); const [note,setNote]=useState('');
 const [groupFilter,setGroupFilter]=useState<number|null>(null);
 const load=()=>api('/watchlists').then(x=>{setLists(x);setSelected(c=>c&&x.some((w:any)=>w.id===c)?c:x[0]?.id)});
 useEffect(()=>{load()},[]); const w=lists.find(x=>x.id===selected)||lists[0];
 useEffect(()=>{setGroupFilter(null)},[selected]);
 const groups=w?.groups||[];
 const create=async()=>{const name=newName.trim();if(!name)return;await api('/watchlists',json({name,is_default:!lists.length}));setNewName('');setShowCreate(false);load()};
 const createGroup=async()=>{const name=groupName.trim();if(!w||!name)return;await api(`/watchlists/${w.id}/groups`,json({name,type:'CUSTOM'}));setGroupName('');setShowGroup(false);load()};
 const add=async(sym:string)=>{if(!w)return;try{const gid=groupFilter||groups[0]?.id;await api(`/watchlists/${w.id}/stocks`,json({symbol:sym,group_id:gid}));await load()}catch(e:any){window.alert(e.message)}};
 const saveNote=async()=>{if(!w||!noteFor)return;await api(`/watchlists/${w.id}/stocks/${noteFor}`,json({note}));setNoteFor(null);setNote('');load()};
 const moveGroup=async(symbol:string,gid:number)=>{await api(`/watchlists/${w.id}/stocks/${symbol}/group`,{method:'PATCH',body:JSON.stringify({group_id:gid})});load()};
 const visible=useMemo(()=>groupFilter?w?.items?.filter((x:any)=>x.group_id===groupFilter):w?.items,[w,groupFilter]);
 return <div className="space-y-6">
  <header className="topbar"><div><div className="eyebrow">YOUR MARKET STATE</div><h1 className="page-title">Watchlists</h1><p className="muted">Keep the stocks you care about visible while you work. Open any stock for deeper intelligence.</p></div><button className="secondary-btn" onClick={()=>setShowCreate(v=>!v)}><Plus size={16}/> New list</button></header>
  {showCreate&&<Panel><div className="inline-form"><div><div className="eyebrow">NEW WATCHLIST</div><h2>Name your list</h2></div><input autoFocus value={newName} onChange={e=>setNewName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&create()} placeholder="e.g. Swing ideas, Banks, Long term"/><button className="primary-btn" onClick={create}>Create list</button><button className="icon-btn" onClick={()=>setShowCreate(false)} aria-label="Close"><X size={16}/></button></div></Panel>}
  <div className="watchlist-search-panel"><div className="eyebrow">FIND A STOCK</div><h2>Search the market</h2><p className="muted">Try a company name, ticker, sector or NSE index. New stocks go into the selected group.</p><StockSearch onAdd={add}/></div>
  <div className="grid lg:grid-cols-[240px_1fr] gap-5"><Panel title="Lists"><div className="space-y-2 mt-4">{lists.map(x=><button key={x.id} onClick={()=>setSelected(x.id)} className={`list-btn ${w?.id===x.id?'selected':''}`}><span>{x.name}</span>{x.is_default&&<span className="badge">Default</span>}</button>)}</div></Panel>
   {w&&<div className="space-y-5">
    <Panel><div className="flex justify-between items-start gap-4"><div><h2 className="text-2xl font-bold">{w.name}</h2><p className="muted text-sm">{w.items.length} stocks · health {w.health.score}/100</p></div><div className="flex flex-wrap gap-2"><button className="secondary-btn" onClick={()=>setShowGroup(v=>!v)}><FolderPlus size={15}/> New group</button><button className="secondary-btn" onClick={async()=>{await api(`/watchlists/${w.id}/review`,{method:'POST'});load()}}><RefreshCw size={15}/> Review now</button></div></div>
     {showGroup&&<div className="inline-subform mt-4"><input autoFocus value={groupName} onChange={e=>setGroupName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&createGroup()} placeholder="e.g. Momentum, Banks, Long term"/><button className="primary-btn" onClick={createGroup}>Create group</button><button className="icon-btn" onClick={()=>setShowGroup(false)}><X size={16}/></button></div>}
     <div className="group-tabs mt-4"><button className={!groupFilter?'active':''} onClick={()=>setGroupFilter(null)}>All <span>{w.items.length}</span></button>{groups.map((g:any)=><button key={g.id} className={groupFilter===g.id?'active':''} onClick={()=>setGroupFilter(g.id)}>{g.name} <span>{w.items.filter((x:any)=>x.group_id===g.id).length}</span></button>)}</div>
     <div className="health-mini"><span>Momentum {w.health.momentum}</span><span>Stability {w.health.stability}</span><span>Breadth {w.health.breadth}%</span></div>
    </Panel>
    <Panel title={groupFilter?`Holdings · ${groups.find((g:any)=>g.id===groupFilter)?.name||''}`:'Holdings'}><div className="table-wrap"><table><thead><tr><th>Stock</th><th>Price</th><th>Today</th><th>Sector / index</th><th>Sector value</th><th>Rel. vol.</th><th>Group</th><th>Note</th><th>Actions</th></tr></thead><tbody>{visible?.map((x:any)=><tr key={x.symbol}>
      <td className="cursor-pointer" onClick={()=>onStock(x.symbol)}><b>{x.symbol}</b><span className="block muted text-xs">{x.name}</span></td>
      <td>₹{Number(x.price).toLocaleString('en-IN')}</td><td className={x.change_pct>=0?'green':'red'}>{x.change_pct>=0?'+':''}{x.change_pct}%</td>
      <td><span className="sector-cell"><b>{x.sector}</b><small>{x.sector_index}</small></span></td>
      <td>{x.sector_value==null?'N/A':`₹${Number(x.sector_value).toLocaleString('en-IN')}`}<small className="block muted">{x.sector_change_pct==null?'':`${x.sector_change_pct>=0?'+':''}${x.sector_change_pct}%`}</small></td>
      <td>{x.relative_volume==null?'N/A':`${x.relative_volume}×`}</td>
      <td><select className="compact-select" value={x.group_id||''} onChange={e=>moveGroup(x.symbol,Number(e.target.value))}>{groups.map((g:any)=><option key={g.id} value={g.id}>{g.name}</option>)}</select></td>
      <td>{x.note?<span className="note-visible" title={x.note}><StickyNote size={13}/>{x.note}</span>:<span className="muted text-xs">—</span>}</td>
      <td><div className="flex gap-2"><button className="icon-btn" title="Pin" onClick={()=>api(`/watchlists/${w.id}/stocks/${x.symbol}/pin`,{method:'POST'}).then(load)}><Star size={15} className={x.pinned?'fill-current amber':''}/></button><button className="icon-btn" title="Edit note" onClick={()=>{setNoteFor(x.symbol);setNote(x.note||'')}}><StickyNote size={15}/></button><button className="icon-btn" title="Remove" onClick={()=>api(`/watchlists/${w.id}/stocks/${x.symbol}`,{method:'DELETE'}).then(load)}><Trash2 size={15}/></button></div></td>
     </tr>)}</tbody></table></div>{!visible?.length&&<div className="empty-state">No stocks in this group yet. Search above to add one.</div>}</Panel>
   </div>}
  </div>
  {noteFor&&<Panel><div className="inline-form"><div><div className="eyebrow">NOTE · {noteFor}</div><h2>Keep a thought with this stock</h2></div><input autoFocus value={note} onChange={e=>setNote(e.target.value)} onKeyDown={e=>e.key==='Enter'&&saveNote()} placeholder="Why are you watching it?"/><button className="primary-btn" onClick={saveNote}>Save note</button><button className="icon-btn" onClick={()=>setNoteFor(null)}><X size={16}/></button></div></Panel>}
 </div>
}
