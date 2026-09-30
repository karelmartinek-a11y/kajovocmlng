// Explicit ECMASCRIPT_AUTH_CLONE_GRAPH_V1 engine codec. Never arbitrary JSON fallback.
(()=>{
 const b64=b=>{const view=new Uint8Array(b),chunks=[];for(let i=0;i<view.length;i+=32768)chunks.push(String.fromCharCode(...view.subarray(i,i+32768)));return btoa(chunks.join(''))};
 const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
 const float=v=>{const b=new ArrayBuffer(8);new DataView(b).setFloat64(0,v,false);return {encoding:'IEEE754_BINARY64_BIG_ENDIAN_BASE64',base64:b64(b)}};
 const number=v=>new DataView(bytes(v.base64).buffer).getFloat64(0,false);
 async function encode(root){
  const nodes=[],seen=new Map();
  async function walk(v){
   if(v!==null&&(typeof v==='object')&&seen.has(v))return seen.get(v);
   const id='n'+nodes.length,n={id};nodes.push(n);
   if(v!==null&&typeof v==='object')seen.set(v,id);
   if(v===undefined)n.kind='UNDEFINED';else if(v===null)n.kind='NULL';
   else if(typeof v==='boolean'){n.kind='BOOLEAN';n.value=v}
   else if(typeof v==='string'){n.kind='STRING';n.value=v}
   else if(typeof v==='number'){n.kind='NUMBER';n.value=float(v)}
   else if(typeof v==='bigint'){n.kind='BIGINT';n.decimal=v.toString()}
   else if(v instanceof Date){n.kind='DATE';n.epochMilliseconds=float(v.getTime())}
   else if(v instanceof RegExp){n.kind='REGEXP';n.source=v.source;n.flags=v.flags}
   else if(v instanceof ArrayBuffer){n.kind='ARRAY_BUFFER';n.base64=b64(v)}
   else if(ArrayBuffer.isView(v)){n.kind='TYPED_ARRAY';n.elementType=v.constructor.name;n.bufferNodeId=await walk(v.buffer);n.byteOffset=v.byteOffset;n.byteLength=v.byteLength}
   else if(v instanceof File){n.kind='FILE';n.name=v.name;n.mediaType=v.type;n.lastModifiedMilliseconds=float(v.lastModified);n.base64=b64(await v.arrayBuffer())}
   else if(v instanceof Blob){n.kind='BLOB';n.mediaType=v.type;n.base64=b64(await v.arrayBuffer())}
   else if(Array.isArray(v)){n.kind='ARRAY';n.length=v.length;n.items=[];n.properties=[];for(const k of Object.keys(v)){if(/^(0|[1-9][0-9]*)$/.test(k)&&Number(k)<4294967295)n.items.push({index:Number(k),nodeId:await walk(v[k])});else n.properties.push({name:k,valueNodeId:await walk(v[k])})}}
   else if(v instanceof Set){n.kind='SET';n.items=[];for(const x of v)n.items.push({nodeId:await walk(x)})}
   else if(v instanceof Map){n.kind='MAP';n.entries=[];for(const [k,x]of v)n.entries.push({keyNodeId:await walk(k),valueNodeId:await walk(x)})}
   else if(Object.getPrototypeOf(v)===Object.prototype){n.kind='OBJECT';n.entries=[];for(const k of Object.keys(v))n.entries.push({name:k,valueNodeId:await walk(v[k])})}
   else throw new Error('BROWSER_STATE_SERIALIZER_UNSUPPORTED');
   return id;
  }
  return {serializer:'ECMASCRIPT_AUTH_CLONE_GRAPH_V1',rootNodeId:await walk(root),nodes};
 }
 function decode(g){
  if(g.serializer!=='ECMASCRIPT_AUTH_CLONE_GRAPH_V1')throw new Error('BROWSER_STATE_SERIALIZER_UNSUPPORTED');
  const out=new Map(),defs=new Map();
  for(const n of g.nodes){if(defs.has(n.id))throw new Error('BROWSER_STATE_DUPLICATE_NODE');defs.set(n.id,n)}
  for(const n of g.nodes){let v;
   switch(n.kind){
   case 'UNDEFINED':v=undefined;break;case 'NULL':v=null;break;case 'BOOLEAN':case 'STRING':v=n.value;break;
   case 'NUMBER':v=number(n.value);break;case 'BIGINT':v=BigInt(n.decimal);break;case 'DATE':v=new Date(number(n.epochMilliseconds));break;
   case 'REGEXP':v=new RegExp(n.source,n.flags);break;
   case 'ARRAY_BUFFER':v=bytes(n.base64).buffer;break;
   case 'BLOB':v=new Blob([bytes(n.base64)],{type:n.mediaType});break;
   case 'FILE':v=new File([bytes(n.base64)],n.name,{type:n.mediaType,lastModified:number(n.lastModifiedMilliseconds)});break;
   case 'OBJECT':v={};break;case 'ARRAY':v=[];break;case 'SET':v=new Set();break;case 'MAP':v=new Map();break;
   case 'TYPED_ARRAY':continue;default:throw new Error('BROWSER_STATE_SERIALIZER_UNSUPPORTED')}
   out.set(n.id,v)
  }
  const get=id=>{if(!out.has(id))throw new Error('BROWSER_STATE_GRAPH_REFERENCE_INVALID');return out.get(id)};
  for(const n of g.nodes)if(n.kind==='TYPED_ARRAY'){
   const widths={Int8Array:1,Uint8Array:1,Uint8ClampedArray:1,Int16Array:2,Uint16Array:2,Int32Array:4,Uint32Array:4,Float32Array:4,Float64Array:8,BigInt64Array:8,BigUint64Array:8};
   const b=get(n.bufferNodeId);if(!(b instanceof ArrayBuffer)||n.byteOffset+n.byteLength>b.byteLength)throw new Error('BROWSER_STATE_TYPED_ARRAY_RANGE_INVALID');
   if(n.elementType==='DataView')out.set(n.id,new DataView(b,n.byteOffset,n.byteLength));
   else if(widths[n.elementType]&&n.byteOffset%widths[n.elementType]===0&&n.byteLength%widths[n.elementType]===0)out.set(n.id,new globalThis[n.elementType](b,n.byteOffset,n.byteLength/widths[n.elementType]));
   else throw new Error('BROWSER_STATE_TYPED_ARRAY_RANGE_INVALID')
  }
  for(const n of g.nodes){const v=get(n.id);
   if(n.kind==='OBJECT')for(const e of n.entries)Object.defineProperty(v,e.name,{value:get(e.valueNodeId),enumerable:true,writable:true,configurable:true});
   if(n.kind==='ARRAY'){v.length=n.length;for(const e of n.items)v[e.index]=get(e.nodeId);for(const e of n.properties)Object.defineProperty(v,e.name,{value:get(e.valueNodeId),enumerable:true,writable:true,configurable:true})}
   if(n.kind==='SET')for(const e of n.items)v.add(get(e.nodeId));
   if(n.kind==='MAP')for(const e of n.entries)v.set(get(e.keyNodeId),get(e.valueNodeId));
  }
  return get(g.rootNodeId)
 }
 globalThis.KCMLClone={encode,decode};
})()
