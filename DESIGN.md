---
name: Herdr Q0 Agents
description: Native Herdr panel for nine stable Keychron Q0 Plus agent slots.
typography:
  body:
    fontSize: "13px"
  control:
    fontSize: "12px"
  meta:
    fontSize: "11px"
rounded:
  control: "5px"
spacing:
  panel: "14px"
  section: "12px"
  row: "6px"
  row-content: "8px"
  compact: "4px"
  candidate: "3px"
  label-stack: "2px"
components:
  action:
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "6px 9px"
  slot-selector:
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    size: "34px"
---

# Design System: Herdr Q0 Agents

## Overview

Q0 Agents is an Operate-mode extension of Herdr's native GPUI interface. It inherits the active Herdr theme and keeps the established compact, dark, information-first visual language; it does not introduce a separate product identity.

- Nine numbered slots fill automatically and remain spatially stable while their agents exist.
- Status is communicated by a short label and semantic color, with firmware lights mirroring the same state model.
- Assignment and mode controls remain subordinate to the slot list.

## Colors

Use Herdr's semantic theme tokens rather than fixed panel colors:

- `chrome` for the panel background.
- `foreground` for titles, agent labels, and controls.
- `muted` for transport text, instructions, empty states, and any status without a dedicated theme token.
- `dim` for unavailable status and the hardware hint.
- `raised` for an unselected slot selector and `selected` for the selected slot.
- `hover` for pointer-hover feedback on actions and candidates.
- `ansi1` for errors.

For other live states, use the matching Herdr theme key when present (`idle`, `working`, `done`, or `blocked`), falling back to `muted`. The firmware palette remains: unassigned off, idle dim white, working pulsing blue, unread completion green, needs-you pulsing amber, error red, and unavailable dim purple.

## Typography

Inherit Herdr's native font stack. The panel uses a restrained three-size hierarchy:

- **Body** (`13px`): panel default.
- **Control / row label** (`12px`): actions, candidate rows, primary slot labels.
- **Meta** (`11px`): transport state, slot status, instructions, and hardware hint.

The panel title uses Herdr's semibold treatment. Long agent labels truncate in assigned-slot rows; candidate rows may use the available scroll area.

## Layout

The panel is a full-size vertical flex container with `14px` padding and `12px` section gaps. The nine-slot list uses `6px` vertical gaps. Each slot row uses an `8px` horizontal gap and vertically centers a fixed `34px × 34px` number selector, a flexible two-line label stack with a `2px` gap, and an optional **Show** action.

The assignment actions use a `4px` gap. Candidate choices use a `3px` gap inside a flexible, vertically scrollable region. Keep the order stable: header and mode, bridge/error message, slots 1–9, assignment actions, instruction, candidates, then the hardware hint.

## Elevation & Depth

The mod applies no shadows. Depth comes from Herdr's tonal `chrome`, `raised`, `selected`, and `hover` surfaces.

## Shapes

Buttons and slot selectors use a `5px` radius. Slots remain square and fixed-size; do not change their silhouette or let content resize them.

## Components

### Slot rows

- The selector displays the stable number 1–9 and changes from `raised` to `selected` when chosen.
- The primary line is the assigned agent label or **Unassigned**. The secondary line is one of **Unassigned**, **Idle**, **Working**, **Unread**, **Needs you**, **Error**, or **Unavailable**.
- A disconnected/loading machine retains its saved assignment as **Unavailable**. A confirmed closed agent releases its key, which may then be filled by a waiting agent.
- **Show** appears only when the slot has a current address and is not unavailable. Do not render a no-op Show action.

### Assignment actions and candidates

- Actions use `9px` horizontal and `6px` vertical padding with a `5px` radius.
- **Assign current → N** assigns the focused Herdr agent to the selected slot. **Next waiting** replaces that key with the first available waiting agent.
- Assigning an agent to another slot moves it rather than duplicating it.
- Candidate rows show `label · address`. Only live terminal candidates with reported status are included; subagents and agents without desktop panes remain eligible when they meet that rule.
- When there are no candidates, show **Agents appear here when they report status.** in `muted` text.

### Transport and state feedback

- Show the bridge message in `muted`. Replace it with **Cannot update keyboard: …** in `ansi1` when snapshot export fails.
- Raw terminal errors remain **Error**. A disconnected remote machine becomes **Unavailable** so it cannot retain a misleading active state.
- Desktop unread/seen state remains authoritative for completion status.

### Mode behavior

- The header action reads **Agent mode** while agent mode is enabled and **Number mode** while ordinary number entry is enabled.
- Mode changes and assignments share a revision. Ignore stale mode and selection commands so a previous mapping cannot act after either changes.
- A slot selection also checks the authoritative shared mode, a current address, and availability before focusing an agent.
- After M1 requests ordinary number entry, firmware immediately permits numbers and rejects old mode frames. The next authoritative state reconciles a concurrent rejected request after the bounded 1.5-second wait documented by the bridge/firmware contract.
- While agent mode is enabling, keys remain numbers until the status lights appear. If the heartbeat expires, the firmware clears the overlay and restores ordinary number entry.

## Do's and Don'ts

- **Do** preserve Herdr's active theme, native typography, and compact density.
- **Do** keep all nine slots visible, ordered, and spatially stable.
- **Do** preserve assignments during connection outages, release confirmed closed agents, and fill empty keys without moving surviving assignments.
- **Do** keep error and unavailable treatments distinct in both the panel and firmware lights.
- **Don't** add fixed brand colors, custom typefaces, gradients, shadows, or decorative identity elements to this mod.
- **Don't** reorder slots by urgency, status, or candidate order.
- **Don't** expose actions that cannot succeed, including Show for an empty or unavailable slot.
- **Don't** allow stale mode or slot commands to cross an assignment or mode revision.
