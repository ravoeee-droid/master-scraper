// Deterministic, evidence-aware first-stage enrichment. No network claims or inferred legal ownership.
const EXCLUDE=/\b(caritas|diakonie|awo|arbeiterwohlfahrt|johanniter|malteser|drk|deutsches rotes kreuz|asb|arbeiter-samariter-bund|korian|all[oö]heim|emeis|orian[a-z]*|vit[a-z]*care|kursana|advita|argentum|compassio|pro seniore|senecura)\b/i;
const ROLE=/(pflegefachkraft|pflegefachfrau|pflegefachmann|gesundheits.?und.?krankenpfleg|examiniert.*pflege|altenpfleger|krankenpfleger|intensivpflegefachkraft)/i;
const NOT_ROLE=/(pflegehilf|pflegeassist|pflegehelfer|pflegeleitung|pflegedienstleitung|\bpdl\b|ausbildung|praktik|werkstudent)/i;
function norm(v){return String(v||'').normalize('NFKC').replace(/\s+/g,' ').trim();}
export function enrichJobs(jobs,checkedAt=new Date().toISOString()){
 const grouped=new Map(),unique=new Map();
 for(const j of jobs){
  const company=norm(j.arbeitgeber),title=norm(j.titel),city=norm(j.ort);
  const key=company.toLocaleLowerCase('de')+'|'+title.toLocaleLowerCase('de')+'|'+city.toLocaleLowerCase('de');
  if(unique.has(key))continue;
  unique.set(key,j);
  const employerKey=company.toLocaleLowerCase('de');
  if(employerKey)grouped.set(employerKey,(grouped.get(employerKey)||0)+1);
 }
 return [...unique.values()].map(j=>{
  const company=norm(j.arbeitgeber),title=norm(j.titel),employerKey=company.toLocaleLowerCase('de');
  const excluded=EXCLUDE.test(company);
  const roleOk=ROLE.test(title)&&!NOT_ROLE.test(title);
  const date=/^\d{4}-\d{2}-\d{2}/.test(String(j.datum||''))?String(j.datum).slice(0,10):null;
  const stamp=date?Date.parse(date+'T00:00:00Z'):NaN;
  const days=Number.isFinite(stamp)?Math.floor((Date.parse(checkedAt)-stamp)/86400000):null;
  const plausible=days!==null&&days>=0&&days<730;
  const count=grouped.get(employerKey)||1;
  const rejected=excluded||!roleOk;
  const reasons=[excluded?'Bekannter Konzern/Wohlfahrtsverband – ausschließen':null,!roleOk?'Keine passende examinierte Fachkraftstelle':null,count>=2?'Mehrere Anzeigen dieses Arbeitgebers im Suchergebnis':null,plausible&&days>=30?'Veröffentlichungsdatum mindestens 30 Tage zurück (keine durchgehende Besetzungsprüfung)':null].filter(Boolean);
  return {...j,sourceCheckedAt:checkedAt,companyKey:employerKey,employerJobCount:count,roleMatch:roleOk,excluded,advertisementDays:plausible?days:null,publicationEvidence:plausible?'Quellen-Veröffentlichungsdatum (Kontinuität ungeprüft)':'Kein belastbares Datum',ownershipEvidence:'Nicht geprüft',currentVacancyEvidence:'Anzeige in Quellensuche gefunden; Arbeitgeberseite ungeprüft',verificationStatus:rejected?'AUSSCHLUSS':'RECHERCHE_NÖTIG',reasons,score:rejected?0:Math.min(65,20+(count>=2?20:0)+(plausible&&days>=30?20:0)+(company?5:0)),researchUrl:company?'https://www.google.com/search?q='+encodeURIComponent('"'+company+'" '+(j.ort||'')+' Impressum Pflegedienst'):null};
 });
}
