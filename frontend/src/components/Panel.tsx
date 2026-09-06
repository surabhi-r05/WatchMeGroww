import {ReactNode} from 'react';
export default function Panel({title,action,children,className=''}:{title?:string;action?:ReactNode;children:ReactNode;className?:string}){return <section className={`panel p-5 ${className}`}><div className="flex items-center justify-between gap-3">{title&&<h2 className="text-lg font-semibold tracking-tight">{title}</h2>}{action}</div>{children}</section>}
