import { useState, useEffect, useRef } from "react";
import { analyzeReport } from "./api.js";
import { DEMO_ANALYSIS } from "./demoData.js";

const D = {
  bg:"#080C14", bg2:"#0C1220", card:"rgba(255,255,255,0.032)",
  bd:"rgba(255,255,255,0.08)", bd2:"rgba(255,255,255,0.15)",
  em:"#00D4AA", emD:"rgba(0,212,170,0.1)", emB:"rgba(0,212,170,0.22)",
  red:"#FF4060", redD:"rgba(255,64,96,0.1)",
  amb:"#FFB020", ambD:"rgba(255,176,32,0.1)",
  blu:"#4D9EFF", bluD:"rgba(77,158,255,0.09)",
  grn:"#22D67E",
  t1:"#F0F4FF", t2:"#8B9AB8", t3:"#3D5272", t4:"#1A2840",
};

const sc  = (s) => s==="HIGH"?D.red:s==="LOW"?D.amb:D.grn;
const sf  = (s) => s==="HIGH"?D.redD:s==="LOW"?D.ambD:"rgba(34,214,126,0.1)";
const pc  = (sev) => sev==="critical"?D.red:sev==="high"?D.amb:D.blu;
const pcd = (sev) => sev==="critical"?D.redD:sev==="high"?D.ambD:D.bluD;

function useCount(target, ms=1000, go=true) {
  const [v,setV] = useState(0);
  useEffect(()=>{
    if(!go) return;
    const n=parseFloat(String(target)||"0")||0;
    const dec=String(target).includes(".")?(String(target).split(".")[1]||"").length:0;
    let start=null;
    const tick=(t)=>{
      if(!start) start=t;
      const p=Math.min((t-start)/ms,1), e=1-Math.pow(1-p,3);
      setV(+(n*e).toFixed(dec));
      if(p<1) requestAnimationFrame(tick); else setV(target);
    };
    requestAnimationFrame(tick);
  },[go,target,ms]);
  return v;
}

function Label({children}){
  return <div style={{fontSize:9,fontWeight:700,letterSpacing:2,color:D.t3,textTransform:"uppercase",marginBottom:12}}>{children}</div>;
}

function RangeDot({v,lo,hi,s}){
  const safeV=v||0, safeLo=lo||0, safeHi=hi||1;
  const pct=Math.max(3,Math.min(93,((safeV-safeLo)/Math.max(safeHi-safeLo,1))*100));
  return(
    <div style={{position:"relative",height:3,background:"rgba(255,255,255,0.07)",borderRadius:99,width:52}}>
      <div style={{position:"absolute",left:`${pct}%`,top:-2,width:7,height:7,borderRadius:"50%",background:sc(s),transform:"translateX(-50%)",boxShadow:`0 0 5px ${sc(s)}99`}}/>
    </div>
  );
}

function MiniArc({pct,color}){
  const r=28,circ=Math.PI*r,fill=Math.min(pct||0,1)*circ;
  return(
    <svg width="64" height="34" viewBox="0 0 64 34" style={{display:"block"}}>
      <path d="M6,30 A28,28 0 0,1 58,30" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={4} strokeLinecap="round"/>
      <path d="M6,30 A28,28 0 0,1 58,30" fill="none" stroke={color||D.grn} strokeWidth={4} strokeLinecap="round"
        strokeDasharray={`${fill} ${circ}`}
        style={{filter:`drop-shadow(0 0 3px ${color||D.grn}88)`,transition:"stroke-dasharray 1.2s cubic-bezier(.4,0,.2,1)"}}/>
    </svg>
  );
}

function SBadge({s}){
  const status = s||"NORMAL";
  return <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,background:sf(status),color:sc(status),border:`1px solid ${sc(status)}20`}}>
    {status==="HIGH"?"HIGH":status==="LOW"?"LOW":"NORMAL"}
  </span>;
}

const LOGOS=[
  {name:"qure.ai",tag:"AI Radiology"},{name:"Wadhwani AI",tag:"Health Intelligence"},
  {name:"Apollo 24|7",tag:"Digital Health"},{name:"Practo",tag:"Healthcare Platform"},
  {name:"1mg Health",tag:"Diagnostics & Pharma"},{name:"SRL Diagnostics",tag:"Lab Sciences"},
  {name:"Metropolis",tag:"Pathology Network"},{name:"Narayana Health",tag:"Cardiac Care"},
  {name:"Fortis Healthcare",tag:"Hospital Group"},{name:"Medanta",tag:"Medical Institute"},
  {name:"Thyrocare",tag:"Lab Network"},{name:"mfine",tag:"AI Doctor Platform"},
];

