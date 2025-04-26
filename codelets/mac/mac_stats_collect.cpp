// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "mac_sched_crc_stats.pb.h"

#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define MAX_NUM_UE 32


jbpf_ringbuf_map(output_map, mac_stats, 1000);

struct jbpf_load_map_def SEC("maps") crc_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") last_time = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint64_t),
    .max_entries = 1,
};

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_crc = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(mac_stats),
    .max_entries = 1,
};


DEFINE_PROTOHASH_32(crc_hash, MAX_NUM_UE);

// Consecutive packet losses
struct jbpf_load_map_def SEC("maps") cnt_loss = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(uint64_t),
    .value_size = sizeof(uint32_t),
    .max_entries = MAX_NUM_UE,
};




//#define DEBUG_PRINT 1

extern "C" SEC("jbpf_ran_layer2")
uint64_t jbpf_main(void *state)
{
    struct jbpf_stats_ctx *ctx;
    uint64_t zero_index = 0;
    uint64_t timestamp;

    ctx = (struct jbpf_stats_ctx *)state;

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&crc_not_empty, &zero_index);
    if (!not_empty_stats)
        return JBPF_CODELET_FAILURE;

    // Get stats map buffer to save output across invocations
    void *c = jbpf_map_lookup_elem(&stats_map_crc, &zero_index);
    if (!c)
        return JBPF_CODELET_FAILURE;
    mac_stats *out = (mac_stats *)c;

    uint64_t *last_timestamp = (uint64_t*)jbpf_map_lookup_elem(&last_time, &zero_index);
    if (!last_timestamp)
        return JBPF_CODELET_FAILURE;

    // Timestamp field name should not change as it is hardcoded in post processing
    timestamp = jbpf_time_get_ns();

    uint64_t timestamp32 = (uint64_t) (timestamp >> 30);

#ifdef DEBUG_PRINT
        jbpf_printf_debug("OUTPUT CHECK: %lu %u\n", timestamp32, *last_timestamp);
#endif

    if (*not_empty_stats && *last_timestamp < timestamp32)
    {
        out->timestamp = timestamp;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("OUTPUT: %lu\n", out->timestamp);
#endif

        int ret = jbpf_ringbuf_output(&output_map, (void *) out, sizeof(mac_stats));

        JBPF_HASHMAP_CLEAR(&crc_hash);
        
        // Reset the info
        // NOTE: this is not thread safe, but we don't care here
        // The worst case we can overwrite someone else writing
        jbpf_map_clear(&stats_map_crc);
        jbpf_map_clear(&cnt_loss);

        *not_empty_stats = 0;
        *last_timestamp = timestamp32;

        if (ret < 0) {
            return JBPF_CODELET_FAILURE;
        }

    }

    return JBPF_CODELET_SUCCESS;
}
