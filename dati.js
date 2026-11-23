// Dati di riferimento condivisi tra calcolatore e test (copiati da calcolatore.html, non modificati).
const CLIMI = {
  milano: { tmax:[7.3,10.0,15.5,19.3,23.9,28.1,30.7,29.9,25.5,19.0,12.4,7.4], tmin:[-0.4,0.6,4.4,8.4,12.8,17.2,19.3,18.8,14.9,10.2,5.3,0.6], rh:[78.9,73.6,68,67.7,67.2,66.9,66.2,67.4,70,76.5,81,81.8], td:[0.2,0.8,3.9,7.0,11.2,14.7,16.6,16.8,13.4,10.1,5.9,1.2] },
  roma: { tmax:[12.0,13.0,15.8,18.8,22.3,28.1,31.0,31.6,26.7,22.2,16.9,12.7], tmin:[3.4,3.4,5.9,8.6,12.6,16.7,19.3,19.8,16.0,12.4,8.5,4.7], rh:[75.8,71.5,70.6,70.4,69,65.4,63.3,64.1,69.1,74,77.9,77.2], td:[3.9,3.5,5.8,8.5,12.1,15.1,16.9,17.7,15.5,12.9,9.3,5.2] },
  viterbo: { tmax:[10.6,11.9,14.7,17.9,22.4,27.4,31.2,31.3,26.0,20.7,15.0,11.2], tmin:[2.2,2.2,4.0,6.7,10.2,14.2,16.9,17.5,14.3,10.5,6.3,3.1], rh:[74.5,70.6,69.6,70.1,69.2,66.1,62.5,62.8,67.8,73.3,77.2,76.1], td:null },
};
const MESI = ['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'];
const MIX_LABELS = { gas_olio:'Gas e olio', carbone:'Carbone', biomasse:'Biomasse', idro:'Idroelettrico', eolico:'Eolico', fv:'Fotovoltaico', geo:'Geotermico', import:'Import (saldo)' };
const MIX0 = { gas_olio:134382, carbone:2975, biomasse:15699, idro:41365, eolico:21363, fv:44290, geo:5261, import:46889 };
const F0 = { gas_olio:0.8, carbone:2.2, biomasse:2.09, idro:0, eolico:0, fv:0, geo:0.038, import:1.33, idroEvap:17.0 };
const SYS = {
  aria_dry:  { name:'Chiller ad aria + free cooling', short:'Aria, circuito chiuso', heatT:'25–35 °C', hint:'Nessuna evaporazione: acqua solo per usi accessori. Più energia nelle ore calde.',
               p:{ sys:'dry', tFcFull:12, tFcNone:22, copA:9, copB:0.15, fan:0.04, adiabatic:false, coc:3, tSwitch:26, eps:0.8, dTcoil:10 } },
  aria_adiab:{ name:'Dry cooler + adiabatico estivo', short:'Adiabatico', heatT:'25–35 °C', hint:"L'aria viene pre-raffreddata con acqua solo sopra la soglia di temperatura.",
               p:{ sys:'dry', tFcFull:12, tFcNone:22, copA:9, copB:0.15, fan:0.04, adiabatic:true, tSwitch:26, eps:0.8, dTcoil:10, coc:2.7 } },
  torri:     { name:'Torri evaporative + chiller ad acqua', short:'Torri evaporative', heatT:'28–35 °C', hint:"Molto efficiente in energia, ma evapora acqua quasi tutto l'anno.",
               p:{ sys:'tower', tFcFull:8, tFcNone:14, copA:11, copB:0.2, fan:0.03, fEvap:0.85, coc:4, tDry:-50 } },
  diretta:   { name:'Aria esterna diretta + evaporativo', short:'Aria diretta', heatT:'25–35 °C', hint:'Nessun chiller. Acqua solo nelle ore più calde. Parametri tarati sul caso AWS Rho-Pero.',
               p:{ sys:'direct', tSwitch:28, tSup:24, eps:0.85, dTair:12, coc:2.7, fan:0.03 } },
  liquido:   { name:'Liquido diretto al chip + dry cooler', short:'Liquido al chip', heatT:'40–55 °C', hint:'Acqua calda in uscita: free cooling quasi tutto l\'anno e calore più facile da riusare.',
               p:{ sys:'dry', tFcFull:28, tFcNone:36, copA:9, copB:0.15, fan:0.03, adiabatic:false, coc:3, tSwitch:30, eps:0.8, dTcoil:10 } },
};
const COMMON0 = { losses:0.05, kHeat:1.03, accessori:0 };
if (typeof module !== 'undefined') module.exports = { CLIMI, MESI, MIX_LABELS, MIX0, F0, SYS, COMMON0 };
