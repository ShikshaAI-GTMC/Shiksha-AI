// When FastAPI serves the app this resolves to the current site.  When the
// static pages are opened through Live Server (or directly from disk), use the
// local FastAPI server instead of sending /signup to the static-file server.
const isApiOrigin=location.port==='8000';
const API_URL=localStorage.getItem('shiksha_api')||(isApiOrigin?location.origin:'http://localhost:8000');
const token=()=>localStorage.getItem('shiksha_token');
async function request(path,options={}){const headers=options.headers||{};if(token())headers.Authorization=`Bearer ${token()}`;let res;try{res=await fetch(API_URL+path,{...options,headers})}catch{throw new Error(`Cannot reach ShikshaAI API at ${API_URL}. Start the FastAPI server, then try again.`)}const data=await res.json().catch(()=>({detail:`The server returned an invalid response for ${path}. Make sure the FastAPI API is running on port 8000.`}));if(!res.ok)throw new Error(data.detail||'Request failed');return data}
const api={get:p=>request(p),post:(p,body,isForm=false)=>request(p,{method:'POST',body:isForm?body:JSON.stringify(body),headers:isForm?{}:{'Content-Type':'application/json'}}),del:p=>request(p,{method:'DELETE'})};
