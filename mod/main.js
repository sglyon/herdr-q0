import { View, div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { agents, terminals, machines, focused, theme, shared, setShared, appHome, nextCommand, run, notify, readTextFile, writeTextFile } from "herdr";
import { STORE, assignments, candidates, snapshot, assign, reconcile, nextRevision } from "./model.js";

export default class Q0Agents extends View {
  init(_props, cx) {
    this.selected = 1;
    this.enabled = shared("q0-agents.enabled") !== false;
    this.bridge = "Bridge not running";
    this.error = "";
    this.busy = false;
    this.cached = null;
    this.directory = `${appHome()}/mods/q0-agents`;
    // Only transport heartbeat is periodic. agents()/terminals() are read reactively in render.
    cx.timer.every(750, cx => this.exchange(cx));
    cx.spawn(async cx => {
      for (;;) {
        const command = await nextCommand();
        const mode = /^mode-(\d+)-([01])$/.exec(command);
        if (mode && assignments(shared(STORE)).revision === Number(mode[1]))
          this.setMode(mode[2] === "1", cx);
        if (command.startsWith("select-")) {
          const match = /^select-(\d+)-([1-9])$/.exec(command);
          const saved = assignments(shared(STORE));
          if (match && saved.revision === Number(match[1])) {
            const s = this.cached?.slots[Number(match[2]) - 1];
            if (shared("q0-agents.enabled") !== false && s?.address && s.state !== "unavailable") run("agent.focus", { terminal: s.address });
          }
        }
        const a = /^assign-([1-9])$/.exec(command);
        if (a) this.assignCurrent(Number(a[1]), cx);
        const clear = /^clear-([1-9])$/.exec(command);
        if (clear) this.save(Number(clear[1]), null, cx);
        cx.notify();
      }
    });
  }

  exchange(cx) {
    if (this.busy || !this.cached) return;
    this.busy = true;
    const body = { ...this.cached, timestamp: Date.now() };
    cx.spawn(async cx => {
      try {
        // Hidden runtime files are ignored by Herdr's mod source watcher.
        const path = `${this.directory}/.state.json`;
        const expected = await readTextFile(path);
        await writeTextFile(path, JSON.stringify(body), expected);
        let label = "Bridge not running";
        try {
          const b = JSON.parse(await readTextFile(`${this.directory}/.bridge-status.json`));
          if (b && Date.now() - b.timestamp < 4000) label = b.message;
        } catch (_) { /* Bridge may not be installed or started yet. */ }
        if (this.bridge !== label || this.error) { this.bridge = label; this.error = ""; cx.notify(); }
      } catch (e) {
        const message = `Cannot update keyboard: ${String(e)}`;
        if (this.error !== message) { this.error = message; cx.notify(); }
      } finally { this.busy = false; }
    });
  }

  save(slot, agent, cx) {
    setShared(STORE, assign(assignments(shared(STORE)), slot, agent));
    cx.notify();
  }

  setMode(enabled, cx) {
    setShared("q0-agents.enabled", enabled);
    setShared(STORE, nextRevision(assignments(shared(STORE))));
    cx.notify();
  }

  assignCurrent(slot, cx) {
    const f = focused();
    const agent = this.all?.find(a => a.address === (f?.terminal || f?.agent));
    if (agent) this.save(slot, agent, cx);
    else notify({ title: "Select an agent first", body: "Focus an agent in Herdr, then assign it to a number.", level: "info" });
  }

  button(id, text, action, t) {
    return div().id(id).px(9).py(6).rounded(5).text_size(12).text_color(t.foreground)
      .cursor_pointer().hover(s => s.bg(t.hover)).on_click(action).child(text);
  }

  render(cx) {
    const t = theme();
    const terminalList = terminals();
    const machineList = machines();
    this.all = candidates(agents(), terminalList, machineList);
    const previous = assignments(shared(STORE));
    const saved = reconcile(previous, this.all, terminalList, machineList);
    if (saved !== previous) setShared(STORE, saved);
    const keyByAddress = new Map(saved.slots.flatMap((s, i) => s ? [[s.address, i + 1]] : []));
    const waiting = this.all.filter(a => !keyByAddress.has(a.address) && a.state !== "unavailable");
    this.enabled = shared("q0-agents.enabled") !== false;
    this.cached = snapshot(saved, this.all, this.enabled);
    const color = s => s === "error" ? t.ansi1 : s === "unavailable" ? t.dim : t[s] || t.muted;
    const label = { off: "Unassigned", idle: "Idle", working: "Working", done: "Unread", blocked: "Needs you", error: "Error", unavailable: "Unavailable" };
    const row = slot => {
      const s = this.cached.slots[slot - 1];
      return h_flex().gap(8).items_center().children([
        div().id(`slot-${slot}`).w(34).h(34).flex_none().rounded(5).flex().items_center().justify_center()
          .bg(this.selected === slot ? t.selected : t.raised).text_color(color(s.state))
          .cursor_pointer().tooltip(`Choose slot ${slot}`).on_click((_e, cx) => { this.selected = slot; cx.notify(); }).child(String(slot)),
        v_flex().flex_1().min_w(0).gap(2).children([
          div().truncate().text_size(12).text_color(t.foreground).child(s.label),
          div().text_size(11).text_color(color(s.state)).child(label[s.state]),
        ]),
        ...(s.address && s.state !== "unavailable"
          ? [this.button(`show-${slot}`, "Show", () => run("agent.focus", { terminal: s.address }), t)] : []),
      ]);
    };
    return v_flex().size_full().min_h(0).bg(t.chrome).p(14).gap(12).text_size(13).children([
      h_flex().items_center().justify_between().children([
        div().font_semibold().child("Q0 agents"),
        this.button("mode", this.enabled ? "Agent mode" : "Number mode", (_e, cx) => {
          this.setMode(shared("q0-agents.enabled") === false, cx);
        }, t),
      ]),
      div().text_size(11).text_color(this.error ? t.ansi1 : t.muted).child(this.error || this.bridge),
      v_flex().id("slots").gap(6).children([1,2,3,4,5,6,7,8,9].map(row)),
      h_flex().gap(4).children([
        this.button("assign-current", `Assign current → ${this.selected}`, (_e, cx) => this.assignCurrent(this.selected, cx), t),
        ...(waiting.length ? [this.button("next-waiting", "Next waiting", (_e, cx) => this.save(this.selected, waiting[0], cx), t)] : []),
      ]),
      div().text_size(11).text_color(t.muted).child(waiting.length
        ? `${waiting.length} waiting. Choose an agent below to replace key ${this.selected}.`
        : "New agents fill empty keys automatically. Existing agents keep their numbers."),
      v_flex().id("choices").flex_1().min_h(0).overflow_y_scrollbar().gap(3).children(
        this.all.length ? this.all.map(a => this.button(`candidate-${a.address}`, `${keyByAddress.has(a.address) ? `Key ${keyByAddress.get(a.address)}` : "Waiting"} · ${a.label} · ${a.address}`, (_e, cx) => this.save(this.selected, a, cx), t))
          : [div().text_color(t.muted).child("Agents appear here when they report status.")]),
      div().text_size(11).text_color(t.dim).child("M1 toggles numbers · Hold M5 for number entry"),
    ]);
  }
}
