export type DocumentRecord = { id:string; filename:string; status:"uploaded"|"processing"|"ready"|"failed"; page_count:number|null; last_processed_page:number; processing_error:string|null };
export type Citation = { document_id:string; filename:string; page:number; excerpt:string; chunk_id?:string|null };
export type ChatResponse = { conversation_id:string; message_id:string; result:{ answer:string; citations:Citation[]; grounded:boolean; confidence:number } };
export class ApiError extends Error { constructor(public code:string, message:string, public status:number){ super(message); this.name="ApiError"; } }
const base=(process.env.NEXT_PUBLIC_API_BASE_URL||"http://localhost:8000").replace(/\/$/,"");
async function request<T>(path:string, sessionId:string, init:RequestInit={}):Promise<T>{
  const headers=new Headers(init.headers); headers.set("X-Session-ID",sessionId);
  if(init.body && !(init.body instanceof FormData)) headers.set("Content-Type","application/json");
  const response=await fetch(`${base}${path}`,{...init,headers});
  if(!response.ok){ let payload:{error?:{code?:string;message?:string}}={}; try{payload=await response.json();}catch{} throw new ApiError(payload.error?.code||"request_failed",payload.error?.message||`Request failed (${response.status}).`,response.status); }
  return response.status===204 ? undefined as T : response.json();
}
export const api={
  listDocuments:(s:string)=>request<DocumentRecord[]>("/api/documents",s),
  upload:(s:string,file:File)=>{const body=new FormData();body.append("file",file);return request<DocumentRecord>("/api/documents/upload",s,{method:"POST",body});},
  process:(s:string,id:string)=>request<DocumentRecord&{done:boolean;progress:number}>(`/api/documents/${id}/process`,s,{method:"POST"}),
  remove:(s:string,id:string)=>request<void>(`/api/documents/${id}`,s,{method:"DELETE"}),
  chat:(s:string,question:string,conversationId:string|null,documentIds:string[])=>request<ChatResponse>("/api/chat",s,{method:"POST",body:JSON.stringify({question,conversation_id:conversationId,document_ids:documentIds.length?documentIds:null})}),
};
