import {NextResponse} from 'next/server';
export const runtime='nodejs';
export const dynamic='force-dynamic';
const ROOT='https://rest.arbeitsagentur.de/jobboerse/jobsuche-service';
const ENDPOINTS=['/pc/v6/jobs','/pc/v4/app/jobs'];
function normalize(j){const ref=j.referenznummer||j.refnr||'';const place=j.arbeitsort||{};return {referenznummer:ref,arbeitgeber:j.arbeitgeber||j.arbeitgeberName||'',titel:j.titel||j.stellenangebotsTitel||'',ort:typeof place==='string'?place:(place.ort||place.region||''),datum:j.aktuelleVeroeffentlichungsdatum||j.veroeffentlichungsdatum||'',url:j.externeUrl||(ref?'https://www.arbeitsagentur.de/jobsuche/jobdetail/'+encodeURIComponent(ref):''),privatstatus:'NICHT_GEPRUEFT',altersnachweis:'NICHT_NACHGEWIESEN'};}
export async function GET(request){
 const p=new URL(request.url).searchParams;
 const was=(p.get('was')||'Pflegefachkraft').slice(0,90),wo=(p.get('wo')||'Nordrhein-Westfalen').slice(0,90);
 const attempts=[];
 // Progressive reduction makes upstream failures observable. Never turn failures into fake empty results.
 for(const endpoint of ENDPOINTS){
  for(const opts of [
    {was,wo,angebotsart:'1',arbeitszeit:'vz',zeitarbeit:'false',size:'25',page:'1'},
    {was,wo,size:'25',page:'1'},
    {was,size:'25',page:'1'}
  ]){
   const url=new URL(ROOT+endpoint);Object.entries(opts).forEach(([k,v])=>url.searchParams.set(k,v));
   try{
    const res=await fetch(url,{headers:{'X-API-Key':'jobboerse-jobsuche',Accept:'application/json'},signal:AbortSignal.timeout(9000),cache:'no-store'});
    if(!res.ok){attempts.push(endpoint+' HTTP '+res.status);if([401,403,429].includes(res.status))break;continue;}
    const data=await res.json();
    const raw=Array.isArray(data.stellenangebote)?data.stellenangebote:Array.isArray(data.jobs)?data.jobs:null;
    if(!raw){attempts.push(endpoint+' unknown response schema');continue;}
    const jobs=raw.map(normalize);
    return NextResponse.json({source:'Bundesagentur für Arbeit (inoffizielle API)',endpoint,checkedAt:new Date().toISOString(),jobs,total:data.maxErgebnisse||null,filtersApplied:Object.keys(opts),locationFilterApplied:Boolean(opts.wo)},{headers:{'Cache-Control':'no-store'}});
   }catch(e){attempts.push(endpoint+' '+(e.name==='TimeoutError'?'timeout':e.message));}
  }
 }
 return NextResponse.json({error:'Arbeitsagentur-Schnittstelle derzeit nicht verfügbar. '+[...new Set(attempts)].slice(0,6).join('; '),attempts:[...new Set(attempts)]},{status:502,headers:{'Cache-Control':'no-store'}});
}