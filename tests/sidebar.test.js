import { test } from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFile } from 'node:fs/promises';

async function renderer() {
  const context = vm.createContext({});
  function div() {
    const data = {children: []};
    let node;
    node = new Proxy(data, {get(target, key) {
      if (key in target) return target[key];
      return (...args) => {
        if (key === 'child') target.children.push(args[0]);
        else target[key] = args;
        return node;
      };
    }});
    return node;
  }
  const gpui = new vm.SyntheticModule(['div'], function() { this.setExport('div', div); }, {context});
  const model = new vm.SourceTextModule(await readFile(new URL('../mod/model.js', import.meta.url), 'utf8'), {context});
  await model.link(() => {}); await model.evaluate();
  const badges = new vm.SourceTextModule(await readFile(new URL('../sidebar/badges.js', import.meta.url), 'utf8'), {context});
  await badges.link(name => name === 'gpui-kit' ? gpui : model); await badges.evaluate();
  return badges.namespace;
}

test('sidebar badges follow addresses through sorting, title changes, reassignment and closure', async () => {
  const {assignedKeys, keyBadge} = await renderer();
  const saved = {slots: Array.from({length: 9}, (_, i) => ({address: `host/t${i+1}`, label: 'Same title'}))};
  const t = {raised: '#222', foreground: '#eee', muted: '#aaa'};
  let keys = assignedKeys(saved);
  for (let i = 9; i >= 1; i--) {
    const badge = keyBadge(t, `host/t${i}`, keys, true);
    assert.deepEqual(badge.children, [String(i)]);
    assert.deepEqual(badge.tooltip, [`Q0 key ${i}`]);
  }
  assert.equal(keyBadge(t, 'other-host/t1', keys, true), null);
  assert.equal(keyBadge(t, 'host/t10', keys, true), null);
  saved.slots[0].label = 'Renamed';
  [saved.slots[0], saved.slots[5]] = [saved.slots[5], saved.slots[0]];
  keys = assignedKeys(saved);
  assert.deepEqual(keyBadge(t, 'host/t1', keys, true).children, ['6']);
  assert.deepEqual(keyBadge(t, 'host/t6', keys, true).children, ['1']);
  saved.slots[5] = null;
  assert.equal(keyBadge(t, 'host/t1', assignedKeys(saved), true), null);
});

test('number mode keeps assignment visible without claiming that it is active', async () => {
  const {assignedKeys, keyBadge} = await renderer();
  const keys = assignedKeys({slots: [{address: 't1'}]});
  const t = {raised: '#222', foreground: '#eee', muted: '#aaa'};
  const badge = keyBadge(t, 't1', keys, false);
  assert.deepEqual(badge.children, ['1']);
  assert.deepEqual(badge.text_color, ['#aaa']);
  assert.match(badge.tooltip[0], /Number mode selected/);
  assert.equal(assignedKeys(null).size, 0);
});
