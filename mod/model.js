// Pure slot model. Fill gaps automatically; existing live assignments stay put.
export const STORE = "q0-agents.assignments.v1";
export const STATES = { off: 0, idle: 1, working: 2, done: 3, blocked: 4, error: 5, unavailable: 6 };

export function assignments(value) {
  const slots = Array.from({ length: 9 }, (_, i) => {
    const s = value?.slots?.[i];
    return s && typeof s.address === "string" && s.address.length < 256
      ? { address: s.address, label: String(s.label || s.address).slice(0, 160) } : null;
  });
  return { revision: Number.isInteger(value?.revision) ? value.revision >>> 0 : 1, slots };
}

export function candidates(agents, terminals, machines = []) {
  const shown = new Map(agents.map(a => [a.address, a]));
  const offline = new Set(machines.filter(m => m.name && m.layout !== "ready").map(m => m.name));
  return terminals.filter(t => t.state === "live" && (shown.has(t.address) || t.status || t.report?.state))
    .map(t => {
      const a = shown.get(t.address);
      const raw = typeof t.status === "string" ? t.status : t.status?.state || t.report?.state;
      // Error survives desktop's error→blocked normalization. Desktop owns unread done.
      const state = offline.has(t.address.split("/")[0]) ? "unavailable" : raw === "error" ? "error" : a?.status || raw || "idle";
      return { address: t.address, label: a ? `${a.space_name || a.program?.name || "Agent"} · ${a.title || a.tab_name || a.address}` : t.name || t.title || t.address,
        state: Object.hasOwn(STATES, state) ? state : "unavailable", focused: !!a?.focused };
    });
}

export function snapshot(saved, all, enabled) {
  const byAddress = new Map(all.map(a => [a.address, a]));
  return { version: 1, revision: saved.revision, enabled, slots: saved.slots.map((s, i) => {
    const live = s && byAddress.get(s.address);
    return { slot: i + 1, address: s?.address || null, label: live?.label || s?.label || "Unassigned",
      state: !s ? "off" : live?.state || "unavailable", focused: !!live?.focused };
  }) };
}

export function assign(saved, slot, agent) {
  if (!Number.isInteger(slot) || slot < 1 || slot > 9) throw Error("Invalid slot");
  const slots = saved.slots.map(s => s && { ...s });
  if (agent) for (let i = 0; i < 9; i++) if (slots[i]?.address === agent.address) slots[i] = null;
  slots[slot - 1] = agent ? { address: agent.address, label: agent.label } : null;
  return { revision: (saved.revision + 1) >>> 0, slots };
}

export function reconcile(saved, all, terminals, machines) {
  const available = new Map(all.map(a => [a.address, a]));
  const known = new Map(terminals.map(t => [t.address, t]));
  const ready = new Set(machines.filter(m => m.layout === "ready").map(m => m.name));
  const seen = new Set();
  const slots = saved.slots.map(s => {
    if (!s || seen.has(s.address)) return null;
    const terminal = known.get(s.address);
    const machine = s.address.includes("/") ? s.address.split("/")[0] : null;
    // A missing/ceased agent is authoritative only after that machine is ready.
    // Explicit exit is conclusive even when its machine has since disconnected.
    if (terminal?.state === "finished" || (!available.has(s.address) && ready.has(machine))) return null;
    seen.add(s.address);
    return s;
  });
  for (const a of all) {
    if (seen.has(a.address) || a.state === "unavailable") continue;
    const i = slots.indexOf(null);
    if (i === -1) break;
    slots[i] = { address: a.address, label: a.label };
    seen.add(a.address);
  }
  if (slots.every((s, i) => s?.address === saved.slots[i]?.address)) return saved;
  return { revision: (saved.revision + 1) >>> 0, slots };
}

// Mode and assignments share one revision so stale presses cannot cross either change.
export function nextRevision(saved) {
  return { ...saved, revision: (saved.revision + 1) >>> 0 };
}
