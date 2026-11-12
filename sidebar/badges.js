import { div } from "gpui-kit";
import { assignments } from "./model.js";

// Addresses are stable across title, status, grouping, and sort changes.
export function assignedKeys(value) {
  const keys = new Map();
  assignments(value).slots.forEach((slot, i) => {
    if (slot?.address && !keys.has(slot.address)) keys.set(slot.address, i + 1);
  });
  return keys;
}

export function keyBadge(t, address, keys, enabled) {
  const key = keys.get(address);
  if (!key) return null;
  return div().id(`q0-key-${address}`).size(18).flex_none().rounded(4)
    .bg(t.raised).text_color(enabled ? t.foreground : t.muted)
    .text_size(11).font_medium().flex().items_center().justify_center()
    .tooltip(`Q0 key ${key}${enabled ? "" : " · Number mode selected"}`)
    .child(String(key));
}
