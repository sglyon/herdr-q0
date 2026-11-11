// SPDX-License-Identifier: GPL-2.0-or-later
// Layout based on upstream Keychron Q0 Plus default keymap (Copyright 2023 Keychron).
#include QMK_KEYBOARD_H
#include "raw_hid.h"
#include "via.h"
#include "protocol.h"

enum { BASE, FUNC, EXTRA2, EXTRA3 };
enum { HQ_TOGGLE = QK_KB_0 };
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [BASE] = LAYOUT_numpad_6x5(
        KC_MUTE, MO(FUNC), KC_ESC, KC_BSPC, KC_TAB,
        HQ_TOGGLE, KC_NUM, KC_PSLS, KC_PAST, KC_PMNS,
        _______, KC_P7, KC_P8, KC_P9, KC_PPLS,
        _______, KC_P4, KC_P5, KC_P6,
        _______, KC_P1, KC_P2, KC_P3, KC_PENT,
        MO(EXTRA2), KC_P0, KC_PDOT),
    [FUNC] = LAYOUT_numpad_6x5(
        RM_TOGG, _______, KC_MUTE, KC_VOLD, KC_VOLU,
        _______, RM_NEXT, RM_VALU, RM_HUEU, KC_DEL,
        _______, RM_PREV, RM_VALD, RM_HUED, _______,
        _______, RM_SATU, RM_SPDU, KC_MPRV,
        _______, RM_SATD, RM_SPDD, KC_MPLY, _______,
        _______, RM_TOGG, KC_MNXT),
    [EXTRA2] = LAYOUT_numpad_6x5(
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______),
    [EXTRA3] = LAYOUT_numpad_6x5(
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______, _______,
        _______, _______, _______, _______, _______,
        _______, _______, _______),
};
const uint16_t PROGMEM encoder_map[][NUM_ENCODERS][NUM_DIRECTIONS] = {
    [BASE] = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [FUNC] = { ENCODER_CCW_CW(RM_VALD, RM_VALU) },
    [EXTRA2] = { ENCODER_CCW_CW(KC_TRNS, KC_TRNS) },
    [EXTRA3] = { ENCODER_CCW_CW(KC_TRNS, KC_TRNS) },
};
static uint32_t last_update, revision;
static uint8_t states[9];
static bool connected, agent_mode;
static bool mode_pending, requested_mode;
static uint32_t requested_revision;
static uint32_t mode_requested_at;
static bool lighting_override, lighting_was_enabled;
static uint8_t lighting_was_mode;
static bool swallowed[MATRIX_ROWS][MATRIX_COLS];
static bool live(void) { return connected && timer_elapsed32(last_update) < HQ_TIMEOUT_MS; }
static bool active(void) { return live() && agent_mode && !mode_pending && get_highest_layer(layer_state | default_layer_state) == BASE; }
static void send_event(uint8_t op, uint8_t slot) {
    uint8_t p[HQ_PACKET_SIZE] = {0};
    memcpy(p, hq_prefix, 4); p[4] = op;
    p[5] = revision; p[6] = revision >> 8; p[7] = revision >> 16; p[8] = revision >> 24; p[9] = slot;
    raw_hid_send(p, sizeof(p));
}
// Only our reserved command is consumed; every ordinary VIA command is untouched.
bool via_command_kb(uint8_t *p, uint8_t n) {
    if (!hq_header(p, n)) return false;
    if (p[4] == 1) {
        mode_pending = false; // A fresh bridge session reconciles from authoritative Herdr state.
        memset(p + 4, 0, n - 4); p[4] = 0x81; memcpy(p + 9, "Q0H1", 4);
        raw_hid_send(p, n);
    } else if (p[4] == 2 && hq_valid_state(p)) {
        if (mode_pending) {
            // Ignore pre-toggle heartbeats. No keys are captured until Herdr acknowledges.
            bool acknowledged = hq_revision(p) != requested_revision && (bool)p[9] == requested_mode;
            // A concurrent assignment can reject the mode request. Reconcile to Herdr's
            // authoritative mode after a bounded wait instead of wedging the toggle.
            if (!acknowledged && timer_elapsed32(mode_requested_at) < 1500) return true;
            mode_pending = false;
        }
        revision = hq_revision(p); agent_mode = p[9]; memcpy(states, p + 10, 9);
        last_update = timer_read32(); connected = true;
    } else if (p[4] == 4) {
        connected = false; mode_pending = false;
    }
    return true;
}
bool process_record_user(uint16_t code, keyrecord_t *record) {
    uint8_t row = record->event.key.row, col = record->event.key.col;
    if (row >= MATRIX_ROWS || col >= MATRIX_COLS) return true;
    // Always pair swallowed presses/releases, including disconnects while a key is held.
    if (!record->event.pressed && swallowed[row][col]) { swallowed[row][col] = false; return false; }
    if (code == HQ_TOGGLE) {
        if (record->event.pressed && live() && !mode_pending) {
            requested_mode = !agent_mode; requested_revision = revision; mode_pending = true;
            mode_requested_at = timer_read32();
            send_event(5, requested_mode);
        }
        return false;
    }
    uint8_t slot = code >= KC_P1 && code <= KC_P9 ? code - KC_P1 + 1 : 0;
    if (slot && active() && record->event.pressed) {
        swallowed[row][col] = true;
        send_event(3, slot);
        return false;
    }
    return true;
}
void matrix_scan_user(void) {
    bool enabled = active();
    if (enabled && !lighting_override) {
        lighting_was_enabled = rgb_matrix_is_enabled();
        lighting_was_mode = rgb_matrix_get_mode();
        rgb_matrix_mode_noeeprom(RGB_MATRIX_SOLID_COLOR);
        rgb_matrix_enable_noeeprom();
        lighting_override = true;
    } else if (!enabled && lighting_override) {
        rgb_matrix_mode_noeeprom(lighting_was_mode);
        if (!lighting_was_enabled) rgb_matrix_disable_noeeprom();
        lighting_override = false;
    }
}
bool rgb_matrix_indicators_user(void) {
    if (!active()) return true;
    // Final-frame pass: decorative animations and neighboring LEDs must not
    // obscure unassigned slots or overwrite status colors in later chunks.
    rgb_matrix_set_color_all(0, 0, 0);
    // Exact indices from keyboards/keychron/q0/plus/keyboard.json, in numeric order.
    static const uint8_t leds[9] = {19,20,21,15,16,17,10,11,12};
    static const uint8_t colors[7][3] = {
        {0,0,0}, {28,28,28}, {24,90,220}, {24,200,65}, {230,130,12}, {240,24,24}, {35,25,40}
    };
    uint16_t phase = timer_read32() % 1600;
    uint16_t pulse = phase < 800 ? 70 + phase * 185 / 800 : 255 - (phase - 800) * 185 / 800;
    for (uint8_t i=0; i<9; ++i) {
        uint8_t s = states[i]; uint16_t scale = s == 2 || s == 4 ? pulse : 255;
        rgb_matrix_set_color(leds[i], colors[s][0]*scale/255, colors[s][1]*scale/255, colors[s][2]*scale/255);
    }
    return true;
}
bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max) {
    (void)led_min; (void)led_max;
    // Suppress the board's decorative Num Lock indicator in agent mode too.
    return !active();
}
