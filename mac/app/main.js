const {app,BrowserWindow,Menu,shell,ipcMain,net}=require('electron');
const path=require('path');
const updater=require('./updater');
app.setName('openCRNA');
// Trafic réel : l'API OpenSky n'autorise pas les appels depuis la page (CORS), on passe donc par le processus principal
ipcMain.handle('opensky',async(e,b)=>{
  const n=v=>Number.isFinite(v)?v:0,u='https://opensky-network.org/api/states/all?lamin='+n(b.lamin)+'&lomin='+n(b.lomin)+'&lamax='+n(b.lamax)+'&lomax='+n(b.lomax);
  try{const r=await net.fetch(u,{headers:{'User-Agent':'openCRNA'}});return{status:r.status,remaining:r.headers.get('x-rate-limit-remaining'),body:r.ok?await r.json():null}}
  catch(err){return{status:0,error:String(err.message||err)}}
});
function createWindow(){
  const win=new BrowserWindow({width:1480,height:920,minWidth:1024,minHeight:660,backgroundColor:'#000000',title:'openCRNA',show:false,
    webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true,spellcheck:false,preload:path.join(__dirname,'preload.js')}});
  win.once('ready-to-show',()=>win.show());
  // Auto-test (OPENCRNA_SELFTEST=1) : vérifie la requête OpenSky via le pont puis quitte
  if(process.env.OPENCRNA_SELFTEST)win.webContents.once('did-finish-load',()=>win.webContents.executeJavaScript("window.opencrna.opensky({lamin:44,lomin:0,lamax:45,lomax:1}).then(r=>JSON.stringify({status:r.status,avions:r.body&&r.body.states?r.body.states.length:null,quota:r.remaining}))").then(v=>{console.log('SELFTEST '+v);app.quit()},err=>{console.log('SELFTEST ERREUR '+err);app.quit()}));
  win.loadFile(path.join(__dirname,'index.html'));
  win.webContents.setWindowOpenHandler(({url})=>{if(/^https?:/.test(url))shell.openExternal(url);return{action:'deny'}});
  win.webContents.on('will-navigate',(e,url)=>{if(!url.startsWith('file:')){e.preventDefault();shell.openExternal(url)}});
}
const isMac=process.platform==='darwin';
const template=[
  ...(isMac?[{label:'openCRNA',submenu:[{role:'about',label:'À propos d’openCRNA'},{label:'Rechercher les mises à jour…',click:()=>updater.check(true)},{type:'separator'},{role:'hide',label:'Masquer openCRNA'},{role:'hideOthers',label:'Masquer les autres'},{role:'unhide',label:'Tout afficher'},{type:'separator'},{role:'quit',label:'Quitter openCRNA'}]}]:[]),
  {label:'Édition',submenu:[{role:'undo',label:'Annuler'},{role:'redo',label:'Rétablir'},{type:'separator'},{role:'cut',label:'Couper'},{role:'copy',label:'Copier'},{role:'paste',label:'Coller'},{role:'selectAll',label:'Tout sélectionner'}]},
  {label:'Présentation',submenu:[{role:'togglefullscreen',label:'Plein écran'},{type:'separator'},{role:'resetZoom',label:'Taille réelle'},{role:'zoomIn',label:'Agrandir'},{role:'zoomOut',label:'Réduire'},{type:'separator'},{role:'reload',label:'Nouvelle session (recharger)'}]},
  {label:'Fenêtre',submenu:[{role:'minimize',label:'Placer dans le Dock'},{role:'zoom',label:'Réduire/agrandir'},{type:'separator'},{role:'front',label:'Tout ramener au premier plan'}]}
];
app.whenReady().then(()=>{
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
  app.setAboutPanelOptions({applicationName:'openCRNA',applicationVersion:app.getVersion(),copyright:'Simulateur de contrôle en route · profil LFBB',credits:'Données : VATSpy (VATSIM), OurAirports'});
  createWindow();
  updater.reportFailure();setTimeout(()=>updater.check(false),4000);
  app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0)createWindow()});
});
app.on('window-all-closed',()=>app.quit());
