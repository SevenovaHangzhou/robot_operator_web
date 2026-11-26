import assert from 'node:assert/strict';
import {ReceivedSequences} from '../web/arm/received-sequences.mjs';
let now=100, calls=[], row={package_id:'pkg',sha256:'hash',preset_id:'batch',total:2,expires_at:200,revoked:false,attempt:null};
const steps=[{name:'a',gear:'slow',dwell_s:2},{name:'b',gear:'slow',dwell_s:8}];
const m=new ReceivedSequences(async url=>{
 calls.push(url);
 return url.endsWith('/pkg')?{...row,steps,motion_started:false}:{packages:[{...row}],capabilities:{execution_enabled:true}};
},()=>now,()=>'request');
await m.refresh(); assert.equal(m.loaded,null); assert.equal(m.reason(row),'');
await m.load('pkg',{moving:null,sequence:null},{gears:[{name:'slow'}]});
assert.deepEqual(m.command(),{package_id:'pkg',request_id:'request'});assert.equal(calls.length,3);
assert(calls.every(c=>c.startsWith('/api/arm/experiment-packages')));
// An acknowledgement retry keeps the same request; it does not create another attempt.
assert.deepEqual(m.command(),m.command());
await assert.rejects(m.load('pkg',{moving:true},{gears:[]}),/运动/);
row.revoked=true;await m.refresh();assert.throws(()=>m.command(),/撤回/);
row.revoked=false;row.attempt={state:'complete'};await m.refresh();assert.throws(()=>m.command(),/已执行/);
row.attempt=null;now=201;await m.refresh();assert.throws(()=>m.command(),/过期/);
now=100;m.clear();assert.equal(m.loaded,null);
m.read=async()=>{throw Error('network');};await assert.rejects(m.refresh());assert.match(m.reason(row),/未更新/);
console.log('Received sequence catalog/load/expiry/revoke/retry tests passed; no motion calls');
