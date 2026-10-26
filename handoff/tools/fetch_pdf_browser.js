const { chromium } = require('playwright'); const fs=require('fs');
(async () => {
  const b = await chromium.launch({proxy:{server:process.env.HTTPS_PROXY}});
  const args=process.argv.slice(2);
  for (let i=0;i<args.length;i+=2){ for (let t=0;t<5;t++){ const ctx = await b.newContext(); try { const r = await ctx.request.get(args[i], {timeout:180000}); const buf = await r.body();
    console.log(r.status(), buf.length, r.headers()['content-type'], args[i]); if (r.status()===200){fs.writeFileSync(args[i+1], buf); await ctx.close(); break;} } catch(e){console.log('ERR',args[i],e.message.split('\n')[0]);} await ctx.close(); await new Promise(s=>setTimeout(s,4000*(t+1))); } }
  await b.close();
})();
