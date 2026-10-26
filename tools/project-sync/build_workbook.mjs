import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const out='C:/Users/gavad/Documents/Codex/2026-10-18/let/outputs/Project-Sync-2026-10-25';
const data=JSON.parse(await fs.readFile(`${out}/project-state.json`,'utf8'));
const wb=Workbook.create();
const sheets={};
function col(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
function sheet(name,title,note,headers,rows,widths){
 const s=wb.worksheets.add(name);sheets[name]=s;s.showGridLines=false;
 const end=col(headers.length);s.getRange('A2').values=[[title]];s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#21334A'};
 s.getRange('A3').values=[[note]];s.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:'#536273'};
 s.getRange(`A5:${end}${rows.length+5}`).values=[headers,...rows];
 s.getRange(`A5:${end}${rows.length+5}`).format.font={name:'Arial',size:10};
 s.getRange(`A5:${end}5`).format={fill:'#263D57',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:34,wrapText:true,verticalAlignment:'center',horizontalAlignment:'center'};
 s.getRange(`A6:${end}${rows.length+5}`).format.rowHeight=24;
 s.getRange(`A6:${end}${rows.length+5}`).format.verticalAlignment='center';
 widths.forEach((w,i)=>s.getRange(`${col(i+1)}5:${col(i+1)}${rows.length+5}`).format.columnWidth=w);
 s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(3);
 const t=s.tables.add(`A5:${end}${rows.length+5}`,true,name.replace(/[^A-Za-z]/g,'')+'Data');t.showFilterButton=true;
 return s;
}
function mainWeapon(ws){return ws.find(w=>typeof w.damage==='number'&&w.damage>0)||{};}
const urows=data.units.map(u=>{
 const b=mainWeapon(u.weapons_before),a=mainWeapon(u.weapons_after);
 return [u.faction,u.domain,u.id,u.original,u.replacement,b.damage??null,a.damage??null,b.range??null,a.range??null,u.stats_before.speed,u.stats_after.speed,null,u.stats_before.health,u.stats_after.health,u.installed?'Installed prototype':'Planned only',b.label??'No damaging gun',a.label??'No damaging gun'];
});
const us=sheet('Unit comparison','SC2 conversion and balance snapshot','2026-10-25 | A = primary weapon Damage per projectile/tick; R = MaxRadius; S = MaxSpeed. Base DLC values; no research buffs.',
 ['Faction','Domain','Unit ID','Original unit','Replacement','A vanilla','A current','R vanilla','R current','S vanilla','S current','Speed change','HP vanilla','HP current','Implementation','Vanilla A/R weapon','Current A/R weapon'],urows,[12,12,16,27,52,14,14,14,14,14,14,16,15,15,24,30,30]);
for(let i=0;i<urows.length;i++){const r=i+6;us.getRange(`L${r}`).formulas=[[`=IF(AND(ISNUMBER(J${r}),ISNUMBER(K${r})),IF(J${r}=0,"n.a.",K${r}/J${r}-1),"n.a.")`]];}
us.getRange(`F6:K${urows.length+5}`).setNumberFormat('0.###');us.getRange(`L6:L${urows.length+5}`).setNumberFormat('0.00%');us.getRange(`M6:N${urows.length+5}`).setNumberFormat('#,##0.##');
us.getRange(`L6:L${urows.length+5}`).conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FFF1CE'}});
const mrows=data.metrics.map(m=>[m.faction,m.domain,m.id,m.original,m.replacement,m.metric,m.vanilla,m.current,null,null,m.source]);
const ms=sheet('Metric deltas','Detailed unit metric comparison','Numbers are extracted inputs; delta columns calculate from them. Blank = absent/not applicable, not zero.',
 ['Faction','Domain','Unit ID','Original','Replacement','Metric','Vanilla','Current','Difference','Change %','Vanilla source archive / entry'],mrows,[12,12,16,27,48,23,16,16,16,16,100]);
