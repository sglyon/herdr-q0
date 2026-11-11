#include <assert.h>
#include <stdio.h>
#include "qmk_stub.h"
uint32_t layer_state,default_layer_state;
static uint32_t now;
static uint8_t output[32],colors[26][3];
static unsigned writes;
static bool rgb_on;
static uint8_t rgb_mode=5;
uint32_t timer_read32(void) {return now;}
uint32_t timer_elapsed32(uint32_t last) {return now-last;}
uint8_t get_highest_layer(uint32_t s) {uint8_t n=0;while(s>>=1)++n;return n;}
void raw_hid_send(uint8_t *p,uint8_t n) {assert(n==32);memcpy(output,p,n);writes++;}
void rgb_matrix_set_color(uint8_t i,uint8_t r,uint8_t g,uint8_t b) {assert(i<26);colors[i][0]=r;colors[i][1]=g;colors[i][2]=b;}
void rgb_matrix_set_color_all(uint8_t r,uint8_t g,uint8_t b) {for(int i=0;i<26;i++)rgb_matrix_set_color(i,r,g,b);}
bool rgb_matrix_is_enabled(void) {return rgb_on;}
uint8_t rgb_matrix_get_mode(void) {return rgb_mode;}
void rgb_matrix_mode_noeeprom(uint8_t mode) {rgb_mode=mode;}
void rgb_matrix_enable_noeeprom(void) {rgb_on=true;}
void rgb_matrix_disable_noeeprom(void) {rgb_on=false;}
#define QMK_KEYBOARD_H "qmk_stub.h"
#include "../firmware/keymap.c"
static keyrecord_t key(bool pressed) {return (keyrecord_t){.event={.key={4,1},.pressed=pressed}};}
static void update(void) {
    uint8_t p[32]={0};memcpy(p,hq_prefix,4);p[4]=2;p[5]=42;p[9]=1;
    for(int i=0;i<9;i++)p[10+i]=2;
    assert(via_command_kb(p,32));
}
int main(void) {
    uint8_t p[32]={1};assert(!via_command_kb(p,32));assert(!connected);
    memcpy(p,hq_prefix,4);p[4]=1;assert(via_command_kb(p,32));
    assert(output[4]==0x81&&!memcmp(output+9,"Q0H1",4));assert(!connected);
    p[4]=2;p[9]=1;p[10]=255;assert(via_command_kb(p,32));assert(!connected);
    for(int n=0;n<32;n++)assert(!via_command_kb(p,n));
    update();assert(active());assert(revision==42);
    matrix_scan_user();assert(rgb_on&&rgb_mode==RGB_MATRIX_SOLID_COLOR);
    for(int i=1;i<=9;i++) {
        keyrecord_t k=key(true);unsigned before=writes;
        assert(!process_record_user(KC_P1+i-1,&k));
        assert(writes==before+1&&output[4]==3&&output[9]==i&&output[5]==42);
        k.event.pressed=false;assert(!process_record_user(KC_P1+i-1,&k));
    }
    // A release remains swallowed even after a timeout or mode/layer transition.
    keyrecord_t k=key(true);assert(!process_record_user(KC_P1,&k));
    now=HQ_TIMEOUT_MS+1;assert(!active());matrix_scan_user();assert(!rgb_on&&rgb_mode==5);
    k.event.pressed=false;assert(!process_record_user(KC_P1,&k));
    k.event.pressed=true;assert(process_record_user(KC_P1,&k));
    update();layer_state=1u<<EXTRA2;assert(process_record_user(KC_P1,&k));layer_state=0;
    assert(!process_record_user(HQ_TOGGLE,&k));assert(output[4]==5&&output[9]==0);
    assert(mode_pending&&!active());
    assert(process_record_user(KC_P1,&k)); // Immediate M1→1 stays ordinary number entry.
    update();assert(mode_pending&&!active()); // Old heartbeat cannot re-enable capture.
    uint8_t ack[32]={0};memcpy(ack,hq_prefix,4);ack[4]=2;ack[5]=43;ack[9]=0;
    assert(via_command_kb(ack,32));assert(!mode_pending&&!active());
    assert(!process_record_user(HQ_TOGGLE,&k));assert(output[4]==5&&output[9]==1);
    assert(process_record_user(KC_P1,&k)); // Remains numeric while enabling awaits acknowledgement.
    ack[5]=44;ack[9]=1;for(int i=0;i<9;i++)ack[10+i]=2;
    assert(via_command_kb(ack,32));assert(!mode_pending&&active());
    // Host rejects a stale mode request after a concurrent assignment revision.
    assert(!process_record_user(HQ_TOGGLE,&k));assert(mode_pending);
    ack[5]=45;ack[9]=1;
    assert(via_command_kb(ack,32));assert(mode_pending&&!active());
    now+=1500;
    assert(via_command_kb(ack,32));assert(!mode_pending&&active());
    assert(!process_record_user(HQ_TOGGLE,&k));assert(mode_pending); // Toggle is usable again.
    ack[5]=46;ack[9]=0;assert(via_command_kb(ack,32));
    ack[5]=47;ack[9]=1;assert(via_command_kb(ack,32));
    // Every numeric LED index, rendered after the complete background frame.
    memset(colors,0,sizeof colors);now=5600;
    rgb_matrix_indicators_user();
    const int led[9]={19,20,21,15,16,17,10,11,12};
    for(int i=0;i<9;i++)assert(colors[led[i]][2]==220);
    assert(colors[9][2]==0&&colors[22][2]==0);
    // Regression: two idle slots and seven unassigned, against a fully red frame.
    states[0]=1;states[1]=1;for(int i=2;i<9;i++)states[i]=0;
    rgb_matrix_set_color_all(255,0,0);rgb_matrix_indicators_user();
    assert(!rgb_matrix_indicators_advanced_user(0,6)); // Board Num Lock cannot add light.
    assert(colors[19][0]==28&&colors[19][1]==28&&colors[19][2]==28);
    assert(colors[20][0]==28&&colors[20][1]==28&&colors[20][2]==28);
    for(int i=0;i<26;i++)if(i!=19&&i!=20)assert(colors[i][0]==0&&colors[i][1]==0&&colors[i][2]==0);
    agent_mode=false;rgb_matrix_set_color_all(255,0,0);rgb_matrix_indicators_user();
    assert(rgb_matrix_indicators_advanced_user(0,6));
    for(int i=0;i<26;i++)assert(colors[i][0]==255); // Number mode leaves decoration alone.
    agent_mode=true;
    // Encoder/synthetic positions cannot index the switch-state array.
    k.event.key.row=255;assert(process_record_user(KC_P1,&k));
    // Explicit disable restores ordinary keyboard behavior immediately.
    memcpy(p,hq_prefix,4);p[4]=4;assert(via_command_kb(p,32));assert(!active());
    puts("Firmware: protocol, all nine slots, timeout, paired releases, layer bypass, LED map, and VIA passthrough passed");
}
