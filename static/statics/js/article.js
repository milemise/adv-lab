const articleSlug = document.body.dataset?.slug || new URLSearchParams(window.location.search).get('slug') || null;
const escapeArticle = value => { const d=document.createElement('div'); d.textContent=value ?? ''; return d.innerHTML; };
const articleUrl = window.location.pathname.split('/article/')[1] || '';
async function loadArticlePage(){
  const slug=decodeURIComponent(articleSlug || articleUrl);
  const target=document.getElementById('article');
  if(!slug){target.innerHTML='<div class="p-10">No se indicó una nota.</div>';return;}
  try{
    const response=await fetch('/api/articles/'+encodeURIComponent(slug));
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.detail || 'No se pudo cargar la nota.');
    document.title='ADV-Lab · '+data.title;
    const fallback='https://images-assets.nasa.gov/image/PIA12348/PIA12348~orig.jpg';
    const cover=data.cover || fallback;
    target.innerHTML=`<img src="${escapeArticle(cover)}" onerror="this.src='${fallback}'" class="w-full aspect-[16/7] object-cover" alt="${escapeArticle(data.title)}"><div class="p-7 md:p-10"><p class="mono-label text-slate-500">${escapeArticle(data.author)}</p><h1 class="font-display text-4xl md:text-6xl mt-2">${escapeArticle(data.title)}</h1><p class="text-xs text-slate-500 mt-3">${new Date(data.created_at).toLocaleDateString('es-AR',{day:'2-digit',month:'long',year:'numeric'})}</p><div class="mt-8 text-slate-300 leading-8 whitespace-pre-line">${escapeArticle(data.content)}</div></div>`;
  }catch(error){target.innerHTML=`<div class="p-10"><h1 class="font-display text-3xl">No se pudo cargar la nota</h1><p class="text-slate-400 mt-3">${escapeArticle(error.message)}</p><a class="text-cyan-200 inline-block mt-5" href="/#noticias">Volver a noticias →</a></div>`;}
}
document.addEventListener('DOMContentLoaded',loadArticlePage);
