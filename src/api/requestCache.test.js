import test from 'node:test'
import assert from 'node:assert/strict'
import { createRequestCache } from './requestCache.js'
test('concurrent requests share one load; cached reads expire and keys isolate stations', async () => {
  let clock = 0, count = 0
  const read = createRequestCache(() => clock)
  const load = async () => ++count
  assert.deepEqual(await Promise.all([read('station1',load,60),read('station1',load,60)]),[1,1])
  assert.equal(await read('station1',load,60),1)
  assert.equal(await read('station2',load,60),2)
  clock = 61
  assert.equal(await read('station1',load,60),3)
})
test('failed requests are not cached', async () => {
  const read = createRequestCache()
  await assert.rejects(read('x',async()=>{throw Error('offline')}))
  assert.equal(await read('x',async()=>42),42)
})