for(let i=0;i<mrows.length;i++){let r=i+6;ms.getRange(`I${r}:J${r}`).formulas=[[`=IF(AND(ISNUMBER(G${r}),ISNUMBER(H${r})),H${r}-G${r},"n.a.")`,`=IF(AND(ISNUMBER(G${r}),ISNUMBER(H${r})),IF(G${r}=0,"n.a.",H${r}/G${r}-1),"n.a.")`]];}
ms.getRange(`G6:I${mrows.length+5}`).setNumberFormat('0.####');ms.getRange(`J6:J${mrows.length+5}`).setNumberFormat('0.00%');
ms.getRange(`I6:I${mrows.length+5}`).conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FFF1CE'}});
const wr=data.weapons.map(w=>[w.faction,w.domain,w.id,w.original,w.replacement,w.version,w.index,w.label,w.damage,w.range,w.min_range,w.rate,null,w.splash,w.muzzle_count,w.muzzle_salvo,w.rack_salvo,w.rack_together,w.beam_lifetime,w.collision_delay,w.target_allow,w.layers,w.projectile]);
const ws=sheet('Weapon profiles','Every weapon and targeting profile','Compare by weapon label/role; redesigned guns do not map one-to-one. Damage × RateOfFire is not reliable total DPS.',
 ['Faction','Domain','Unit ID','Original','Replacement','Version','Index','Weapon label','Damage','Max range','Min range','RateOfFire','Rate interval (s)','Splash radius','Muzzles','Muzzle salvo','Rack salvo','Racks together','Beam lifetime','Collision interval','Allowed target filter','Target layers','Projectile reference'],wr,[12,12,16,27,48,14,10,30,14,14,14,14,18,16,12,14,14,17,16,18,50,65,95]);
for(let i=0;i<wr.length;i++){let r=i+6;ws.getRange(`M${r}`).formulas=[[`=IF(ISNUMBER(L${r}),IF(L${r}=0,"n.a.",1/L${r}),"n.a.")`]];}
ws.getRange(`I6:T${wr.length+5}`).setNumberFormat('0.####');
const rr=data.units.map(u=>[u.faction,u.domain,u.id,u.original,u.replacement,u.installed?'Installed prototype':'Design only',u.selection_status,u.visible_name_reconstructed,u.notes||'',u.patches.map(p=>p.archive+'!'+p.entry).join('; ')||'No installed override']);
sheet('Conversion roster','Complete mobile conversion roster','46 unique slots: 25 GAR / 21 CIS. Experimentals appear once in their movement domain. Buildings and dependencies deferred.',
 ['Faction','Domain','Unit ID','SC2 unit','Replacement','Implementation','Planning decision','Reconstructed display name','Current evidence / outstanding work','Installed override provenance'],rr,[12,12,16,27,55,24,40,40,115,125]);
