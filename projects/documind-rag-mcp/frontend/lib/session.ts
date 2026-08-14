const KEY="documind_session_id";
export function getSessionId():string{ if(typeof window==="undefined") return ""; let id=localStorage.getItem(KEY); if(!id){id=crypto.randomUUID();localStorage.setItem(KEY,id);} return id; }
