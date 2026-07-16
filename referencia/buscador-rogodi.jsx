import React, { useState, useMemo } from "react";
import { Search, Package, AlertCircle, CheckCircle2, Zap, TrendingUp, X, ArrowRight, Sparkles } from "lucide-react";

// quitar acentos y normalizar (usado en todo el archivo)
const norm = (s) => String(s||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"").trim();

// ============================================================
// DATOS REALES extraÃ­dos del catÃ¡logo de ROGODI
// (Foco Luz Principal Â· LED COB) â muestra para la demo
// ============================================================
const PRODUCTOS = [
  {codigo:"124-0300-03",desc:"FOCO LED CHIP COB 9004 H/L 3 CARAS 6000K 9/36V",linea:"BASE",tipo:"9004",caras:3,volt:"9/36V",precio:139.99,exist:48},
  {codigo:"124-1100-03",desc:"FOCO LED CHIP COB ALPHA-X 9004 H/L 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"9004",caras:10,volt:"9/36V",precio:739.00,exist:0},
  {codigo:"124-1100-09",desc:"FOCO LED CHIP COB ALPHA-X 9005 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"9005",caras:10,volt:"9/36V",precio:655.00,exist:2},
  {codigo:"124-1100-10",desc:"FOCO LED CHIP COB ALPHA-X 9006 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"9006",caras:10,volt:"9/36V",precio:655.00,exist:5},
  {codigo:"124-1100-04",desc:"FOCO LED CHIP COB ALPHA-X 9007 H/L 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"9007",caras:10,volt:"9/36V",precio:739.00,exist:0},
  {codigo:"124-1100-08",desc:"FOCO LED CHIP COB ALPHA-X H11 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"H11",caras:10,volt:"9/36V",precio:625.00,exist:2},
  {codigo:"124-1100-01",desc:"FOCO LED CHIP COB ALPHA-X H4 H/L 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"H4",caras:10,volt:"9/36V",precio:739.00,exist:0},
  {codigo:"124-1100-07",desc:"FOCO LED CHIP COB ALPHA-X H7 10 CARAS 9/36V",linea:"ALPHA-X",tipo:"H7",caras:10,volt:"9/36V",precio:655.01,exist:2},
  {codigo:"124-1001-02",desc:"FOCO LED CHIP COB CONCORD 9004 H/L MULTICOLOR",linea:"CONCORD",tipo:"9004",caras:null,volt:null,precio:599.00,exist:11},
  {codigo:"124-1001-03",desc:"FOCO LED CHIP COB CONCORD 9007 H/L MULTICOLOR",linea:"CONCORD",tipo:"9007",caras:null,volt:null,precio:599.00,exist:9},
  {codigo:"124-1001-05",desc:"FOCO LED CHIP COB CONCORD H1 MULTICOLOR",linea:"CONCORD",tipo:"H1",caras:null,volt:null,precio:643.00,exist:5},
  {codigo:"124-1001-04",desc:"FOCO LED CHIP COB CONCORD H13 H/L MULTICOLOR",linea:"CONCORD",tipo:"H13",caras:null,volt:null,precio:689.00,exist:2},
  {codigo:"124-1001-06",desc:"FOCO LED CHIP COB CONCORD H3 MULTICOLOR",linea:"CONCORD",tipo:"H3",caras:null,volt:null,precio:643.00,exist:10},
  {codigo:"124-1001-01",desc:"FOCO LED CHIP COB CONCORD H4 H/L MULTICOLOR",linea:"CONCORD",tipo:"H4",caras:null,volt:null,precio:565.00,exist:4},
  {codigo:"124-1004-01",desc:"FOCO LED CHIP COB CONCORD H4 MULTICOLOR CON ESTROBO 9/36V",linea:"CONCORD",tipo:"H4",caras:null,volt:"9/36V",precio:745.00,exist:0},
  {codigo:"124-1001-07",desc:"FOCO LED CHIP COB CONCORD H7 MULTICOLOR",linea:"CONCORD",tipo:"H7",caras:null,volt:null,precio:643.00,exist:0},
  {codigo:"124-0415-03",desc:"FOCO LED CHIP COB ECO 9004 H/L 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"9004",caras:4,volt:"9/36V",precio:285.00,exist:13},
  {codigo:"124-0415-09",desc:"FOCO LED CHIP COB ECO 9005 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"9005",caras:4,volt:"9/36V",precio:245.00,exist:15},
  {codigo:"124-0415-04",desc:"FOCO LED CHIP COB ECO 9007 H/L 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"9007",caras:4,volt:"9/36V",precio:285.00,exist:21},
  {codigo:"124-0415-08",desc:"FOCO LED CHIP COB ECO H11 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"H11",caras:4,volt:"9/36V",precio:245.00,exist:55},
  {codigo:"124-0415-02",desc:"FOCO LED CHIP COB ECO H13 H/L 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"H13",caras:4,volt:"9/36V",precio:285.00,exist:11},
  {codigo:"124-0415-01",desc:"FOCO LED CHIP COB ECO H4 H/L 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"H4",caras:4,volt:"9/36V",precio:285.00,exist:109},
  {codigo:"124-0415-07",desc:"FOCO LED CHIP COB ECO H7 4 CARAS 6000K 9/36V",linea:"ECO",tipo:"H7",caras:4,volt:"9/36V",precio:245.00,exist:69},
  {codigo:"124-0200-03",desc:"FOCO LED CHIP COB GEMINIS 9004 H/L 2 CARAS 9/36V",linea:"GEMINIS",tipo:"9004",caras:2,volt:"9/36V",precio:247.00,exist:0},
  {codigo:"124-0200-08",desc:"FOCO LED CHIP COB GEMINIS 9006 2 CARAS 9/36V",linea:"GEMINIS",tipo:"9006",caras:2,volt:"9/36V",precio:165.00,exist:5},
  {codigo:"124-0200-01",desc:"FOCO LED CHIP COB GEMINIS H4 H/L 2 CARAS 9/36V",linea:"GEMINIS",tipo:"H4",caras:2,volt:"9/36V",precio:247.00,exist:5},
  {codigo:"124-0230-01",desc:"FOCO LED CHIP COB H4 H/L CON CAMBUS BLANCO/AMBAR/ROJO Y AZUL 9/36V",linea:"CAMBUS",tipo:"H4",caras:null,volt:"9/36V",precio:589.00,exist:23},
  {codigo:"124-1003-01",desc:"FOCO LED CHIP COB ROYAL H4 MULTICOLOR CON ESTROBO 9/36V",linea:"ROYAL",tipo:"H4",caras:null,volt:"9/36V",precio:589.00,exist:13},
  {codigo:"124-0400-03",desc:"FOCO LED CHIP COB SPYDER 9004 H/L 4 CARAS 12/24V",linea:"SPYDER",tipo:"9004",caras:4,volt:"12/24V",precio:455.00,exist:34},
  {codigo:"124-0400-09",desc:"FOCO LED CHIP COB SPYDER 9005 4 CARAS 12/24V",linea:"SPYDER",tipo:"9005",caras:4,volt:"12/24V",precio:395.00,exist:53},
  {codigo:"124-0400-10",desc:"FOCO LED CHIP COB SPYDER 9006 CARAS 12/24V",linea:"SPYDER",tipo:"9006",caras:4,volt:"12/24V",precio:395.00,exist:19},
  {codigo:"124-0400-04",desc:"FOCO LED CHIP COB SPYDER 9007 H/L 4 CARAS 12/24V",linea:"SPYDER",tipo:"9007",caras:4,volt:"12/24V",precio:455.00,exist:51},
  {codigo:"124-0400-05",desc:"FOCO LED CHIP COB SPYDER H1 4 CARAS 12/24V",linea:"SPYDER",tipo:"H1",caras:4,volt:"12/24V",precio:395.00,exist:9},
  {codigo:"124-0400-08",desc:"FOCO LED CHIP COB SPYDER H11 4 CARAS 12/24V",linea:"SPYDER",tipo:"H11",caras:4,volt:"12/24V",precio:395.00,exist:69},
  {codigo:"124-0400-02",desc:"FOCO LED CHIP COB SPYDER H13 H/L 4 CARAS 12/24V",linea:"SPYDER",tipo:"H13",caras:4,volt:"12/24V",precio:455.00,exist:19},
  {codigo:"124-0400-06",desc:"FOCO LED CHIP COB SPYDER H3 4 CARAS 12/24V",linea:"SPYDER",tipo:"H3",caras:4,volt:"12/24V",precio:395.00,exist:8},
  {codigo:"124-0400-01",desc:"FOCO LED CHIP COB SPYDER H4 H/L 4 CARAS 12/24V",linea:"SPYDER",tipo:"H4",caras:4,volt:"12/24V",precio:455.00,exist:101},
  {codigo:"124-0400-07",desc:"FOCO LED CHIP COB SPYDER H7 4 CARAS 12/24V",linea:"SPYDER",tipo:"H7",caras:4,volt:"12/24V",precio:395.00,exist:43},
  {codigo:"124-0600-09",desc:"FOCO LED CHIP COB X-PRO 9005 6 CARAS 12/24V",linea:"X-PRO",tipo:"9005",caras:6,volt:"12/24V",precio:515.00,exist:16},
  {codigo:"124-0600-10",desc:"FOCO LED CHIP COB X-PRO 9006 6 CARAS 12/24V",linea:"X-PRO",tipo:"9006",caras:6,volt:"12/24V",precio:515.00,exist:20},
  {codigo:"124-0600-05",desc:"FOCO LED CHIP COB X-PRO H1 6 CARAS 12/24V",linea:"X-PRO",tipo:"H1",caras:6,volt:"12/24V",precio:515.00,exist:7},
  {codigo:"124-0600-08",desc:"FOCO LED CHIP COB X-PRO H11 6 CARAS 12/24V",linea:"X-PRO",tipo:"H11",caras:6,volt:"12/24V",precio:515.00,exist:27},
  {codigo:"124-0600-02",desc:"FOCO LED CHIP COB X-PRO H13 6 CARAS 12/24V",linea:"X-PRO",tipo:"H13",caras:6,volt:"12/24V",precio:625.00,exist:13},
  {codigo:"124-0600-06",desc:"FOCO LED CHIP COB X-PRO H3 6 CARAS 12/24V",linea:"X-PRO",tipo:"H3",caras:6,volt:"12/24V",precio:515.00,exist:22},
  {codigo:"124-0600-01",desc:"FOCO LED CHIP COB X-PRO H4 H/L 6 CARAS 12/24V",linea:"X-PRO",tipo:"H4",caras:6,volt:"12/24V",precio:625.00,exist:38},
  {codigo:"124-0600-07",desc:"FOCO LED CHIP COB X-PRO H7 6 CARAS 12/24V",linea:"X-PRO",tipo:"H7",caras:6,volt:"12/24V",precio:515.00,exist:39},
  {codigo:"124-0410-04",desc:"FOCO LED CHIP COB ZAFIRO 9007 H/L 4 CARAS CON CAMBUS 9/36V",linea:"ZAFIRO",tipo:"9007",caras:4,volt:"9/36V",precio:599.00,exist:5},
  {codigo:"124-0410-08",desc:"FOCO LED CHIP COB ZAFIRO H11 4 CARAS CON CAMBUS 9/36V",linea:"ZAFIRO",tipo:"H11",caras:4,volt:"9/36V",precio:547.00,exist:3},
  {codigo:"124-0410-02",desc:"FOCO LED CHIP COB ZAFIRO H13 H/L 4 CARAS CON CAMBUS 9/36V",linea:"ZAFIRO",tipo:"H13",caras:4,volt:"9/36V",precio:599.00,exist:3},
  {codigo:"IOL-LHL-341",desc:"SERIE NEW ALLOY 9007 9-32V 65W/PC LED CSP Y CANBUS CON APP ESTROBOSCOPICA",linea:"NEW ALLOY",tipo:"9007",caras:null,volt:"9/32V",precio:1649.00,exist:4},
  {codigo:"IOL-LHL-334",desc:"SERIE NEW ZINC ALLOY APP MOVIL H7 9-32V 65W LED CSP CANBUS 6000K DRL",linea:"NEW ALLOY",tipo:"H7",caras:null,volt:"9/32V",precio:1377.00,exist:4},
];

// Diccionario de sinÃ³nimos para Rogodi
const SINONIMOS = {
  "foco":["foco","bulbo","lampara","lÃ¡mpara","led","luz","faro"],
  "h4":["h4","h-4"],"h7":["h7","h-7"],"h11":["h11","h-11"],"h1":["h1","h-1"],
  "h3":["h3","h-3"],"h13":["h13","h-13"],
  "9004":["9004","hb1"],"9005":["9005","hb3"],"9006":["9006","hb4"],"9007":["9007","hb5"],
  "estrobo":["estrobo","estroboscopico","flash"],
  "multicolor":["multicolor","rgb","colores"],
  "cambus":["cambus","canbus","cambus"],
};

// ============================================================
// TEMPORADAS â quÃ© familias se venden en cada temporada.
// En el catÃ¡logo completo, cada familia (prefijo del cÃ³digo)
// se mapea aquÃ­. En esta demo solo hay focos (familia 124).
// ============================================================
// ============================================================
// ESTACIONALIDAD por familia (prefijo de cÃ³digo) â hipÃ³tesis
// El cÃ³digo empieza con el nÃºmero de familia: 037 = limpiaparabrisas, etc.
// ============================================================
const FAMILIA_NOMBRE = {
  "037":"Limpiaparabrisas","026":"Botaguas","029":"Loderas","035":"Deflector de cofre",
  "092":"Parasoles","067":"Extinguidores","049":"Focos LED","124":"Focos LED",
  "038":"Focos halÃ³geno","070":"Faro alta intensidad","075":"Faro de niebla LED",
  "077":"Unidad LED","078":"Barras LED","050":"Focos interiores","051":"Focos miniatura",
  "002":"Plafones LED","003":"Calaveras","004":"Cuartos punta","005":"Cuartos frontales",
  "006":"Cuartos laterales","105":"Tiras LED","106":"MÃ³dulos LED","109":"Torretas LED",
  "030":"Aromatizantes","040":"Funda volante piel","041":"Funda volante vinipiel",
  "043":"Funda volante reflejante","093":"Perilla volante","094":"Perilla palanca",
  "087":"Adornos universales","112":"Volantes deportivos","129":"Vestiduras asiento",
  "054":"QuÃ­micos limpieza","097":"Armor All","098":"QuÃ­micos",
};

const TEMPORADAS = {
  lluvia: {
    nombre:"Temporada de lluvias", meses:"jun â sep", emoji:"ð§ï¸",
    sinonimos:["lluvia","lluvias","agua","temporal","aguacero","mojado"],
    familias:["037","026","029","035","092"],
    pitch:"Visibilidad y protecciÃ³n contra el agua. Lo que el cliente necesita cuando empieza a llover.",
  },
  finDeAnio: {
    nombre:"Fin de aÃ±o / noches largas", meses:"oct â dic", emoji:"ð",
    sinonimos:["invierno","frio","frÃ­o","noche","oscuro","fin de aÃ±o","navidad","diciembre","iluminacion","iluminaciÃ³n"],
    familias:["049","124","038","070","075","077","078","050","051","002","003","004","005","006","105","106","109"],
    pitch:"Cuando oscurece temprano, la iluminaciÃ³n se dispara. Tu temporada fuerte de focos LED.",
  },
  regalo: {
    nombre:"Regalo y decoraciÃ³n", meses:"nov â dic", emoji:"ð",
    sinonimos:["regalo","navidad","decoracion","decoraciÃ³n","reyes","adorno","obsequio"],
    familias:["030","040","041","043","093","094","087","112","129"],
    pitch:"Compra de impulso y regalo decembrino. Accesorios que se ven y se regalan.",
  },
  verificacion: {
    nombre:"VerificaciÃ³n vehicular", meses:"semestral", emoji:"ð ï¸",
    sinonimos:["verificacion","verificaciÃ³n","revista","verifica","seguridad"],
    familias:["067","037","038","049"],
    pitch:"Lo que la gente repone para pasar la verificaciÃ³n: focos, limpiaparabrisas, extinguidor.",
  },
};

// saca la familia (3 dÃ­gitos iniciales) de un cÃ³digo tipo "124-0400-01"
function familiaDe(codigo){
  const m=String(codigo).match(/^(\d{3})/);
  return m?m[1]:null;
}

// detecta si la bÃºsqueda es por temporada; devuelve la clave o null
function detectarTemporada(q){
  const t=norm(q);
  for(const [clave,temp] of Object.entries(TEMPORADAS)){
    if(temp.sinonimos.some(s=>t.includes(norm(s)))) return clave;
  }
  return null;
}

// productos de una temporada (los que pertenecen a sus familias)
function productosDeTemporada(clave){
  const fams=new Set(TEMPORADAS[clave].familias);
  return PRODUCTOS.filter(p=>fams.has(familiaDe(p.codigo)))
    .sort((a,b)=>(b.exist>0?1:0)-(a.exist>0?1:0));
}

// distancia simple para tolerar errores de escritura (Levenshtein acotado)
function cercano(a,b){
  a=norm(a);b=norm(b);
  if(a===b)return 0;
  if(a.length<2||b.length<2)return 9;
  const m=a.length,n=b.length;
  const d=Array.from({length:m+1},(_,i)=>[i,...Array(n).fill(0)]);
  for(let j=0;j<=n;j++)d[0][j]=j;
  for(let i=1;i<=m;i++)for(let j=1;j<=n;j++)
    d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
  return d[m][n];
}

// detectar la medida (tipo de foco) en el texto de bÃºsqueda
const MEDIDAS=["9004","9005","9006","9007","h11","h13","h4","h7","h3","h1"];
function detectarMedida(q){
  const t=norm(q).replace(/[-\s]/g,"");
  for(const m of MEDIDAS){ if(t.includes(m)) return m.toUpperCase(); }
  return null;
}

function buscar(query){
  const q=norm(query);
  if(!q) return [];

  // Â¿es una bÃºsqueda por temporada? -> filtrar por familias de esa temporada
  const temp=detectarTemporada(query);
  if(temp){
    const fams=TEMPORADAS[temp].familias;
    return PRODUCTOS
      .filter(p=>fams.includes(familiaDe(p.codigo)))
      .map(p=>({...p,score:p.exist>0?100:50}))
      .sort((a,b)=>b.score-a.score || b.exist-a.exist);
  }

  const medida=detectarMedida(query);
  const palabras=q.split(/\s+/).filter(p=>p.length>0);

  return PRODUCTOS.map(p=>{
    let score=0;
    const txt=norm(p.codigo+" "+p.desc+" "+p.linea+" "+p.tipo);

    // match exacto de cÃ³digo
    if(norm(p.codigo)===q){score+=1000;}
    else if(norm(p.codigo).includes(q)){score+=200;}

    // match de medida (lo mÃ¡s importante para focos)
    if(medida && p.tipo===medida){score+=120;}
    else if(medida && p.tipo!==medida){score-=40;}

    // match por palabra (con sinÃ³nimos y tolerancia a errores)
    for(const palabra of palabras){
      if(MEDIDAS.includes(palabra.replace(/[-\s]/g,""))) continue; // ya contada
      // sinÃ³nimos
      let matched=false;
      for(const [base,syns] of Object.entries(SINONIMOS)){
        if(syns.some(s=>s===palabra)){
          if(syns.some(s=>txt.includes(s))){score+=25;matched=true;break;}
        }
      }
      if(matched) continue;
      // contenciÃ³n directa
      if(txt.includes(palabra)){score+=30;}
      else {
        // tolerancia a errores: comparar contra cada token del producto
        const tokens=txt.split(/[\s\-]+/);
        const cerca=tokens.some(t=>t.length>2 && cercano(palabra,t)<=1);
        if(cerca)score+=15;
      }
    }
    return {...p,score};
  }).filter(p=>p.score>0).sort((a,b)=>b.score-a.score);
}

// para un producto agotado, encontrar alternativas (misma medida, en stock)
function alternativas(prod){
  return PRODUCTOS
    .filter(p=>p.tipo===prod.tipo && p.exist>0 && p.codigo!==prod.codigo)
    .sort((a,b)=>{
      // priorizar misma cantidad de caras, luego precio cercano
      const da=Math.abs((a.caras||0)-(prod.caras||0));
      const db=Math.abs((b.caras||0)-(prod.caras||0));
      if(da!==db)return da-db;
      return Math.abs(a.precio-prod.precio)-Math.abs(b.precio-prod.precio);
    }).slice(0,3);
}

const TINTA="#0a0e1a", AMBAR="#f5a623", CIAN="#00d9ff", GRIS="#8b94a8";

function Stock({n}){
  if(n<=0) return <span style={{color:"#ff5470",fontWeight:700,fontSize:12,display:"inline-flex",alignItems:"center",gap:3}}><X size={12}/>Sin stock</span>;
  if(n<5) return <span style={{color:AMBAR,fontWeight:700,fontSize:12}}>â Quedan {n}</span>;
  return <span style={{color:"#2ee6a0",fontWeight:700,fontSize:12,display:"inline-flex",alignItems:"center",gap:3}}><CheckCircle2 size={12}/>{n} disp.</span>;
}

export default function App(){
  const [query,setQuery]=useState("");
  const [sel,setSel]=useState(null);
  const temporadaActiva=useMemo(()=>detectarTemporada(query),[query]);
  const resultados=useMemo(()=>temporadaActiva?productosDeTemporada(temporadaActiva):buscar(query),[query,temporadaActiva]);
  const ejemplos=["H4","foco H11 spyder","9007 led","lluvia","124-0400-01","fin de aÃ±o"];

  return (
    <div style={{fontFamily:"'Inter',system-ui,sans-serif",background:`radial-gradient(circle at 20% 0%, #16203a 0%, ${TINTA} 55%)`,minHeight:"100vh",color:"#e8edf7"}}>
      <div style={{maxWidth:1080,margin:"0 auto",padding:"26px 20px 60px"}}>
        {/* encabezado */}
        <div style={{display:"flex",alignItems:"center",gap:11,marginBottom:5}}>
          <div style={{background:`linear-gradient(135deg,${AMBAR},#ff7a18)`,borderRadius:11,padding:9,display:"flex",boxShadow:`0 0 24px ${AMBAR}55`}}><Zap size={22} color="#0a0e1a" fill="#0a0e1a"/></div>
          <div>
            <div style={{fontSize:23,fontWeight:800,letterSpacing:-0.5,lineHeight:1}}>Buscador ROGODI <span style={{color:AMBAR}}>Pro</span></div>
            <div style={{fontSize:12.5,color:GRIS,marginTop:3}}>Encuentra el foco correcto en segundos â y quÃ© ofrecer cuando no hay stock.</div>
          </div>
        </div>

        {/* barra de bÃºsqueda */}
        <div style={{position:"relative",marginTop:22}}>
          <Search size={20} style={{position:"absolute",left:18,top:"50%",transform:"translateY(-50%)",color:GRIS}}/>
          <input autoFocus value={query} onChange={e=>{setQuery(e.target.value);setSel(null);}}
            placeholder="Escribe medida, lÃ­nea o cÃ³digoâ¦  ej: H4 spyder"
            style={{width:"100%",boxSizing:"border-box",padding:"16px 18px 16px 50px",fontSize:16,borderRadius:14,
              border:`1.5px solid ${query?AMBAR:"#2a3654"}`,background:"#0e1424",color:"#fff",outline:"none",
              boxShadow:query?`0 0 0 4px ${AMBAR}22`:"none",transition:"all .2s"}}/>
          {query && <button onClick={()=>{setQuery("");setSel(null);}} style={{position:"absolute",right:14,top:"50%",transform:"translateY(-50%)",background:"none",border:"none",color:GRIS,cursor:"pointer"}}><X size={18}/></button>}
        </div>

        {/* chips de ejemplo */}
        {!query && (
          <div style={{marginTop:14}}>
            <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
              <span style={{fontSize:12,color:GRIS}}>Prueba:</span>
              {ejemplos.map(e=>(
                <button key={e} onClick={()=>setQuery(e)} style={{background:"#141d33",border:"1px solid #2a3654",color:"#c5cde0",
                  padding:"6px 12px",borderRadius:20,fontSize:12.5,cursor:"pointer",transition:"all .15s"}}
                  onMouseEnter={ev=>ev.currentTarget.style.borderColor=AMBAR}
                  onMouseLeave={ev=>ev.currentTarget.style.borderColor="#2a3654"}>{e}</button>
              ))}
            </div>
            <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center",marginTop:10}}>
              <span style={{fontSize:12,color:GRIS}}>Por temporada:</span>
              {Object.entries(TEMPORADAS).map(([k,t])=>(
                <button key={k} onClick={()=>setQuery(t.sinonimos[0])} style={{background:"#101a2e",border:`1px solid ${CIAN}44`,color:CIAN,
                  padding:"6px 12px",borderRadius:20,fontSize:12.5,cursor:"pointer",transition:"all .15s",display:"inline-flex",alignItems:"center",gap:5}}
                  onMouseEnter={ev=>ev.currentTarget.style.borderColor=CIAN}
                  onMouseLeave={ev=>ev.currentTarget.style.borderColor=CIAN+"44"}>{t.emoji} {t.nombre}</button>
              ))}
            </div>
          </div>
        )}

        {/* aviso demo */}
        {!query && (
          <div style={{marginTop:26,background:"#101728",border:"1px solid #1f2c47",borderRadius:14,padding:"16px 18px",display:"flex",gap:12}}>
            <Sparkles size={20} color={CIAN} style={{flexShrink:0,marginTop:2}}/>
            <div style={{fontSize:13,lineHeight:1.6,color:"#aab4c8"}}>
              <b style={{color:"#e8edf7"}}>DemostraciÃ³n con datos reales de tu catÃ¡logo.</b> CarguÃ© los focos LED COB de Foco Luz Principal ({PRODUCTOS.length} productos reales con sus precios y existencias). Busca por medida (<b style={{color:AMBAR}}>H4, H11, 9007â¦</b>), por lÃ­nea (<b style={{color:AMBAR}}>Spyder, Eco, X-Proâ¦</b>) o por cÃ³digo. Cuando un producto estÃ© agotado, el buscador te dirÃ¡ <b style={{color:CIAN}}>quÃ© alternativa ofrecer al cliente</b>.
            </div>
          </div>
        )}

        {/* resultados */}
        {query && (
          <div style={{marginTop:20}}>
            {/* banner de temporada */}
            {temporadaActiva && (
              <div style={{background:`linear-gradient(135deg,#0e2438,#101a2e)`,border:`1px solid ${CIAN}55`,borderRadius:14,padding:"15px 18px",marginBottom:16,display:"flex",gap:13,alignItems:"center"}}>
                <div style={{fontSize:30}}>{TEMPORADAS[temporadaActiva].emoji}</div>
                <div>
                  <div style={{fontSize:15,fontWeight:800,color:"#fff"}}>{TEMPORADAS[temporadaActiva].nombre} <span style={{color:CIAN,fontSize:12.5,fontWeight:600}}>Â· {TEMPORADAS[temporadaActiva].meses}</span></div>
                  <div style={{fontSize:12.5,color:"#aab4c8",marginTop:2}}>{TEMPORADAS[temporadaActiva].pitch}</div>
                </div>
              </div>
            )}
            <div style={{fontSize:12.5,color:GRIS,marginBottom:12}}>
              {resultados.length>0 ? <>EncontrÃ© <b style={{color:"#e8edf7"}}>{resultados.length}</b> {resultados.length===1?"producto":"productos"}{temporadaActiva?<> de esta temporada</>:detectarMedida(query)&&<> Â· filtrando por medida <b style={{color:AMBAR}}>{detectarMedida(query)}</b></>}</>
              : temporadaActiva ? "En esta demo solo hay focos cargados; con el catÃ¡logo completo aquÃ­ aparecerÃ­an limpiaparabrisas, loderas, botaguas, etc."
              : "Sin coincidencias exactas â revisa la escritura o prueba con la medida (H4, H11â¦)"}
            </div>

            <div style={{display:"flex",flexDirection:"column",gap:10}}>
              {resultados.map(p=>{
                const agotado=p.exist<=0;
                const alts=agotado?alternativas(p):[];
                const abierto=sel===p.codigo;
                return (
                  <div key={p.codigo} style={{background:agotado?"#15101a":"#0f1626",border:`1px solid ${agotado?"#3a2030":"#1f2c47"}`,borderRadius:14,overflow:"hidden",transition:"all .2s"}}>
                    <div style={{display:"flex",alignItems:"center",gap:14,padding:"14px 16px"}}>
                      <div style={{flexShrink:0,width:54,height:54,borderRadius:10,background:"#1a2236",display:"flex",alignItems:"center",justifyContent:"center",border:"1px solid #2a3654"}}>
                        <Package size={22} color={GRIS}/>
                      </div>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                          <span style={{fontFamily:"ui-monospace,monospace",fontSize:12.5,color:AMBAR,fontWeight:700}}>{p.codigo}</span>
                          {p.tipo && <span style={{fontSize:10.5,background:"#1c2740",color:CIAN,padding:"2px 8px",borderRadius:6,fontWeight:700,letterSpacing:.3}}>{p.tipo}</span>}
                          {p.linea && p.linea!=="BASE" && <span style={{fontSize:10.5,background:"#1c2740",color:"#c5cde0",padding:"2px 8px",borderRadius:6,fontWeight:600}}>{p.linea}</span>}
                        </div>
                        <div style={{fontSize:13.5,color:"#dde3f0",marginTop:4,lineHeight:1.35,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{p.desc}</div>
                      </div>
                      <div style={{textAlign:"right",flexShrink:0}}>
                        <div style={{fontSize:17,fontWeight:800,color:"#fff"}}>${p.precio.toLocaleString("es-MX",{minimumFractionDigits:2})}</div>
                        <div style={{marginTop:3}}><Stock n={p.exist}/></div>
                      </div>
                    </div>

                    {/* recomendaciÃ³n cuando estÃ¡ agotado */}
                    {agotado && (
                      <div style={{borderTop:"1px solid #3a2030",background:"#1a0e16",padding:"12px 16px"}}>
                        {alts.length>0 ? (
                          <>
                            <div style={{display:"flex",alignItems:"center",gap:7,fontSize:12,fontWeight:700,color:CIAN,marginBottom:10}}>
                              <TrendingUp size={14}/> Ofrece esta alternativa al cliente (misma medida {p.tipo}, con stock):
                            </div>
                            <div style={{display:"flex",flexDirection:"column",gap:7}}>
                              {alts.map(a=>(
                                <button key={a.codigo} onClick={()=>setQuery(a.codigo)} style={{display:"flex",alignItems:"center",gap:10,background:"#0f1626",border:"1px solid #24416b",borderRadius:10,padding:"9px 12px",cursor:"pointer",textAlign:"left",width:"100%"}}>
                                  <ArrowRight size={15} color={CIAN}/>
                                  <span style={{fontFamily:"ui-monospace,monospace",fontSize:12,color:AMBAR,fontWeight:700}}>{a.codigo}</span>
                                  <span style={{flex:1,fontSize:12.5,color:"#c5cde0",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{a.linea} Â· {a.caras?a.caras+" caras":"â"}</span>
                                  <span style={{fontSize:13,fontWeight:700,color:"#fff"}}>${a.precio.toLocaleString("es-MX")}</span>
                                  <Stock n={a.exist}/>
                                </button>
                              ))}
                            </div>
                          </>
                        ) : (
                          <div style={{display:"flex",alignItems:"center",gap:7,fontSize:12.5,color:"#ff8fa3"}}>
                            <AlertCircle size={14}/> Sin stock y sin alternativa en la misma medida {p.tipo}. Considera pedido especial.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
