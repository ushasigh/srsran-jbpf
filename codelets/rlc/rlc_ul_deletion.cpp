// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "rlc_defines.h"
#include "rlc_ul_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


#define MAX_NUM_UE_RB (256)

//// UL stats

jbpf_ringbuf_map(output_map_ul, rlc_ul_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_ul = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_ul_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(ul_hash, MAX_NUM_UE_RB);



//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    
    const jbpf_rlc_ctx_info& rlc_ctx = *reinterpret_cast<const jbpf_rlc_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&rlc_ctx) + sizeof(jbpf_rlc_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(rlc_ctx.is_srb, rlc_ctx.rb_id);    

#ifdef DEBUG_PRINT
    jbpf_printf_debug("rlc_dl_deletion: du_ue_index=%d, rb_id=%d\n", 
        ue_index, rb_id);
#endif


    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
       
    rlc_ul_stats *out = (rlc_ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, ul_hash, rb_id, rlc_ctx.du_ue_index, new_val);

    out->stats[ind % MAX_NUM_UE_RB].du_ue_index = rlc_ctx.du_ue_index;
    out->stats[ind % MAX_NUM_UE_RB].is_srb = rlc_ctx.is_srb;
    out->stats[ind % MAX_NUM_UE_RB].rb_id = rlc_ctx.rb_id;
    out->stats[ind % MAX_NUM_UE_RB].rlc_mode = rlc_ctx.rlc_mode;

    out->stats[ind % MAX_NUM_UE_RB].pdu_bytes.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].pdu_bytes.total = 0;

    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_bytes.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_bytes.total = 0;

    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.total = 0;
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.min = UINT32_MAX;
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.max = 0;

    out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.total = 0;
    out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.min = UINT32_MAX;
    out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.max = 0;
    out->stats[ind % MAX_NUM_UE_RB].has_um = false;

    out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.count = 0;
    out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.total = 0;
    out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min = UINT32_MAX;
    out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max = 0;
    out->stats[ind % MAX_NUM_UE_RB].has_am = false;

    return JBPF_CODELET_SUCCESS;
}