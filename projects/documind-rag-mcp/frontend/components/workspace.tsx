"use client";
import { FormEvent,useCallback,useEffect,useState } from "react";
import { api,Citation,DocumentRecord } from "@/lib/api";
import { getSessionId } from "@/lib/session";

type Exchange={question:string;answer:string;grounded:boolean;confidence:number;citations:Citation[]};
export function Workspace(){
 const [session,setSession]=useState(""); const [docs,setDocs]=useState<DocumentRecord[]>([]); const [selected,setSelected]=useState<string[]>([]); const [question,setQuestion]=useState(""); const [conversation,setConversation]=useState<string|null>(null); const [history,setHistory]=useState<Exchange[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
 const refresh=useCallback(async(s:string)=>setDocs(await api.listDocuments(s)),[]);
 useEffect(()=>{const s=getSessionId();setSession(s);refresh(s).catch(e=>setError(e.message));},[refresh]);
 async function upload(file:File){setBusy(true);setError("");try{let doc=await api.upload(session,file);while(doc.status!=="ready"&&doc.status!=="failed") doc=await api.process(session,doc.id);await refresh(session);if(doc.status==="ready")setSelected(v=>[...new Set([...v,doc.id])]);else setError(doc.processing_error||"Document processing failed.");}catch(e){setError(e instanceof Error?e.message:"Upload failed.");}finally{setBusy(false);}}
 async function ask(e:FormEvent){e.preventDefault();if(!question.trim())return;setBusy(true);setError("");try{const q=question.trim();const r=await api.chat(session,q,conversation,selected);setConversation(r.conversation_id);setHistory(v=>[...v,{question:q,...r.result}]);setQuestion("");}catch(e){setError(e instanceof Error?e.message:"Question failed.");}finally{setBusy(false);}}
 async function remove(id:string){try{await api.remove(session,id);setSelected(v=>v.filter(x=>x!==id));await refresh(session);}catch(e){setError(e instanceof Error?e.message:"Delete failed.");}}
 return <section className="workspace" id="workspace">
  <aside><p className="eyebrow">01 · Sources</p><h2>Your document library</h2><label className="drop"><input type="file" accept="application/pdf,.pdf" disabled={busy} onChange={e=>{const f=e.target.files?.[0];if(f)void upload(f);}}/><strong>{busy?"Working…":"Choose a PDF"}</strong><small>PDF only · maximum 10 MB</small></label>
   <div className="docs">{docs.length===0?<p className="muted">No documents yet.</p>:docs.map(d=><div className="doc" key={d.id}><input aria-label={`Select ${d.filename}`} type="checkbox" checked={selected.includes(d.id)} disabled={d.status!=="ready"} onChange={e=>setSelected(v=>e.target.checked?[...v,d.id]:v.filter(x=>x!==d.id))}/><div><b>{d.filename}</b><small>{d.status}{d.page_count?` · ${d.page_count} pages`:""}</small></div><button aria-label={`Delete ${d.filename}`} onClick={()=>void remove(d.id)}>×</button></div>)}</div>
  </aside>
  <div className="chat"><p className="eyebrow">02 · Ask</p><h2>Interrogate the evidence</h2><div className="thread">{history.length===0?<div className="empty"><span>⌁</span><h3>Ask about your selected documents</h3><p>Answers include page-level source excerpts. Unsupported questions receive an explicit refusal.</p></div>:history.map((x,i)=><article className="exchange" key={i}><p className="question">{x.question}</p><div className={x.grounded?"answer grounded":"answer refused"}><small>{x.grounded?`Grounded · ${Math.round(x.confidence*100)}% confidence`:"Insufficient evidence"}</small><p>{x.answer}</p>{x.citations.map((c,j)=><details key={j}><summary>{c.filename} · page {c.page}</summary><blockquote>{c.excerpt}</blockquote></details>)}</div></article>)}</div>
   {error&&<p role="alert" className="error">{error}</p>}<form onSubmit={ask}><textarea aria-label="Question" value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)} placeholder="What are the refund conditions?"/><button className="primary" disabled={busy||!question.trim()}>Ask DocuMind →</button></form>
  </div>
 </section>;
}
