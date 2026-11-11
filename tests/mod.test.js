import { test } from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFile } from 'node:fs/promises';

test('real mod lifecycle: reactive status → atomic snapshot; commands reject stale mappings', async () => {
  const context=vm.createContext({console,Date});
  const saved=new Map(), files=new Map(), calls=[], errors=[], ids=[];
  let deliver;
  const nativeAgents=[{address:'kenya/t1',status:'done',space_name:'API',title:'Fix'}];
  const nativeTerminals=[{address:'kenya/t1',state:'live',status:'done'}];
  const nativeMachines=[{name:'kenya',layout:'ready'}];
  function node() {
    let proxy;
    proxy=new Proxy({}, {get(_target,name) {
      if(name==='when')return (condition,fn)=>condition?fn(proxy):proxy;
      if(name==='id')return id=>{ids.push(id);return proxy};
      return ()=>proxy;
    }});return proxy;
  }
  const host={agents:()=>nativeAgents,terminals:()=>nativeTerminals,machines:()=>nativeMachines,
    focused:()=>({agent:'kenya/t1'}),theme:()=>({}),shared:k=>saved.get(k),setShared:(k,v)=>saved.set(k,v),
    appHome:()=>'/herdr',nextCommand:()=>new Promise(resolve=>{deliver=resolve}),run:(...args)=>calls.push(args),notify:()=>{},
    readTextFile:async p=>files.get(p)??null,writeTextFile:async(p,text,expected)=>{
      assert.equal(files.get(p)??null,expected);files.set(p,text);
    }};
  const synthetic=(exports)=>new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v]of Object.entries(exports))this.setExport(k,v)},{context});
  const model=new vm.SourceTextModule(await readFile(new URL('../mod/model.js',import.meta.url),'utf8'),{context});
  await model.link(()=>{});await model.evaluate();
  const main=new vm.SourceTextModule(await readFile(new URL('../mod/main.js',import.meta.url),'utf8'),{context});
  await main.link(name=>name==='herdr'?synthetic(host):name==='./model.js'?model:
    name==='gpui-kit'?synthetic({View:class{},div:node}):synthetic({v_flex:node,h_flex:node}));
  await main.evaluate();
  let tick;
  const cx={timer:{every(_ms,fn){tick=fn}},spawn(fn){fn(cx).catch(e=>errors.push(e))},notify(){},stop_propagation(){}};
  const mod=new main.namespace.default();mod.init({},cx);mod.render(cx);
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  tick(cx);await flush();
  let s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));
  assert.equal(s.slots[0].address,'kenya/t1');assert.equal(s.slots[0].state,'done');
  const revision=s.revision;
  mod.render(cx);tick(cx);await flush();
  assert.equal(JSON.parse(files.get('/herdr/mods/q0-agents/.state.json')).revision,revision);
  assert.ok(ids.includes('show-1'));assert.ok(!ids.includes('show-2'));
  ids.length=0;nativeMachines[0].layout='unavailable';mod.render(cx);
  assert.ok(!ids.includes('show-1'));nativeMachines[0].layout='ready';mod.render(cx);
  deliver(`select-${revision-1}-1`);await flush();assert.equal(calls.length,0);
  deliver(`select-${revision}-1`);await flush();assert.equal(calls[0][0],'agent.focus');
  nativeAgents[0].status='idle';mod.render(cx);tick(cx);await flush();
  s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));assert.equal(s.slots[0].state,'idle');
  deliver(`mode-${revision}-0`);await flush();
  // Reject before a render can refresh the instance's old cached enabled flag.
  deliver(`select-${revision+1}-1`);await flush();assert.equal(calls.length,1);
  mod.render(cx);tick(cx);await flush();
  s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));assert.equal(s.enabled,false);
  assert.equal(s.revision,revision+1);
  deliver(`select-${revision}-1`);await flush();assert.equal(calls.length,1);
  deliver('clear-1');await flush();mod.render(cx);tick(cx);await flush();
  s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));assert.equal(s.slots[0].address,'kenya/t1');
  // A new agent is assigned on its first native data update, with no user command.
  nativeAgents.push({address:'kenya/t2',status:'working',title:'New'});
  nativeTerminals.push({address:'kenya/t2',state:'live',status:'working'});
  mod.render(cx);tick(cx);await flush();
  s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));assert.equal(s.slots[1].address,'kenya/t2');
  nativeAgents.splice(1,1);nativeTerminals.splice(1,1);
  mod.render(cx);tick(cx);await flush();
  s=JSON.parse(files.get('/herdr/mods/q0-agents/.state.json'));assert.equal(s.slots[1].address,null);
  assert.ok([...files.keys()].every(p=>p.split('/').at(-1).startsWith('.')));
  assert.deepEqual(errors,[]);
});
