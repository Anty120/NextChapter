(() => {
'use strict';
const form=document.querySelector('[data-upload-form]'); if (!form) return;
const input=form.querySelector('[type=file]'), button=form.querySelector('[type=submit]'), status=form.querySelector('[data-upload-status]'), progress=form.querySelector('progress'), cancel=form.querySelector('[data-upload-cancel]');
const csrf=form.querySelector('[name=csrfmiddlewaretoken]').value;
let controller, draft, busy=false;
function reset(){busy=false;button.disabled=false;button.removeAttribute('aria-busy');cancel.hidden=true;}
function discard(){if(draft)fetch(draft.cancel_url,{method:'POST',headers:{'X-CSRFToken':csrf},credentials:'same-origin',keepalive:true}).catch(()=>{});draft=null;}
async function send(url,body,type,retry=false){
 for(let attempt=0;;attempt++){
  try{
   const response=await fetch(url,{method:'POST',body,credentials:'same-origin',signal:controller.signal,headers:{'Content-Type':type,'X-CSRFToken':csrf}});
   if(response.status===503&&retry&&attempt<2)continue;
   const data=await response.json().catch(()=>{throw new Error('Upload unavailable. Check your connection and sign-in, then retry.');});
   if(!response.ok)throw new Error(data.error||'Upload failed. Please retry.');
   return data;
  }catch(error){if(retry&&error instanceof TypeError&&attempt<2)continue;throw error;}
 }
}
input.addEventListener('change',()=>{
 const file=input.files[0];input.setCustomValidity('');status.textContent='';if(!file)return;
 const song=/\.mp3$/i.test(file.name),limit=song?10000000:3*1024*1024;
 if(!/\.(pdf|mp3)$/i.test(file.name))input.setCustomValidity('Choose a PDF book or MP3 song.');
 else if(!file.size||file.size>limit)input.setCustomValidity(song?'Choose a nonempty MP3 of 10 MB (10,000,000 bytes) or less.':'Choose a nonempty PDF of up to 3 MiB.');
 else{status.textContent=file.name+' · '+(file.size/1000000).toFixed(2)+' MB · ready to upload.';const title=form.querySelector('[name=title]');if(!title.value.trim())title.value=file.name.replace(/\.(pdf|mp3)$/i,'').slice(0,180);}
});
form.addEventListener('submit',async event=>{
 if(busy){event.preventDefault();return;}
 const file=input.files[0];button.disabled=true;button.setAttribute('aria-busy','true');status.textContent='Uploading and checking your file…';
 if(!file||file.size<=3*1024*1024)return;
 event.preventDefault();busy=true;controller=new AbortController();cancel.hidden=false;progress.hidden=false;progress.max=file.size;progress.value=0;
 try{
  const metadata=Object.fromEntries(new FormData(form));delete metadata.file;delete metadata.csrfmiddlewaretoken;metadata.size=file.size;metadata.permission=form.querySelector('[name=permission]').checked;
  draft=await send(form.dataset.songStartUrl,JSON.stringify(metadata),'application/json');
  if(controller.signal.aborted){discard();throw new DOMException('Cancelled','AbortError');}
  let offset=0;
  while(offset<file.size){
   const next=await send(draft.chunk_url+'?offset='+offset,file.slice(offset,offset+draft.chunk_bytes),'application/octet-stream',true);
   if(!Number.isInteger(next.offset)||next.offset<=offset||next.offset>file.size)throw new Error('Invalid upload progress. Please retry.');
   offset=next.offset;progress.value=offset;status.textContent='Uploading song: '+Math.round(offset/file.size*100)+'%.';
  }
  status.textContent='Checking your MP3…';const result=await send(draft.finish_url,'','application/octet-stream',true);draft=null;window.location.assign(result.url);
 }catch(error){discard();reset();progress.hidden=true;status.textContent=error.name==='AbortError'?'Upload cancelled. You can choose another file.':error.message;}
});
cancel.addEventListener('click',()=>{controller?.abort();discard();});
window.addEventListener('pagehide',discard);window.addEventListener('pageshow',reset);
})();
