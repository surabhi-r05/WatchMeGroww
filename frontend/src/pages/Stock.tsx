import {useEffect,useMemo,useState} from 'react';
import {ArrowLeft,Bell,Bookmark,Newspaper,ShieldAlert,Plus,Check} from 'lucide-react';
import {Area,AreaChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import Panel from '../components/Panel';
import Metric from '../components/Metric';
import {api,json} from '../lib/api';

const AVAILABLE=[
  ['sma20','SMA 20'],['sma50','SMA 50'],['sma200','SMA 200'],['ema20','EMA 20'],
  ['rsi14','RSI 14'],['macd','MACD'],['bollinger','Bollinger Bands'],['volatility','Volatility']
] as const;
const DEFAULT=['sma20','sma50','rsi14','macd'];

export default function Stock({symbol,onBack}:{symbol:string;onBack:()=>void}){
 const [s,setS]=useState<any>(); const [h,setH]=useState<any[]>([]); const [tab,setTab]=useState('Overview'); const [range,setRange]=useState(120);
 const key=`watchmegroww-indicators-${symbol}`;
 const [selected,setSelected]=useState<string[]>(()=>{try{return JSON.parse(localStorage.getItem(key)||'null')||DEFAULT}catch{return DEFAULT}});
 useEffect(()=>{Promise.all([api('/stocks/'+symbol),api('/stocks/'+symbol+'/history?days=1825')]).then(([a,b])=>{setS(a);setH(b);api('/stocks/'+symbol+'/seen',{method:'POST'}).catch(()=>{})})},[symbol]);
 useEffect(()=>{localStorage.setItem(key,JSON.stringify(selected))},[key,selected]);
 const chart=useMemo(()=>h.slice(-range),[h,range]);
 if(!s)return <div className="loading">Loading stock intelligence…</div>;
 const sector=s.sector_change_pct;
 const rel=sector==null?null:round(s.change_pct-sector,2);
 const fundamentals=s.fundamentals||{}; const options=s.options||{};
 const toggle=(id:string)=>setSelected(v=>v.includes(id)?v.filter(x=>x!==id):[...v,id]);
 return <div className="space-y-6">
  <button onClick={onBack} className="back-btn"><ArrowLeft size={16}/> Back</button>
  <header className="stock-head">
   <div><div className="eyebrow">{s.exchange} · {s.sector}</div><h1 className="page-title">{s.name}</h1><p className="muted">{s.symbol} · {s.sector_index}</p></div>
   <div className="stock-price"><strong>₹{Number(s.price).toLocaleString('en-IN')}</strong><span className={s.change_pct>=0?'green':'red'}>{s.change_pct>=0?'+':''}{s.change_pct}% today</span><small>{s.freshness} · {s.source}</small></div>
  </header>
  <div className="grid md:grid-cols-5 gap-3">
   <Panel><Metric label="Trend" value={s.trend}/></Panel><Panel><Metric label="Relative volume" value={s.relative_volume==null?'N/A':`${s.relative_volume}×`}/></Panel>
   <Panel><Metric label="Sector" value={sector==null?'N/A':`${sector>=0?'+':''}${sector}%`}/></Panel><Panel><Metric label="Vs sector" value={rel==null?'N/A':`${rel>=0?'+':''}${rel}%`}/></Panel>
   <Panel><Metric label="Since last checked" value={s.since_last_seen_pct==null?'First view':`${s.since_last_seen_pct>=0?'+':''}${s.since_last_seen_pct}%`}/></Panel>
  </div>
  <Panel title="Why is this moving?" action={<span className="badge">{s.attention} attention</span>}>
   <div className="grid md:grid-cols-4 gap-4 mt-4"><div><div className="muted text-xs">Price move</div><b className="text-xl">{s.change_pct>=0?'+':''}{s.change_pct}%</b></div><div><div className="muted text-xs">Sector</div><b className="text-xl">{sector==null?'N/A':`${sector>=0?'+':''}${sector}%`}</b></div><div><div className="muted text-xs">Relative volume</div><b className="text-xl">{s.relative_volume==null?'N/A':`${s.relative_volume}×`}</b></div><div><div className="muted text-xs">Signals</div><b className="text-xl">{s.signals.length}</b></div></div>
   <div className="mt-5 space-y-2">{(s.reasons||[]).map((r:string)=><div key={r}>• {r}</div>)}</div>
   <p className="tiny muted mt-4">Market-data-derived explanation. Verified external news is shown separately.</p>
  </Panel>
  <div className="tabs-scroll">{['Overview','Technicals','Fundamentals','Derivatives','News & Events'].map(t=><button key={t} onClick={()=>setTab(t)} className={tab===t?'active':''}>{t}</button>)}</div>
  {tab==='Overview'&&<>
   <div className="grid lg:grid-cols-[2fr_1fr] gap-5">
    <Panel title="Price history" action={<span className="badge">{s.freshness} · {s.source}</span>}>
     <div className="range-row">{[[30,'1M'],[90,'3M'],[120,'6M'],[252,'1Y'],[365,'5Y']].map(([n,l])=><button key={n} onClick={()=>setRange(n as number)} className={range===n?'active':''}>{l}</button>)}</div>
     <div className="h-80"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><XAxis dataKey="date" tick={{fontSize:10}} minTickGap={35}/><YAxis tick={{fontSize:10}} domain={['auto','auto']}/><Tooltip/><Area type="monotone" dataKey="price" strokeWidth={2} fillOpacity={0.1}/></AreaChart></ResponsiveContainer></div>
    </Panel>
    <Panel title="Support / resistance"><div className="space-y-5 mt-4"><Metric label="Resistance" value={`₹${Number(s.resistance).toLocaleString('en-IN')}`}/><Metric label="Current" value={`₹${Number(s.price).toLocaleString('en-IN')}`}/><Metric label="Support" value={`₹${Number(s.support).toLocaleString('en-IN')}`}/><p className="tiny muted">Derived from recent price structure. These are analytical levels, not guarantees.</p></div></Panel>
   </div>
   <Panel title="Market context"><div className="grid md:grid-cols-3 gap-4 mt-4"><Metric label="Stock today" value={`${s.change_pct>=0?'+':''}${s.change_pct}%`}/><Metric label={s.sector_index||'Sector'} value={sector==null?'N/A':`${sector>=0?'+':''}${sector}%`}/><Metric label="NIFTY 50" value="See Market Overview"/></div></Panel>
  </>}
  {tab==='Technicals'&&<>
   <Panel title="Choose indicators" action={<span className="tiny muted">Saved for this stock</span>}><div className="indicator-picker">{AVAILABLE.map(([id,label])=><button key={id} className={selected.includes(id)?'selected':''} onClick={()=>toggle(id)}>{selected.includes(id)?<Check size={14}/>:<Plus size={14}/>} {label}</button>)}</div></Panel>
   <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">{selected.map(id=><Panel key={id}><div className="eyebrow">{AVAILABLE.find(x=>x[0]===id)?.[1]}</div><div className="text-2xl font-semibold mt-2">{formatIndicator(s.indicators?.[id])}</div><p className="tiny muted mt-2">Calculated from available price history.</p></Panel>)}</div>
   <Panel title="Technical interpretation"><div className="space-y-2 mt-4">{technicalExplanation(s).map(x=><p key={x}>• {x}</p>)}</div></Panel>
  </>}
  {tab==='Fundamentals'&&<>
   <Panel title="Fundamental snapshot" action={<span className="badge">{fundamentals.freshness||'unavailable'} · {fundamentals.source||'N/A'}</span>}><div className="grid md:grid-cols-3 gap-4 mt-4">{Object.entries(fundamentals).filter(([k])=>!['source','freshness','fallback_reason'].includes(k)).map(([k,v]:any)=><Metric key={k} label={k.replaceAll('_',' ')} value={v==null?'N/A':v}/>)}</div>{fundamentals.fallback_reason&&<p className="tiny muted mt-5">{fundamentals.fallback_reason}</p>}</Panel>
   <Panel title="Fundamental analysis"><div className="grid md:grid-cols-3 gap-4 mt-4"><div><b>Profitability</b><p className="muted text-sm mt-1">ROE {fundamentals.roe??'N/A'} · ROCE {fundamentals.roce??'N/A'}</p></div><div><b>Growth</b><p className="muted text-sm mt-1">Revenue growth {fundamentals.revenue_growth??'N/A'}%</p></div><div><b>Leverage / valuation</b><p className="muted text-sm mt-1">P/E {fundamentals.pe??'N/A'} · Debt/Equity {fundamentals.debt_to_equity??'N/A'}</p></div></div></Panel>
  </>}
  {tab==='Derivatives'&&<Panel title="Option chain" action={<span className="badge">{options.freshness} · {options.source}</span>}>
   <div className="grid md:grid-cols-4 gap-3 mt-4"><Metric label="Underlying" value={options.underlying??s.price}/><Metric label="Expiry" value={options.expiry??'N/A'}/><Metric label="PCR" value={options.pcr??'N/A'}/><Metric label="Rows" value={options.chain?.length||0}/></div>
   {options.chain?.length?<div className="table-wrap"><table><thead><tr><th>Call OI</th><th>Call IV</th><th>Strike</th><th>Put IV</th><th>Put OI</th></tr></thead><tbody>{options.chain.slice(Math.max(0,Math.floor(options.chain.length/2)-7),Math.floor(options.chain.length/2)+8).map((r:any)=><tr key={`${r.expiry}-${r.strike}`}><td>{Number(r.call.oi).toLocaleString()}</td><td>{r.call.iv}</td><td><b>{r.strike}</b></td><td>{r.put.iv}</td><td>{Number(r.put.oi).toLocaleString()}</td></tr>)}</tbody></table></div>:<div className="empty-state mt-4"><ShieldAlert size={18}/> Option-chain data unavailable.</div>}
   {options.fallback_reason&&<p className="tiny muted mt-4">{options.fallback_reason} Demo data is shown so the page is not empty.</p>}
  </Panel>}
  {tab==='News & Events'&&<Panel title="Verified news & events" action={<span className="badge"><Newspaper size={13}/> {s.news.freshness}</span>}><div className="space-y-3 mt-4">{(s.news.articles||[]).map((a:any)=><a href={a.url} target="_blank" rel="noreferrer" className="news-card block" key={a.url}><div className="flex justify-between gap-3"><span className="eyebrow">{a.event_type}</span><span className="tiny muted">{a.source}</span></div><h3>{a.title}</h3><p>{a.description}</p><small>{a.published_at?new Date(a.published_at).toLocaleString():''}</small></a>)}{!(s.news.articles||[]).length&&<div className="empty-state"><ShieldAlert size={18}/> Verified news is unavailable. Configure GNEWS_API_KEY for external headlines.</div>}</div></Panel>}
  <Panel title="Signal evidence"><div className="grid md:grid-cols-2 gap-3">{s.signals.map((x:any)=><div className="signal-card" key={x.type}><div className="flex justify-between"><b>{x.type.replaceAll('_',' ')}</b><span>{Math.round(x.confidence*100)}% confidence</span></div><p>{x.explanation}</p><small>{JSON.stringify(x.metrics)}</small></div>)}{!s.signals.length&&<p className="muted">No detected signal at the current threshold.</p>}</div></Panel>
  <Panel title="Quick actions"><div className="flex flex-wrap gap-2"><button className="secondary-btn" onClick={async()=>{const t=Number(prompt('Price above'));if(Number.isFinite(t)){await api('/alerts',json({symbol,alert_type:'PRICE_ABOVE',threshold:t}));alert('Alert created')}}}><Bell size={15}/> Price above</button><button className="secondary-btn" onClick={()=>api(`/watchlists/1/stocks/${symbol}/pin`,{method:'POST'}).catch(()=>{})}><Bookmark size={15}/> Pin to default</button></div></Panel>
 </div>
}
function round(n:number,d=2){const p=10**d;return Math.round(n*p)/p}
function formatIndicator(v:any){if(v==null)return 'N/A';if(typeof v==='object')return Object.entries(v).map(([k,x])=>`${k}: ${x}`).join(' · ');return String(v)}
function technicalExplanation(s:any){const i=s.indicators||{};const out=[];if(i.sma20&&s.price>i.sma20)out.push(`Price is above SMA 20 (${i.sma20}), supporting short-term momentum.`);if(i.sma50&&s.price>i.sma50)out.push(`Price is above SMA 50 (${i.sma50}), indicating a positive medium-term trend.`);if(i.rsi14!=null)out.push(`RSI 14 is ${i.rsi14}; values above 70 are traditionally considered elevated and below 30 depressed.`);if(i.macd?.signal)out.push(`MACD currently reads ${formatIndicator(i.macd)}.`);if(!out.length)out.push('Not enough market history is available for a richer technical interpretation.');return out}