const notes=[
 ['Scope','Vanilla base + DLC vs installed development copy, 2026-10-25. No game files modified by this snapshot.'],
 ['What A means','Damage field for first damaging weapon. Projectile/tick damage, not DPS or full volley damage. Weapon labels identify the selected profile.'],
 ['SPHA-T exception','A current 375 is per beam installment. Ten installments nominally cap one discharge at 3750 over 2 s; compare full beam budget, not 375 vs 3750 as a 90% nerf.'],
 ['UT-AT output','75 + 30 + 30 damage, each at 0.725/s gives nominal fully on-target 97.875 DPS. Requires all three guns to bear and hit; no armor/research included.'],
 ['TX-130 output','Main profile is 60 damage per projectile, two muzzle launches per cycle at 0.5/s: nominal main output 60 DPS. Upgrade weapons are separate profiles, not automatically active.'],
 ['AT-TE role','King Kriptor redesigned into heavy assault walker. Health 50625 -> 30000. Main damage 1500, range 68.75, rate 1/3. Four front guns share volley, two rear guns independent.'],
 ['Stacked Juggernaut speed','Native 2.5 -> 2.875 -> 3.30625, cumulative +32.25%. Each +15% change was applied to its then-current baseline. Confirm whether cumulative value is intended before tuning.'],
 ['Name defect','AT-AP is UUL0102 and AT-RT is UUL0103. Unified naming overlay currently reverses their displayed labels. Snapshot records this defect; no game fixes made during documentation task.'],
 ['Static reconstruction',data.method],
 ['Runtime limits','No new engine session, damage test or research progression was run for this workbook. Script logic, target availability, mitigation, volley timing and research can change effective output.'],
 ['Missing values','Absent blueprint fields stay blank. They may be inherited/engine defaults or not applicable. Do not interpret blanks as zero.'],
 ['Planned entries','For not-yet-converted units, Current equals vanilla because no mod override was found. Replacement names are plans, not claims of implementation.'],
 ['Research state','No research / veterancy / temporary ability buffs applied. Blueprint weapon lists may include disabled upgrade weapons.'],
 ['Economy units','MassValue and EnergyValue are raw blueprint resource values, before research/economy adjustments; BuildTime is a blueprint workload, not necessarily wall-clock seconds.'],
 ['Movement and range','S and R use internal game units; no conversion to km/h or meters is asserted. MaxSpeed is a cap, not acceleration or effective pathfinding pace.'],
 ['Source of truth','project-state.json holds the generated snapshot and provenance; roster.csv, balance-metrics.csv and weapons.csv are exchange views. Obsidian notes and prompt are generated reading views.'],
 ['Refresh','Re-run extraction against current vanilla and installed packages, regenerate workbook and notes, review differences, then commit. Archive old snapshots; do not hand-edit generated numeric outputs.'],
 ['Decision authority','Latest explicit human decisions override older PROJECT_SPEC/roster entries. Approval, source availability, native conversion, installation and runtime acceptance are distinct.'],
 ['Deferred','Structures, Illuminate and facility-linked Proto-Brain dependencies remain out of mobile conversion scope. AV-7 is only a future artillery-structure candidate.'],
 ...data.installed_packages.map(p=>['Installed SHA256: '+p.file,p.sha256])
];
const ns=sheet('Read me','Definitions, exceptions and provenance','Read before using the numbers to propose balance changes.', ['Topic','Meaning / source / evidence'],notes,[42,150]);ns.getRange(`B6:B${notes.length+5}`).format.wrapText=true;ns.getRange(`A6:B${notes.length+5}`).format.rowHeight=42;ns.freezePanes.unfreeze();
wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'Unit comparison',range:'A6:Q18',maxChars:2200,tableMaxCols:17,tableMaxRows:13})).ndjson);
// Verify a dependent percentage reacts to a temporary input edit, then restore.
const r=6+data.units.findIndex(u=>u.id==='uux0101');const initial=us.getRange(`K${r}`).values[0][0];
us.getRange(`K${r}`).values=[[2.5]];wb.recalculate();const test=us.getRange(`L${r}`).values[0][0];if(Math.abs(test)>1e-8)throw Error('Speed delta formula did not recalculate');us.getRange(`K${r}`).values=[[initial]];wb.recalculate();
for(const [name,s] of Object.entries(sheets)){
 const end=name==='Read me'?'B14':name==='Unit comparison'?'L16':name==='Metric deltas'?'J16':name==='Weapon profiles'?'M15':'H16';
 const blob=await wb.render({sheetName:name,range:`A1:${end}`,scale:1.3,format:'png'});
 await fs.writeFile(`${out}/${name.replaceAll(' ','-')}-preview.png`,new Uint8Array(await blob.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(`${out}/SC2-Conversion-and-Balance.xlsx`);
await fs.writeFile(`${out}/workbook-validation.json`,JSON.stringify({sheets:Object.keys(sheets),units:data.units.length,metricRows:mrows.length,weaponRows:wr.length,formulaRecalculationTest:'passed',nativeExcelVerified:false},null,2));
console.log('Workbook exported');

