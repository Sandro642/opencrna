// Pont minimal et sûr entre la page et le processus principal : seulement la requête OpenSky (trafic réel)
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('opencrna',{
  opensky:b=>ipcRenderer.invoke('opensky',{lamin:+b.lamin,lomin:+b.lomin,lamax:+b.lamax,lomax:+b.lomax})
});
