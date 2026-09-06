const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export type Creds={email:string;password:string};
function readCreds():Creds|null{try{return JSON.parse(localStorage.getItem('wmgr_creds')||'null')}catch{return null}}
let creds:Creds|null=readCreds();
export const getCreds=()=>creds;
export const setCreds=(x:Creds)=>{creds=x;localStorage.setItem('wmgr_creds',JSON.stringify(x));};
export const clearCreds=()=>{creds=null;localStorage.removeItem('wmgr_creds');};
export async function api(path:string,opts:RequestInit={}){
  const headers:Record<string,string>={'Content-Type':'application/json',...(opts.headers as Record<string,string>|undefined)};
  if(creds){headers['X-User-Email']=creds.email;headers['X-User-Password']=creds.password;}
  const r=await fetch(API+path,{...opts,headers});
  if(!r.ok){let msg='Request failed';try{const x=await r.json();msg=x.detail||msg}catch{}throw new Error(msg)}
  return r.status===204?null:r.json();
}
export async function login(email:string,password:string){await api('/auth/login',{method:'POST',body:JSON.stringify({email,password})});setCreds({email,password});}
export async function register(email:string,password:string){await api('/auth/register',{method:'POST',body:JSON.stringify({email,password})});setCreds({email,password});}
export const json=(x:any):RequestInit=>({method:'POST',body:JSON.stringify(x)});
