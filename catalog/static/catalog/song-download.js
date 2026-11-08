(() => {
'use strict';
const root=document.querySelector('[data-song-download]');if(!root)return;
const start=root.querySelector('[data-download-start]'),cancel=root.querySelector('[data-download-cancel]'),progress=root.querySelector('progress'),status=root.querySelector('[role=status]');let controller;
cancel.addEventListener('click',()=>controller?.abort());
start.addEventListener('click',async()=>{
 start.disabled=true;cancel.hidden=false;controller=new AbortController();const size=Number(root.dataset.size),chunks=[];progress.hidden=false;progress.max=size;progress.value=0;
 try{
  for(let offset=0;offset<size;){
   const end=Math.min(size-1,offset+1048575);
   const response=await fetch(root.dataset.url,{headers:{Range:'bytes='+offset+'-'+end},signal:controller.signal,credentials:'same-origin'});
   if(response.status!==206||response.headers.get('Content-Range')!=='bytes '+offset+'-'+end+'/'+size)throw new Error('Download interrupted. Check your sign-in and retry.');
   const bytes=await response.arrayBuffer();if(bytes.byteLength!==end-offset+1)throw new Error('Incomplete download. Please retry.');
   chunks.push(bytes);offset=end+1;progress.value=offset;status.textContent='Preparing download: '+Math.round(offset/size*100)+'%.';
  }
  const url=URL.createObjectURL(new Blob(chunks,{type:'audio/mpeg'})),link=document.createElement('a');link.href=url;link.download=root.dataset.filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);status.textContent='Your MP3 is ready. Check your browser downloads.';
 }catch(error){status.textContent=error.name==='AbortError'?'Download cancelled.':error.message;}
 finally{chunks.length=0;start.disabled=false;cancel.hidden=true;}
});
})();
