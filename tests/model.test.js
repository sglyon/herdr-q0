import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assignments, assign, snapshot, candidates, reconcile } from '../mod/model.js';

test('slots persist by address across reordered lists and absent agents', () => {
  let s = assign(assignments(null), 4, {address:'kenya/t7',label:'API'});
  s = assign(s, 9, {address:'t3',label:'Local'});
  const snap = snapshot(s, [{address:'t3',state:'working',label:'Local'},{address:'kenya/t7',state:'done',label:'API'}],true);
  assert.equal(snap.slots[3].address,'kenya/t7');
  assert.equal(snap.slots[3].state,'done');
  assert.equal(snap.slots[8].address,'t3');
  const offline = snapshot(s, [], true);
  assert.equal(offline.slots[3].address,'kenya/t7');
  assert.equal(offline.slots[3].state,'unavailable');
});
test('reassignments move rather than duplicate, and invalidate old presses', () => {
  let s = assign(assignments(null),1,{address:'t1',label:'Agent'});
  const before = s.revision;
  s = assign(s,9,{address:'t1',label:'Agent'});
  assert.equal(s.slots[0],null); assert.equal(s.slots[8].address,'t1');
  assert.notEqual(before,s.revision);
  assert.throws(()=>assign(s,0,null));
  assert.equal(assign(s,9,null).slots[8],null);
});
test('desktop unread/seen wins over raw done, raw errors stay errors, subagents included', () => {
  const all = candidates([
    {address:'t1',status:'idle',space_name:'Web',title:'Fix',focused:true},
    {address:'t2',status:'blocked',title:'Oops'},
    {address:'t3',status:'done',title:'Ready'},
  ], [
    {address:'t1',state:'live',status:'done'},
    {address:'t2',state:'live',status:'error'},
    {address:'t3',state:'live',status:'done'},
    {address:'remote/t4',state:'live',status:'working',parent:'t1'},
    {address:'t5',state:'live',status:null},
    {address:'t6',state:'finished',status:'done'},
  ]);
  assert.deepEqual(all.map(a=>a.state),['idle','error','done','working']);
  assert.equal(all[0].focused,true);
});
test('malformed stored assignments are normalized',()=>{
  assert.equal(assignments({slots:[{address:123}]}).slots[0],null);
  assert.equal(assignments({slots:[]}).slots.length,9);
});
test('disconnected machines never retain a misleading working light',()=>{
  const list=candidates([{address:'kenya/t1',status:'working'}],[{address:'kenya/t1',state:'live',status:'working'}],[{name:'kenya',layout:'unavailable'}]);
  assert.equal(list[0].state,'unavailable');
});

const ready = [{name:null,layout:'ready'},{name:'remote',layout:'ready'}];
const agent = n => ({address:`t${n}`,label:`Agent ${n}`,state:'idle'});
const terminalsFor = all => all.map(a=>({address:a.address,state:'live',status:a.state}));
const fill = (saved,all,machines=ready,terminals=terminalsFor(all)) => reconcile(saved,all,terminals,machines);
test('fills every agent below capacity without moving an existing manual key',()=>{
  const all=[agent(1),agent(2),agent(3)];
  const manual=assign(assignments(null),7,all[1]);
  const s=fill(manual,all);
  assert.equal(s.slots[6].address,'t2');
  assert.deepEqual(s.slots.filter(Boolean).map(a=>a.address).sort(),['t1','t2','t3']);
  assert.equal(s.revision,manual.revision+1);
  assert.strictEqual(fill(s,[...all].reverse()),s);
  const next=fill(s,[...all,agent(4)]);
  assert.equal(next.slots[2].address,'t4');
  assert.equal(next.slots[6].address,'t2');
});
test('exits and live terminals returning to a shell free their slots',()=>{
  const all=[agent(1),agent(2),agent(3)];const s=fill(assignments(null),all);
  const next=fill(s,[all[0],all[2]],ready,[...terminalsFor([all[0],all[2]]),{address:'t2',state:'finished'}]);
  assert.equal(next.slots[1],null);assert.equal(next.slots[2].address,'t3');
  const shell=fill(s,[all[0],all[2]],ready,[...terminalsFor([all[0],all[2]]),{address:'t2',state:'live',status:null}]);
  assert.equal(shell.slots[1],null);
  const done=fill(s,[all[0],{...all[1],state:'done'},all[2]]);
  assert.strictEqual(done,s); // A completed turn is still a live agent.
});
test('overflow waits, manual replacement sticks, and a vacancy admits a waiting agent',()=>{
  const all=Array.from({length:11},(_,i)=>agent(i+1));
  const s=fill(assignments(null),all);
  assert.equal(s.slots.filter(Boolean).length,9);
  const manual=assign(s,4,all[9]);const swapped=fill(manual,all);
  assert.strictEqual(swapped,manual);assert.equal(swapped.slots[3].address,'t10');
  const removed=all.filter(a=>a.address!=='t2');const next=fill(swapped,removed);
  assert.equal(next.slots[1].address,'t4'); // The displaced agent was waiting.
  assert.equal(next.slots[3].address,'t10');
  for(const i of [0,2,4,5,6,7,8])assert.equal(next.slots[i].address,swapped.slots[i].address);
});
test('offline/loading machines retain reservations; ready/finished agents can be released',()=>{
  const remote={address:'remote/t1',label:'Remote',state:'working'};
  const s=assign(assignments(null),5,remote);
  for(const layout of ['loading','unavailable']) {
    const m=[{name:null,layout:'ready'},{name:'remote',layout}];
    assert.strictEqual(fill(s,[],m,[]),s);
    assert.equal(fill(s,[],m,[{address:'remote/t1',state:'finished'}]).slots[4],null);
  }
  assert.equal(fill(s,[],ready,[]).slots[4],null);
  assert.strictEqual(fill(s,[],[],[]),s); // No startup snapshot yet.
  assert.equal(fill(assignments(null),[{...remote,state:'unavailable'}]).slots.filter(Boolean).length,0);
});
test('manual moves below capacity preserve coverage and release duplicate slots',()=>{
  const all=[agent(1),agent(2)];const s=fill(assignments(null),all);
  const swapped=fill(assign(s,2,all[0]),all);
  assert.equal(swapped.slots[1].address,'t1');assert.equal(swapped.slots[0].address,'t2');
  assert.equal(new Set(swapped.slots.filter(Boolean).map(s=>s.address)).size,2);
});
