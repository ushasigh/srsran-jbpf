// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "rlc_defines.h"
#include "rlc_dl_north_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


struct jbpf_load_map_def SEC("maps") dl_north_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl_north = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_dl_north_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_north_hash, MAX_NUM_UE_RB);



// #define DEBUG_PRINT

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
    
    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_north_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    rlc_dl_north_stats *out = (rlc_dl_north_stats *)jbpf_map_lookup_elem(&stats_map_dl_north, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;


    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(rlc_ctx.is_srb, rlc_ctx.rb_id);

    // Store SDU arrival time so we can calculate delay and queue size at the rlc level
    uint32_t sdu_length = (uint32_t) (ctx->srs_meta_data1 >> 32);

#ifdef DEBUG_PRINT
    // jbpf_printf_debug("rlc DL NEW SDU: du_ue_index=%d, sdu_length=%d, count=%d\n", 
    //     rlc_ctx.du_ue_index, sdu_length, count);
    jbpf_printf_debug("RLC DL NEW SDU: du_ue_index=%d, rb_id=%d, sdu_length=%d\n", 
        rlc_ctx.du_ue_index, rb_id, sdu_length);
#endif

    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_north_hash, rlc_ctx.du_ue_index, rb_id, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].du_ue_index = rlc_ctx.du_ue_index;
        out->stats[ind % MAX_NUM_UE_RB].is_srb = rlc_ctx.is_srb;
        out->stats[ind % MAX_NUM_UE_RB].rb_id = rlc_ctx.rb_id;
        out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.total = 0;
    }

    *not_empty_stats = 1;

    out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.count++; 
    out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.total += sdu_length;

    return JBPF_CODELET_SUCCESS;
}
