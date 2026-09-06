import {useEffect,useRef,useState} from 'react';
import {Check, Search, TrendingUp} from 'lucide-react';
import {api} from '../lib/api';

type Result={symbol:string;name:string;sector:string;sector_index?:string;exchange?:string};

export default function StockSearch({onAdd,onOpen}:{onAdd?:(symbol:string)=>Promise<void>|void;onOpen?:(symbol:string)=>void}){
 const [q,setQ]=useState('');
 const [results,setResults]=useState<Result[]>([]);
 const [loading,setLoading]=useState(false);
 const [open,setOpen]=useState(false);
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const value=q.trim();
  if(value.length<2){setResults([]);setOpen(false);return}
  const t=setTimeout(async()=>{
   setLoading(true);
   try{setResults(await api('/stocks/search?q='+encodeURIComponent(value)));setOpen(true)}catch{setResults([])}finally{setLoading(false)}
  },220);
  return()=>clearTimeout(t);
 },[q]);
 useEffect(()=>{
  const close=(e:MouseEvent)=>{if(!ref.current?.contains(e.target as Node))setOpen(false)};
  document.addEventListener('mousedown',close);return()=>document.removeEventListener('mousedown',close);
 },[]);
 const choose=async(symbol:string)=>{
  if(onAdd) await onAdd(symbol);
  else onOpen?.(symbol);
  setQ('');setOpen(false);
 };
 return <div className="stock-search" ref={ref}>
  <div className="stock-search-input"><Search size={18}/><input value={q} onChange={e=>setQ(e.target.value)} onFocus={()=>results.length&&setOpen(true)} placeholder="Search stocks, companies or sectors…" aria-label="Search stocks, companies or sectors"/><span className="search-hint">⌘ K</span></div>
  {open&&<div className="stock-search-menu">
   {loading&&<div className="search-loading">Searching NSE stock universe…</div>}
   {!loading&&results.map(r=><button type="button" className="stock-search-result" key={r.symbol} onClick={()=>choose(r.symbol)}>
    <span className="result-icon"><TrendingUp size={16}/></span><span className="result-copy"><b>{r.name}</b><small>{r.symbol} · {r.exchange||'NSE'} · {r.sector}{r.sector_index?` · ${r.sector_index}`:''}</small></span>{onAdd&&<span className="result-action"><Check size={15}/> Add</span>}
   </button>)}
   {!loading&&q.trim().length>=2&&!results.length&&<div className="search-loading">No matching stocks found.</div>}
  </div>}
 </div>
}
