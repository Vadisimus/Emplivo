const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const root='/workspace/releases/Emplivo_Wellness_2026-11-12/www';
const routes=['','jobs/','employers/','about/','cases/','demo-account/','demo-employer-dashboard/','privacy/'];
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],headless:true});
 try{
  for(const locale of ['uk','en']){
   const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   for(const route of routes){
    const p=(locale==='en'?'en/':'')+route;
    await page.goto('http://127.0.0.1:8085/'+p);
    await page.evaluate(()=>document.fonts.ready);
    await page.evaluate(({locale,route})=>{
     document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in-view'));
     const desc=locale==='uk'?'Emplivo: підбір персоналу і кар’єра у SPA, wellness та фітнесі. Перегляньте демонстраційний каталог, обговоріть підбір або надішліть загальну анкету.':'Emplivo recruitment and spa, wellness and fitness careers. Explore the demonstration catalogue, discuss hiring or submit a general application.';
     document.querySelector('meta[name=description]').content=desc;
     for(const [property,content]of Object.entries({'og:title':document.title,'og:description':desc,'og:type':'website','og:url':'https://www.emplivo.com.ua/'+(locale==='en'?'en/':'')+route})){
      let el=document.querySelector(`meta[property="${property}"]`);if(!el){el=document.createElement('meta');el.setAttribute('property',property);document.head.append(el);}el.content=content;
     }
    },{locale,route});
    const html=await page.content();
    if(!html.includes('<h1>'))throw Error('Missing static h1 at '+p);
    fs.writeFileSync(path.join(root,p,'index.html'),html+'\n');
   }
   if(errors.length)throw Error(errors.join('\n'));
   await context.close();
  }
  execFileSync('python',[path.join(__dirname,'make_portable.py'),root],{stdio:'inherit'});
  console.log('Rendered 16 static UK/EN core pages with crawlable content and metadata.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
