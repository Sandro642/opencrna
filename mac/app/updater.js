// Mise à jour depuis les Releases GitHub (sans Squirrel : l'app n'est signée qu'en ad hoc).
// Télécharge le zip de la dernière release, le décompresse, puis un script shell remplace
// le bundle .app une fois l'app quittée et la relance.
const {app,dialog,net,BrowserWindow}=require('electron');
const path=require('path'),fs=require('fs'),os=require('os'),{execFile,spawn}=require('child_process');
const REPO='Sandro642/opencrna',ASSET=/macOS-AppleSilicon\.zip$/;
const newer=(a,b)=>{const x=a.split('.').map(Number),y=b.split('.').map(Number);for(let i=0;i<3;i++){if((x[i]||0)!==(y[i]||0))return (x[i]||0)>(y[i]||0)}return false};
const win=()=>BrowserWindow.getFocusedWindow()||BrowserWindow.getAllWindows()[0];
const box=o=>dialog.showMessageBox(win(),{type:'info',...o});
let busy=false;
async function latest(){
  const r=await net.fetch(`https://api.github.com/repos/${REPO}/releases/latest`,{headers:{'User-Agent':'openCRNA','Accept':'application/vnd.github+json'}});
  if(!r.ok)throw new Error('GitHub a répondu '+r.status);
  const j=await r.json(),a=(j.assets||[]).find(a=>ASSET.test(a.name));
  return {ver:String(j.tag_name||'').replace(/^v/,''),notes:(j.body||'').trim(),url:a&&a.browser_download_url,size:a&&a.size};
}
async function download(url,size,dest){
  const r=await net.fetch(url,{headers:{'User-Agent':'openCRNA'}});
  if(!r.ok)throw new Error('Téléchargement : '+r.status);
  const total=+r.headers.get('content-length')||size||0,out=fs.createWriteStream(dest),rd=r.body.getReader();let n=0;
  for(;;){const {done,value}=await rd.read();if(done)break;n+=value.length;
    if(!out.write(Buffer.from(value)))await new Promise(k=>out.once('drain',k));
    const w=win();if(w&&total)w.setProgressBar(n/total)}
  await new Promise((k,e)=>{out.on('error',e);out.end(k)});
  const w=win();if(w)w.setProgressBar(-1);
}
const run=(cmd,args)=>new Promise((k,e)=>execFile(cmd,args,err=>err?e(err):k()));
async function install(info){
  const bundle=path.resolve(process.execPath,'../../..');
  if(!bundle.endsWith('.app'))throw new Error('Bundle introuvable : '+bundle);
  if(bundle.includes('/AppTranslocation/'))throw new Error('Déplace openCRNA.app dans le dossier Applications puis relance-la avant de mettre à jour.');
  try{fs.accessSync(path.dirname(bundle),fs.constants.W_OK);fs.accessSync(bundle,fs.constants.W_OK)}
  catch(e){throw new Error('Pas le droit de remplacer '+bundle+'.\nDans le Terminal : sudo chown -R "$USER" '+bundle)}
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'opencrna-maj-')),zip=path.join(dir,'maj.zip');
  await download(info.url,info.size,zip);
  await run('/usr/bin/ditto',['-x','-k',zip,dir]);
  const fresh=path.join(dir,'openCRNA.app');
  if(!fs.existsSync(path.join(fresh,'Contents/MacOS')))throw new Error('Archive invalide');
  const q=s=>"'"+s.replace(/'/g,"'\\''")+"'",old=path.join(dir,'ancien.app'),sh=path.join(dir,'maj.sh'),log=path.join(app.getPath('userData'),'maj-echec.txt');
  fs.writeFileSync(sh,`#!/bin/sh
while kill -0 ${process.pid} 2>/dev/null; do sleep 0.3; done
rm -f ${q(log)}
if mv ${q(bundle)} ${q(old)} 2>>${q(log)}; then
  if mv ${q(fresh)} ${q(bundle)} 2>>${q(log)}; then rm -rf ${q(dir)}; rm -f ${q(log)}; else mv ${q(old)} ${q(bundle)}; fi
fi
xattr -cr ${q(bundle)} 2>/dev/null
open ${q(bundle)}
`);
  spawn('/bin/sh',[sh],{detached:true,stdio:'ignore'}).unref();
  app.quit();
}
// Au lancement : signale l'échec éventuel de la mise à jour précédente (journal laissé par maj.sh)
function reportFailure(){
  const log=path.join(app.getPath('userData'),'maj-echec.txt');if(!fs.existsSync(log))return;
  const t=fs.readFileSync(log,'utf8').trim();fs.rmSync(log,{force:true});
  dialog.showMessageBox(win(),{type:'warning',message:'La mise à jour n’a pas pu être installée',detail:(t||'Le remplacement de l’application a échoué.')+'\n\nEssaie : sudo chown -R "$USER" '+path.resolve(process.execPath,'../../..')});
}
async function check(manual){
  if(busy)return;busy=true;let acted=false;
  try{
    if(!app.isPackaged){if(manual)box({message:'Mises à jour désactivées en mode développement.'});return}
    const info=await latest(),cur=app.getVersion();
    if(!info.ver||!newer(info.ver,cur)||!info.url){if(manual)box({message:'openCRNA est à jour',detail:'Version '+cur+'.'});return}
    const {response}=await box({message:'Mise à jour disponible : openCRNA '+info.ver,
      detail:'Version installée : '+cur+(info.notes?'\n\nNouveautés :\n'+info.notes.slice(0,1500):''),
      buttons:['Installer et redémarrer','Plus tard'],defaultId:0,cancelId:1});
    if(response===0){acted=true;await install(info)}
  }catch(e){if(manual||acted)dialog.showMessageBox(win(),{type:'warning',message:'Mise à jour impossible',detail:String(e.message||e)})}
  finally{busy=false}
}
module.exports={check,reportFailure};
