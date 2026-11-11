// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#define HQ_PACKET_SIZE 32
#define HQ_TIMEOUT_MS 2500
static const uint8_t hq_prefix[4] = {0xf0, 0x48, 0x51, 1};
static inline bool hq_header(const uint8_t *p, uint8_t n) {
    return n == HQ_PACKET_SIZE && memcmp(p, hq_prefix, 4) == 0;
}
static inline uint32_t hq_revision(const uint8_t *p) {
    return (uint32_t)p[5] | (uint32_t)p[6] << 8 | (uint32_t)p[7] << 16 | (uint32_t)p[8] << 24;
}
static inline bool hq_valid_state(const uint8_t *p) {
    if (p[9] > 1) return false;
    for (uint8_t i = 0; i < 9; ++i) if (p[10+i] > 6) return false;
    return true;
}
