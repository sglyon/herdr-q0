#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#define PROGMEM
#define MATRIX_ROWS 6
#define MATRIX_COLS 5
#define NUM_ENCODERS 1
#define NUM_DIRECTIONS 2
#define RGB_MATRIX_SOLID_COLOR 1
#define LAYOUT_numpad_6x5(...) {{0}}
#define ENCODER_CCW_CW(a,b) {a,b}
#define MO(n) (0x5220+(n))
enum { KC_NO, KC_TRNS, KC_MUTE, KC_ESC, KC_BSPC, KC_TAB, KC_NUM, KC_PSLS, KC_PAST, KC_PMNS, KC_PPLS,
KC_PENT, KC_P0, KC_PDOT, KC_DEL, KC_MPRV, KC_MPLY, KC_MNXT, KC_VOLU, KC_VOLD,
KC_P1=0x59,KC_P2,KC_P3,KC_P4,KC_P5,KC_P6,KC_P7,KC_P8,KC_P9,
RM_TOGG=0x7800,RM_NEXT,RM_VALU,RM_HUEU,RM_PREV,RM_VALD,RM_HUED,RM_SATU,RM_SPDU,RM_SATD,RM_SPDD,
QK_KB_0=0x7e00 };
#define _______ KC_TRNS
typedef struct { struct { struct {uint8_t row,col;} key; bool pressed; } event; } keyrecord_t;
extern uint32_t layer_state, default_layer_state;
uint32_t timer_read32(void);
uint32_t timer_elapsed32(uint32_t last);
uint8_t get_highest_layer(uint32_t s);
void raw_hid_send(uint8_t *data,uint8_t n);
void rgb_matrix_set_color(uint8_t led,uint8_t r,uint8_t g,uint8_t b);
void rgb_matrix_set_color_all(uint8_t r,uint8_t g,uint8_t b);
bool rgb_matrix_is_enabled(void);
uint8_t rgb_matrix_get_mode(void);
void rgb_matrix_mode_noeeprom(uint8_t mode);
void rgb_matrix_enable_noeeprom(void);
void rgb_matrix_disable_noeeprom(void);
