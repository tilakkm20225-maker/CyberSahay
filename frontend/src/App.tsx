import { useState } from 'react'
import { ShieldCheck, Search, Link2, MessageSquareWarning, Activity, History, AlertTriangle } from 'lucide-react'
const API = 'http://127.0.0.1:8000'
type Result = { category:string; risk_score:number; confidence:number; explanation:string[]; recommendation:string }
export default function App() {
 const [mode,setMode]=useState<'message'|'url'>('message'), [value,setValue]=useState('')
 const [result,setResult]=useState<Result|null>(null), [loading,setLoading]=useState(false), [error,setError]=useState('')
 const [history,setHistory]=useState<any[]>([])
 async function analyze(){
  setLoading(true);setError('');setResult(null)
  try{
   const r=await fetch(`${API}${mode==='message'?'/api/analyze':'/api/analyze-url'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mode==='message'?{text:value,channel:'sms'}:{url:value})})
   if(!r.ok) throw new Error(`API returned ${r.status}. Check that backend is running.`)
   setResult(await r.json())
   const h=await fetch(`${API}/api/history`);if(h.ok)setHistory((await h.json()).items)
  }catch(e){setError(e instanceof Error?e.message:'Request failed')}
  finally{setLoading(false)}
 }
 async function refresh(){try{const r=await fetch(`${API}/api/history`);if(r.ok)setHistory((await r.json()).items)}catch{setError('Could not connect to backend')}}
 return <main className="shell">
  <header><div className="brand"><div className="logo"><ShieldCheck/></div><div><b>CyberSahay</b><small>CYBER SAFETY INTELLIGENCE</small></div></div><span className="status">● Prototype dashboard</span></header>
  <section className="hero"><small>AI-ASSISTED FRAUD AWARENESS</small><h1>Pause. Check. <em>Stay safe.</em></h1><p>Review suspicious messages and links for warning signs before taking action.</p></section>
  <section className="layout"><div className="panel">
   <div className="heading"><div><small>THREAT ANALYSIS</small><h2>Check a message or URL</h2></div><Activity/></div>
   <div className="tabs"><button className={mode==='message'?'active':''} onClick={()=>{setMode('message');setResult(null)}}><MessageSquareWarning size={16}/> Message</button><button className={mode==='url'?'active':''} onClick={()=>{setMode('url');setResult(null)}}><Link2 size={16}/> URL</button></div>
   <label>{mode==='message'?'Paste suspicious message':'Enter suspicious URL — do not open it'}</label>
   <textarea value={value} onChange={e=>setValue(e.target.value)} placeholder={mode==='message'?'Example: Your bank account will be blocked. Verify your KYC...':'https://example.com/...'} />
   <p className="privacy"><ShieldCheck size={15}/> Never enter OTPs, passwords, PINs or banking secrets.</p>
   <button className="analyze" disabled={loading||value.trim().length<3} onClick={analyze}><Search size={17}/>{loading?'Analyzing...':'Analyze safely'}</button>
   {error&&<p className="error">{error}</p>}
   {result&&<div className="result"><div className="resulttop"><div><small>ASSESSMENT</small><h3>{result.category}</h3></div><strong>{result.risk_score}<small>/100</small></strong></div><div className="meter"><span style={{width:`${result.risk_score}%`}}/></div><b>Why it was flagged</b><ul>{result.explanation.map((x,i)=><li key={i}>{x}</li>)}</ul><div className="advice"><AlertTriangle size={18}/>{result.recommendation}</div><small className="note">Heuristic indicator, not a calibrated fraud probability or definitive verdict.</small></div>}
  </div><aside><div className="tip"><ShieldCheck/><div><b>Safety first</b><p>Never share OTPs, passwords or PINs.</p></div></div><div className="tip"><Link2/><div><b>Verify independently</b><p>Use official apps and known contact details.</p></div></div><div className="panel hist"><div className="heading"><h2><History size={17}/> Recent checks</h2><button className="refresh" onClick={refresh}>Refresh</button></div>{history.length===0?<p className="muted">Your recent checks appear here after analysis.</p>:history.slice(0,6).map(x=><div className="histrow" key={x.id}><span>{x.input_type}</span><b>{x.category}</b><small>{x.risk_score}/100</small></div>)}</div></aside></section>
  <footer>CyberSahay · Educational prototype · Verify unexpected requests independently.</footer>
 </main>
}