function Marquee(){
  const items=[...LOGOS,...LOGOS];
  return(
    <div style={{overflow:"hidden",position:"relative",borderTop:`1px solid ${D.bd}`,borderBottom:`1px solid ${D.bd}`,padding:"14px 0",background:`linear-gradient(90deg,${D.bg} 0%,transparent 8%,transparent 92%,${D.bg} 100%)`}}>
      <div style={{display:"flex",animation:"marquee 28s linear infinite",width:"max-content"}}>
        {items.map((l,i)=>(
          <div key={i} style={{display:"flex",alignItems:"center",gap:10,padding:"0 36px",borderRight:`1px solid ${D.bd}`,flexShrink:0}}>
            <div style={{width:28,height:28,borderRadius:7,background:D.card,border:`1px solid ${D.bd}`,display:"flex",alignItems:"center",justifyContent:"center"}}>
              <div style={{width:10,height:10,borderRadius:2,background:D.em,opacity:0.7}}/>
            </div>
            <div>
              <div style={{fontSize:11,fontWeight:700,color:D.t2,whiteSpace:"nowrap"}}>{l.name}</div>
              <div style={{fontSize:9,color:D.t3,whiteSpace:"nowrap"}}>{l.tag}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function UploadScreen({onResult}){
  const [status,setStatus]=useState("idle");
  const [progress,setProgress]=useState(0);
  const [rows,setRows]=useState([]);
  const [parsePct,setParsePct]=useState(0);
  const [scanPct,setScanPct]=useState(0);
  const [error,setError]=useState("");
  const fileRef=useRef();
  const [ready,setReady]=useState(false);
  const [patientName,setPatientName]=useState("");
  const [patientAge,setPatientAge]=useState("");
  const [patientSex,setPatientSex]=useState("Male");

  useEffect(()=>{setTimeout(()=>setReady(true),100);},[]);
  const n1=useCount(35,1200,ready), n2=useCount(94,1400,ready), n3=useCount(6,800,ready);

  const STREAM=[
    {t:"Hemoglobin",v:"11.9 g/dL",s:"LOW"},{t:"TSH",v:"7.964 uIU/mL",s:"HIGH"},
    {t:"ESR",v:"77 mm/hr",s:"HIGH"},{t:"CRP",v:"8.10 mg/L",s:"HIGH"},
    {t:"Iron Serum",v:"54 μg/dL",s:"LOW"},{t:"Vitamin D",v:"12.4 ng/mL",s:"LOW"},
    {t:"UACR",v:"69.02 mg/g",s:"HIGH"},{t:"Folate B9",v:"3.57 ng/mL",s:"LOW"},
    {t:"Uric Acid",v:"7.7 mg/dL",s:"HIGH"},{t:"ALP",v:"123 U/L",s:"HIGH"},
    {t:"Microalbumin",v:"62.00 mg/L",s:"HIGH"},{t:"BUN",v:"28 mg/dL",s:"HIGH"},
  ];

  function runDemoScan(){
    setStatus("demo-scanning"); setScanPct(0); setRows([]); setParsePct(0);
    let p=0;
    const t1=setInterval(()=>{
      p+=1.8; setScanPct(Math.min(p,100));
      if(p>=100){
        clearInterval(t1); setStatus("demo-parsing");
        let i=0;
        const t2=setInterval(()=>{
          setRows(r=>[...r,STREAM[i]]);
          setParsePct(Math.round(((i+1)/STREAM.length)*100));
          i++;
          if(i>=STREAM.length){ clearInterval(t2); setTimeout(()=>onResult(DEMO_ANALYSIS),500); }
        },160);
      }
    },16);
  }

  async function handleFile(file){
    setError("");
    setStatus("uploading"); setProgress(0);
    const fakeProgress=setInterval(()=>setProgress(p=>Math.min(p+3,85)),120);
    try{
      const result=await analyzeReport({file,name:patientName,age:parseInt(patientAge)||0,sex:patientSex});
      clearInterval(fakeProgress); setProgress(100);
      setTimeout(()=>onResult(result),300);
    }catch(e){
      clearInterval(fakeProgress);
      if(e.message.includes("Failed to fetch")||e.message.includes("NetworkError")){
        setError("Backend not running — launching demo mode with sample data.");
        setTimeout(()=>runDemoScan(),1200);
      } else {
        setStatus("idle"); setError(e.message);
      }
    }
  }

  return(
    <div style={{minHeight:"100vh",background:D.bg,display:"flex",flexDirection:"column"}}>
      <nav style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 40px",height:56,borderBottom:`1px solid ${D.bd}`,background:"rgba(8,12,20,0.94)",position:"sticky",top:0,zIndex:100}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="7" fill={D.em}/><path d="M7 13h3l2-5 3 10 2-5h2" stroke="#000" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
          <span style={{fontSize:14,fontWeight:900,color:D.t1,letterSpacing:-.4}}>BioTrack</span>
          <span style={{fontSize:14,fontWeight:400,color:D.em}}>AI</span>
          <div style={{width:1,height:16,background:D.bd,margin:"0 6px"}}/>
          <span style={{fontSize:10,color:D.t3,letterSpacing:1.2,textTransform:"uppercase"}}>Pathology Intelligence</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:6}}>
          {["Product","Research","Docs"].map(l=><span key={l} style={{fontSize:12,color:D.t2,padding:"4px 12px",cursor:"pointer"}}>{l}</span>)}
          <div style={{padding:"7px 18px",borderRadius:8,background:D.em,fontSize:12,fontWeight:700,color:"#000",cursor:"pointer"}}>Request Access</div>
        </div>
      </nav>

      <div style={{flex:1,display:"flex",flexDirection:"column"}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",flex:1,maxHeight:"calc(100vh - 97px)"}}>
          <div style={{padding:"52px 56px",display:"flex",flexDirection:"column",justifyContent:"center",borderRight:`1px solid ${D.bd}`}}>
            <div style={{display:"inline-flex",alignItems:"center",gap:7,padding:"5px 12px",background:D.emD,border:`1px solid ${D.emB}`,borderRadius:20,fontSize:10,fontWeight:700,color:D.em,letterSpacing:.5,marginBottom:24,width:"fit-content"}}>
              <div style={{width:5,height:5,borderRadius:"50%",background:D.em,boxShadow:`0 0 6px ${D.em}`,animation:"pulse 2s infinite"}}/>
              LIVE · OCR + AI Pipeline Active
            </div>
            <h1 style={{fontSize:42,fontWeight:900,color:D.t1,lineHeight:1.12,letterSpacing:-1.5,marginBottom:18}}>
              Pathology reports<br/><span style={{color:D.em}}>decoded in seconds.</span>
            </h1>
            <p style={{fontSize:14,color:D.t2,lineHeight:1.85,marginBottom:36,maxWidth:440}}>
              Upload any Indian lab report — TATA 1mg, SRL, Metropolis, JNMC — and get structured biomarker data, AI risk scores, and a physician-grade clinical advisory instantly.
            </p>
            <div style={{display:"flex",gap:32,marginBottom:40}}>
              {[{v:n1+"+",l:"Biomarker panels"},{v:n2+"%",l:"Extraction accuracy"},{v:n3,l:"Critical flags detected"}].map(s=>(
                <div key={s.l}>
                  <div style={{fontSize:26,fontWeight:900,color:D.em,letterSpacing:-.8}}>{s.v}</div>
                  <div style={{fontSize:10,color:D.t3,marginTop:2}}>{s.l}</div>
                </div>
              ))}
            </div>
            <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
              <input placeholder="Patient name" value={patientName} onChange={e=>setPatientName(e.target.value)}
                style={{flex:2,minWidth:160,padding:"9px 14px",borderRadius:8,border:`1px solid ${D.bd2}`,background:"rgba(255,255,255,0.04)",color:D.t1,fontSize:13,outline:"none"}}/>
              <input placeholder="Age" type="number" value={patientAge} onChange={e=>setPatientAge(e.target.value)}
                style={{width:72,padding:"9px 14px",borderRadius:8,border:`1px solid ${D.bd2}`,background:"rgba(255,255,255,0.04)",color:D.t1,fontSize:13,outline:"none"}}/>
              <select value={patientSex} onChange={e=>setPatientSex(e.target.value)}
                style={{padding:"9px 14px",borderRadius:8,border:`1px solid ${D.bd2}`,background:"rgba(255,255,255,0.04)",color:D.t1,fontSize:13,outline:"none"}}>
                <option>Male</option><option>Female</option><option>Other</option>
              </select>
            </div>
            <div style={{display:"flex",gap:10}}>
              <div onClick={()=>fileRef.current?.click()} style={{display:"inline-flex",alignItems:"center",gap:8,padding:"11px 28px",borderRadius:9,background:D.em,fontSize:13,fontWeight:700,color:"#000",cursor:"pointer"}}>
                <svg width="14" height="14" fill="none" viewBox="0 0 14 14"><path d="M7 9V2M4 5l3-3 3 3M2 11.5h10" stroke="#000" strokeWidth="1.4" strokeLinecap="round"/></svg>
                Upload Real Report
              </div>
              <div onClick={runDemoScan} style={{display:"inline-flex",alignItems:"center",gap:6,padding:"11px 22px",borderRadius:9,border:`1px solid ${D.bd2}`,fontSize:13,color:D.t2,cursor:"pointer"}}>
                ▶ Run Demo
              </div>
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png" style={{display:"none"}}
              onChange={e=>{const f=e.target.files?.[0]; if(f) handleFile(f);}}/>
            {error && <div style={{marginTop:12,fontSize:12,color:D.amb}}>{error}</div>}
          </div>

          <div style={{padding:"40px 44px",display:"flex",flexDirection:"column",justifyContent:"center",background:`linear-gradient(135deg,rgba(0,212,170,0.03) 0%,transparent 50%)`}}>
            <div style={{background:"#0A1120",border:`1px solid ${D.bd}`,borderRadius:14,overflow:"hidden",boxShadow:"0 24px 80px rgba(0,0,0,0.6)"}}>
              <div style={{display:"flex",alignItems:"center",gap:6,padding:"12px 16px",borderBottom:`1px solid ${D.bd}`,background:"rgba(255,255,255,0.02)"}}>
                <div style={{width:10,height:10,borderRadius:"50%",background:"#FF5F57"}}/><div style={{width:10,height:10,borderRadius:"50%",background:"#FEBC2E"}}/><div style={{width:10,height:10,borderRadius:"50%",background:"#28C840"}}/>
                <div style={{flex:1,height:18,background:"rgba(255,255,255,0.04)",borderRadius:4,margin:"0 12px",display:"flex",alignItems:"center",justifyContent:"center"}}>
                  <span style={{fontSize:9,color:D.t3}}>biotrack.ai/analyze · Pathology Intelligence Platform</span>
                </div>
              </div>
              {status==="idle" && (
                <div style={{padding:"32px"}}>
                  <div style={{background:"#0D1829",borderRadius:8,padding:"20px 18px",border:`1px solid ${D.bd}`,marginBottom:16}}>
                    <div style={{fontSize:9,color:"rgba(255,255,255,0.15)",letterSpacing:1,marginBottom:14,textTransform:"uppercase"}}>TATA 1mg Labs · Comprehensive Gold Full Body Checkup · OKH2536878</div>
                    {[100,80,120,60,90,70,110,85,95,65].map((w,i)=>(
                      <div key={i} style={{height:2,background:"rgba(255,255,255,0.06)",borderRadius:1,marginBottom:8,width:w+"%"}}/>
                    ))}
                  </div>
                  <div onClick={()=>fileRef.current?.click()} style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"11px",borderRadius:8,border:`1px dashed ${D.emB}`,background:D.emD,cursor:"pointer"}}>
                    <svg width="14" height="14" fill="none" viewBox="0 0 14 14"><path d="M7 9V2M4 5l3-3 3 3M2 11.5h10" stroke={D.em} strokeWidth="1.4" strokeLinecap="round"/></svg>
                    <span style={{fontSize:12,fontWeight:700,color:D.em}}>Drop report or click to upload</span>
                  </div>
                </div>
              )}
              {status==="uploading" && (
                <div style={{padding:"28px"}}>
                  <div style={{fontSize:13,fontWeight:600,color:D.em,marginBottom:16}}>Uploading to OCR pipeline…</div>
                  <div style={{height:2,background:"rgba(255,255,255,0.05)",borderRadius:99,marginBottom:10}}>
                    <div style={{height:"100%",background:D.em,borderRadius:99,width:`${progress}%`,transition:"width .1s linear"}}/>
                  </div>
                  <div style={{fontSize:11,color:D.t3,fontFamily:"monospace"}}>{progress}%</div>
                </div>
              )}
              {(status==="demo-scanning"||status==="demo-parsing") && (
                <div style={{padding:"24px"}}>
                  {status==="demo-scanning" && (
                    <div style={{position:"relative",height:80,background:"#0D1829",borderRadius:8,border:`1px solid ${D.bd}`,overflow:"hidden",marginBottom:14}}>
                      {[16,28,40,52,64,76].map(y=>(
                        <div key={y} style={{position:"absolute",left:12,top:y,height:2,width:50+Math.sin(y)*40+"%",background:"rgba(255,255,255,0.06)",borderRadius:1}}/>
                      ))}
                      <div style={{position:"absolute",left:0,right:0,top:`${scanPct}%`,height:1.5,background:`linear-gradient(90deg,transparent,${D.em},transparent)`,boxShadow:`0 0 10px ${D.em}`,transition:"top .016s linear"}}/>
                    </div>
                  )}
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                    <span style={{fontSize:11,fontWeight:600,color:D.em}}>{status==="demo-scanning"?"OCR scanning…":"Extracting biomarkers…"}</span>
                    <span style={{fontSize:11,color:D.t3,fontFamily:"monospace"}}>{status==="demo-scanning"?Math.round(scanPct):parsePct}%</span>
                  </div>
                  <div style={{height:2,background:"rgba(255,255,255,0.05)",borderRadius:99,marginBottom:14}}>
                    <div style={{height:"100%",background:D.em,borderRadius:99,width:`${status==="demo-scanning"?scanPct:parsePct}%`,transition:"width .1s linear"}}/>
                  </div>
                  <div style={{fontFamily:"monospace",fontSize:10.5,display:"flex",flexDirection:"column",gap:4}}>
                    {rows.slice(-7).map((r,i)=>(
                      <div key={i} style={{display:"flex",justifyContent:"space-between",padding:"4px 8px",borderRadius:5,background:r.s==="HIGH"?D.redD:r.s==="LOW"?D.ambD:"rgba(255,255,255,0.02)",animation:"slideUp .15s ease",borderLeft:`2px solid ${r.s==="HIGH"?D.red:r.s==="LOW"?D.amb:D.t3}`}}>
                        <span style={{color:D.t2}}>{r.t}</span>
                        <span style={{color:r.s==="HIGH"?D.red:r.s==="LOW"?D.amb:D.grn,fontWeight:700}}>{r.v}</span>
                        <span style={{color:r.s==="HIGH"?D.red:r.s==="LOW"?D.amb:D.grn}}>{r.s==="HIGH"?"↑ HIGH":r.s==="LOW"?"↓ LOW":"✓"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div style={{display:"flex",gap:20,marginTop:18,justifyContent:"center",flexWrap:"wrap"}}>
              {["HIPAA Compliant","ISO 27001","NABL Referenced","HL7 FHIR Ready"].map(b=>(
                <div key={b} style={{display:"flex",alignItems:"center",gap:5,fontSize:9,color:D.t3}}>
                  <svg width="10" height="10" fill="none" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4.5" stroke={D.t3} strokeWidth="1"/><path d="M3 5l1.5 1.5L7 3.5" stroke={D.t3} strokeWidth="1" strokeLinecap="round"/></svg>
                  {b}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{flexShrink:0}}>
          <div style={{textAlign:"center",padding:"10px 0 8px",fontSize:9,letterSpacing:2.5,color:D.t3,textTransform:"uppercase"}}>Trusted by India's leading health organisations</div>
          <Marquee/>
        </div>
      </div>
    </div>
  );
}

function Dashboard({data, onBack}){
  const [tab,setTab]     = useState("overview");
  const [open,setOpen]   = useState(null);
  const [filter,setFilter] = useState("all");
  const [mounted,setMounted] = useState(false);

  // ── all hooks first ──────────────────────────────────────
  const bm      = Array.isArray(data?.biomarkers) ? data.biomarkers : [];
  const rawAbn  = Array.isArray(data?.abnormal)   ? data.abnormal   : bm.filter(b=>b&&b.status!=="NORMAL");
  const abn     = rawAbn.filter(Boolean);
  const alerts  = Array.isArray(data?.alerts)       ? data.alerts.filter(Boolean)       : [];
  const risks   = Array.isArray(data?.risk_scores)  ? data.risk_scores.filter(Boolean)  : [];
  const sysh    = Array.isArray(data?.system_health)? data.system_health.filter(Boolean) : [];
  const adv     = data?.advisory || {summary:"",sections:[]};
  const sections= Array.isArray(adv.sections) ? adv.sections.filter(Boolean) : [];
  const pat     = data?.patient  || {};
  const stats   = data?.stats    || {total:bm.length,abnormal:abn.length,critical_flags:0,systems_reviewed:8};

  const keyMarkers = ["Hemoglobin","TSH","ESR","Vitamin D"];
  const keyBm = keyMarkers.map(n=>bm.find(b=>b&&b.name===n)).filter(Boolean);

  const hb  = useCount(keyBm[0]?.value||0, 1100, mounted);
  const tsh = useCount(keyBm[1]?.value||0, 1300, mounted);
  const esr = useCount(keyBm[2]?.value||0, 900,  mounted);
  const vd  = useCount(keyBm[3]?.value||0, 1200, mounted);
  const gaugeVals = [hb,tsh,esr,vd];

  useEffect(()=>{setTimeout(()=>setMounted(true),80);},[]);

  // ── guard after all hooks ────────────────────────────────
  if(!data || !data.biomarkers) return null;

  const groups = {};
  bm.filter(Boolean).forEach(b=>{
    const g = b.group||"General";
    if(!groups[g]) groups[g]=[];
    groups[g].push(b);
  });

  return(
    <div style={{height:"100vh",display:"flex",flexDirection:"column",background:D.bg,overflow:"hidden"}}>
      <nav style={{height:50,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 20px",borderBottom:`1px solid ${D.bd}`,background:"rgba(8,12,20,0.96)",flexShrink:0,zIndex:100}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <svg width="22" height="22" viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="7" fill={D.em}/><path d="M7 13h3l2-5 3 10 2-5h2" stroke="#000" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
          <span style={{fontSize:13,fontWeight:900,color:D.t1,letterSpacing:-.3}}>BioTrack AI</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:8,background:D.card,border:`1px solid ${D.bd}`,borderRadius:8,padding:"5px 14px"}}>
          <div style={{width:22,height:22,borderRadius:"50%",background:D.emD,border:`1px solid ${D.emB}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:800,color:D.em}}>
            {(pat.name||"?")[0]||"?"}
          </div>
          <div>
            <div style={{fontSize:11.5,fontWeight:700,color:D.t1}}>{pat.name||"Patient"}{pat.age?` · ${pat.age}y`:""}{pat.sex?` ${pat.sex}`:""}</div>
            <div style={{fontSize:9,color:D.t3}}>{data.patient_id_lab||"Lab ID"} · {data.report_date||"Report Date"}</div>
          </div>
          <div style={{width:1,height:18,background:D.bd,margin:"0 2px"}}/>
          <div style={{fontSize:10,fontWeight:700,color:D.red,padding:"2px 8px",borderRadius:5,background:D.redD,border:`1px solid ${D.red}28`}}>{stats.abnormal} Abnormal</div>
        </div>
        <div style={{display:"flex",background:D.card,border:`1px solid ${D.bd}`,borderRadius:9,padding:3,gap:1}}>
          {[["overview","Overview"],["report","Full Report"],["advisory","Advisory"]].map(([id,lbl])=>(
            <button key={id} onClick={()=>setTab(id)} style={{padding:"5px 15px",borderRadius:7,fontSize:11.5,fontWeight:tab===id?700:400,border:"none",cursor:"pointer",transition:"all .15s",background:tab===id?D.em:"transparent",color:tab===id?"#000":D.t2}}>{lbl}</button>
          ))}
        </div>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div style={{display:"flex",alignItems:"center",gap:6}}>
            <div style={{width:6,height:6,borderRadius:"50%",background:D.grn,boxShadow:`0 0 5px ${D.grn}`}}/>
            <span style={{fontSize:11,color:D.t3}}>{data.lab_name||"Lab"}</span>
          </div>
          <button onClick={onBack} style={{padding:"5px 14px",borderRadius:7,fontSize:11,border:`1px solid ${D.bd}`,background:"transparent",color:D.t2,cursor:"pointer"}}>+ New Report</button>
        </div>
      </nav>

      <div style={{flex:1,overflow:"auto"}}>
        {tab==="overview" && (
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 280px",height:"100%"}}>
            {/* Col 1 – Key biomarkers + abnormal list */}
            <div style={{borderRight:`1px solid ${D.bd}`,padding:"20px 22px",overflow:"auto"}}>
              <Label>Key Biomarkers</Label>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:20}}>
                {keyBm.map((m,i)=>(
                  <div key={m.name||i} style={{background:D.card,border:`1px solid ${D.bd}`,borderTop:`2px solid ${sc(m.status||"NORMAL")}`,borderRadius:11,padding:"14px 14px",animation:"fadeUp .3s ease both"}}>
                    <div style={{fontSize:10,color:D.t2,marginBottom:1}}>{m.name}</div>
                    <div style={{display:"flex",alignItems:"baseline",gap:4,marginBottom:10}}>
                      <span style={{fontSize:27,fontWeight:900,color:sc(m.status||"NORMAL"),letterSpacing:-.8,lineHeight:1}}>{gaugeVals[i]}</span>
                      <span style={{fontSize:10,color:D.t3}}>{m.unit||""}</span>
                      <span style={{marginLeft:"auto",fontSize:9,fontWeight:700,padding:"2px 6px",borderRadius:4,background:sf(m.status||"NORMAL"),color:sc(m.status||"NORMAL")}}>{m.status||"NORMAL"}</span>
                    </div>
                    <MiniArc pct={Math.max(0,Math.min(1,((m.value||0)-(m.ref_low||0))/Math.max((m.ref_high||1)-(m.ref_low||0),1)))} color={sc(m.status||"NORMAL")}/>
                    <div style={{fontSize:9,color:D.t3,marginTop:3}}>Ref {m.ref_low}–{m.ref_high}</div>
                  </div>
                ))}
              </div>
              <Label>All Abnormal Results</Label>
              <div style={{display:"flex",flexDirection:"column",gap:1}}>
                {abn.map((m,i)=>(
                  <div key={i} style={{display:"flex",alignItems:"center",gap:8,padding:"7px 10px",borderRadius:8}}>
                    <div style={{width:2.5,height:20,borderRadius:99,background:sc(m.status||"NORMAL"),flexShrink:0}}/>
                    <span style={{fontSize:11,color:D.t2,flex:1}}>{m.name||"—"}</span>
                    <span style={{fontSize:12,fontWeight:700,color:sc(m.status||"NORMAL"),fontFamily:"monospace",minWidth:44,textAlign:"right"}}>{m.value}</span>
                    <span style={{fontSize:9.5,color:D.t3,width:40}}>{m.unit||""}</span>
                    <RangeDot v={m.value||0} lo={m.ref_low} hi={m.ref_high} s={m.status||"NORMAL"}/>
                    <SBadge s={m.status||"NORMAL"}/>
                  </div>
                ))}
              </div>
            </div>

            {/* Col 2 – Alerts */}
            <div style={{borderRight:`1px solid ${D.bd}`,padding:"20px 20px",overflow:"auto"}}>
              <Label>Clinical Findings — {alerts.length} Flagged</Label>
              <div style={{display:"flex",flexDirection:"column",gap:9}}>
                {alerts.map((f,i)=>{
                  if(!f) return null;
                  const sev = f.severity||"moderate";
                  return(
                    <div key={i} style={{background:D.card,border:`1px solid ${pc(sev)}1E`,borderLeft:`2px solid ${pc(sev)}`,borderRadius:11,overflow:"hidden",animation:`fadeUp .3s ease ${i*.055}s both`}}>
                      <div style={{display:"flex",alignItems:"flex-start",gap:10,padding:"12px 14px",borderBottom:`1px solid rgba(255,255,255,0.04)`}}>
                        <div style={{position:"relative",width:7,height:7,flexShrink:0,marginTop:3}}>
                          <div style={{width:7,height:7,borderRadius:"50%",background:pc(sev),boxShadow:`0 0 6px ${pc(sev)}`}}/>
                          {sev==="critical" && <div style={{position:"absolute",inset:-3,borderRadius:"50%",border:`1px solid ${pc(sev)}`,animation:"ripple 1.6s ease-out infinite"}}/>}
                        </div>
                        <div style={{flex:1,minWidth:0}}>
                          <div style={{fontSize:12,fontWeight:700,color:D.t1,marginBottom:2}}>{f.title||""}</div>
                          <div style={{fontSize:10,color:pc(sev),fontFamily:"monospace"}}>{f.marker||""}: {f.value} {f.unit||""}</div>
                        </div>
                        <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,flexShrink:0,background:pcd(sev),color:pc(sev),border:`1px solid ${pc(sev)}28`}}>{f.system||""}</span>
                      </div>
                      <p style={{fontSize:11,color:D.t2,lineHeight:1.75,margin:0,padding:"9px 14px"}}>{f.detail||""}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Col 3 – System health */}
            <div style={{padding:"20px 16px",overflow:"auto"}}>
              <Label>System Health</Label>
              {sysh.map((s,i)=>{
                if(!s) return null;
                return(
                  <div key={s.name||i} style={{marginBottom:11}}>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
                      <span style={{fontSize:11,color:D.t2}}>{s.name||""}</span>
                      <div style={{display:"flex",alignItems:"center",gap:6}}>
                        <span style={{fontSize:9,color:D.t3}}>{s.flags||0} flag{(s.flags||0)!==1?"s":""}</span>
                        <span style={{fontSize:12,fontWeight:800,color:s.color||D.grn,fontFamily:"monospace"}}>{s.score||0}</span>
                      </div>
                    </div>
                    <div style={{height:3,background:"rgba(255,255,255,0.05)",borderRadius:99}}>
                      <div style={{height:"100%",background:s.color||D.grn,borderRadius:99,width:`${s.score||0}%`,boxShadow:`0 0 5px ${s.color||D.grn}55`,transition:`width 1.2s cubic-bezier(.4,0,.2,1) ${i*.06}s`}}/>
                    </div>
                  </div>
                );
              })}
              <div style={{marginTop:18,background:D.card,border:`1px solid ${D.bd}`,borderRadius:10,padding:"14px 14px"}}>
                <Label>Report Summary</Label>
                {[
                  {l:"Total tests run",   v:String(stats.total||0),            c:D.em},
                  {l:"Abnormal results",  v:String(stats.abnormal||0),          c:D.red},
                  {l:"Critical flags",    v:String(stats.critical_flags||0),    c:D.amb},
                  {l:"Systems reviewed",  v:String(stats.systems_reviewed||0),  c:D.blu},
                ].map(r=>(
                  <div key={r.l} style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
                    <span style={{fontSize:11,color:D.t2}}>{r.l}</span>
                    <span style={{fontSize:15,fontWeight:900,color:r.c,fontFamily:"monospace"}}>{r.v}</span>
                  </div>
                ))}
              </div>
              <div style={{marginTop:12,padding:"9px 11px",borderRadius:8,background:"rgba(255,255,255,0.015)",borderLeft:`2px solid ${D.t4}`,fontSize:10,color:D.t3,lineHeight:1.7}}>
                For clinical decision support only. All findings require physician review.
              </div>
            </div>
          </div>
        )}

        {tab==="report" && (
          <div style={{padding:"20px 24px"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
              <Label>Complete Panel · {data.report_date||""} · {bm.length} Tests · {data.lab_name||""}</Label>
              <div style={{display:"flex",gap:4}}>
                {[["all","All"],["abn","Abnormal only"]].map(([id,lbl])=>(
                  <button key={id} onClick={()=>setFilter(id)} style={{padding:"4px 12px",borderRadius:6,fontSize:11,fontWeight:filter===id?700:400,border:"none",cursor:"pointer",background:filter===id?D.em:D.card,color:filter===id?"#000":D.t2}}>{lbl}</button>
                ))}
              </div>
            </div>
            {Object.entries(groups).map(([grp,rows])=>{
              const show = filter==="all" ? rows : rows.filter(r=>r&&r.status!=="NORMAL");
              if(!show.length) return null;
              return(
                <div key={grp} style={{marginBottom:14}}>
                  <div style={{fontSize:9,fontWeight:700,letterSpacing:2,color:D.em,textTransform:"uppercase",marginBottom:6}}>{grp}</div>
                  <div style={{background:D.card,border:`1px solid ${D.bd}`,borderRadius:10,overflow:"hidden"}}>
                    <table style={{width:"100%",borderCollapse:"collapse"}}>
                      <thead><tr style={{background:"rgba(255,255,255,0.018)"}}>
                        {["Test","Value","Unit","Ref Range","","Status"].map(h=>(
                          <th key={h} style={{padding:"8px 16px",textAlign:"left",fontSize:9,letterSpacing:1.5,textTransform:"uppercase",color:D.t3,fontWeight:700,borderBottom:`1px solid ${D.bd}`}}>{h}</th>
                        ))}
                      </tr></thead>
                      <tbody>
                        {show.filter(Boolean).map((m,i)=>(
                          <tr key={i} style={{borderBottom:i<show.length-1?`1px solid rgba(255,255,255,0.03)`:"none",background:m.status!=="NORMAL"?"rgba(255,255,255,0.012)":"transparent"}}>
                            <td style={{padding:"9px 16px",fontSize:12,color:m.status!=="NORMAL"?D.t1:D.t2,fontWeight:m.status!=="NORMAL"?600:400}}>{m.name||""}</td>
                            <td style={{padding:"9px 16px",fontSize:13,fontWeight:800,color:sc(m.status||"NORMAL"),fontFamily:"monospace"}}>{m.value}</td>
                            <td style={{padding:"9px 16px",fontSize:11,color:D.t3}}>{m.unit||""}</td>
                            <td style={{padding:"9px 16px",fontSize:11,color:D.t3,fontFamily:"monospace"}}>{m.ref_low}–{m.ref_high}</td>
                            <td style={{padding:"9px 16px"}}><RangeDot v={m.value||0} lo={m.ref_low} hi={m.ref_high} s={m.status||"NORMAL"}/></td>
                            <td style={{padding:"9px 16px"}}><SBadge s={m.status||"NORMAL"}/></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab==="advisory" && (
          <div style={{padding:"20px 24px",maxWidth:820}}>
            <div style={{background:`linear-gradient(120deg,${D.redD},${D.ambD})`,border:`1px solid rgba(255,64,96,0.18)`,borderRadius:13,padding:"18px 22px",marginBottom:18}}>
              <div style={{fontSize:9,fontWeight:700,letterSpacing:2,color:D.red,textTransform:"uppercase",marginBottom:10}}>AI Clinical Narrative</div>
              <p style={{fontSize:13,color:D.t2,lineHeight:1.9,margin:0}}>{adv.summary||""}</p>
            </div>
            {sections.map((s,i)=>{
              if(!s) return null;
              const color = s.color||D.bd;
              return(
                <div key={i} style={{background:D.card,border:`1px solid ${color}1A`,borderLeft:`2px solid ${color}`,borderRadius:10,overflow:"hidden",marginBottom:8,animation:`fadeUp .25s ease ${i*.06}s both`}}>
                  <div onClick={()=>setOpen(open===i?null:i)} style={{display:"flex",alignItems:"center",gap:10,padding:"12px 16px",cursor:"pointer"}}>
                    <span style={{fontSize:13}}>{s.icon||""}</span>
                    <div style={{flex:1}}>
                      <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                        <span style={{fontSize:12,fontWeight:700,color:D.t1}}>{s.key||""}</span>
                        <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,background:`${color}1A`,color}}>{s.tag||""}</span>
                      </div>
                      <div style={{fontSize:10,color:D.t3,marginTop:2,fontFamily:"monospace"}}>{s.values||""}</div>
                    </div>
                    <svg width="14" height="14" fill="none" viewBox="0 0 14 14" style={{transform:open===i?"rotate(180deg)":"none",transition:"transform .2s",flexShrink:0}}>
                      <path d="M3 5l4 4 4-4" stroke={D.t3} strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                  </div>
                  {open===i && (
                    <div style={{padding:"2px 16px 14px 42px",borderTop:`1px solid rgba(255,255,255,0.04)`}}>
                      {(Array.isArray(s.recs)?s.recs:[]).map((r,j)=>(
                        <div key={j} style={{display:"flex",gap:9,marginTop:10}}>
                          <span style={{color,fontSize:11,flexShrink:0,marginTop:2}}>→</span>
                          <span style={{fontSize:12,color:D.t2,lineHeight:1.7}}>{r}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
            <div style={{marginTop:14,padding:"10px 14px",borderRadius:8,background:"rgba(255,255,255,0.018)",borderLeft:`2px solid ${D.t4}`,fontSize:10,color:D.t3,lineHeight:1.65}}>
              This advisory is AI-generated for clinical decision support only. Not a substitute for physician diagnosis. All recommendations must be reviewed by a qualified medical professional.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App(){
  const [screen,setScreen] = useState("upload");
  const [data,setData]     = useState(null);

  function handleResult(result){ setData(result); setScreen("dashboard"); }
  function handleBack(){ setScreen("upload"); setData(null); }

  return(
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        body{background:#080C14;overflow:hidden}
        button,input,select{font-family:inherit}
        input::placeholder{color:#3D5272}
        @keyframes marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
        @keyframes ripple{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.6);opacity:0}}
        @keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
        @keyframes slideUp{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.07);border-radius:99px}
      `}</style>
      <div style={{fontFamily:"'DM Sans',sans-serif",color:"#F0F4FF",background:"#080C14",minHeight:"100vh",fontSize:13,letterSpacing:-.1}}>
        {screen==="upload"
          ? <UploadScreen onResult={handleResult}/>
          : <Dashboard data={data} onBack={handleBack}/>
        }
      </div>
    </>
  );
}