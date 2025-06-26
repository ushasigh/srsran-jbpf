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


struct jbpf_load_map_def SEC("maps") ul_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_ul = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_ul_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(ul_hash, MAX_NUM_UE_RB);




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
    
    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&ul_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    rlc_ul_stats *out = (rlc_ul_stats *)jbpf_map_lookup_elem(&stats_map_ul, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;


    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(rlc_ctx.is_srb, rlc_ctx.rb_id);

    // Store SDU arrival time so we can calculate delay and queue size at the rlc level
    uint32_t pdcp_sn = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t sdu_length = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t latency_ns = (uint32_t)ctx->srs_meta_data2;

#ifdef DEBUG_PRINT
    jbpf_printf_debug("RLC UL DELIVER SDU: du_ue_index=%d, rb_id=%d, sdu_length=%d\n", 
        rlc_ctx.du_ue_index, rb_id, sdu_length);
#endif

    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, ul_hash, rlc_ctx.du_ue_index, rb_id, new_val);
    if (new_val) {
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

        if (rlc_ctx.rlc_mode == JBPF_RLC_MODE_UM) {

            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.total = 0;
            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.min = UINT32_MAX;
            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.max = 0;

            out->stats[ind % MAX_NUM_UE_RB].has_um = true;
        }

        if (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM) {

            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.total = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min = UINT32_MAX;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max = 0;

            out->stats[ind % MAX_NUM_UE_RB].has_am = true;
        }
    }

    /////////////////////////////////////////////
    // sdu_delivered_bytes
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_bytes.count++;
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_bytes.total += sdu_length;

    /////////////////////////////////////////////
    // sdu_delivered_latency
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.count++;
    if (latency_ns < out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.min) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.min = latency_ns;
    }
    if (latency_ns > out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.max) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.max = latency_ns;
    }
    out->stats[ind % MAX_NUM_UE_RB].sdu_delivered_latency.total += latency_ns;

    /////////////////////////////////////////////
    // UM
    if (out->stats[ind % MAX_NUM_UE_RB].has_um) {

        /////////////////////////////////////////////
        // update pdu_window
        out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.count++;
        if (rlc_ctx.u.um_rx.window_size < out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.min) {
            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.min = rlc_ctx.u.um_rx.window_size;
        }
        if (rlc_ctx.u.um_rx.window_size > out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.max) {
            out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.max = rlc_ctx.u.um_rx.window_size;
        }
        out->stats[ind % MAX_NUM_UE_RB].um.pdu_window.total += rlc_ctx.u.um_rx.window_size;   
    }	
	
    /////////////////////////////////////////////
    // AM
    if (out->stats[ind % MAX_NUM_UE_RB].has_am) {

        /////////////////////////////////////////////
        // update pdu_window
        out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.count++;
        if (rlc_ctx.u.am_rx.window_size < out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min) {
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min = rlc_ctx.u.am_rx.window_size;
        }
        if (rlc_ctx.u.am_rx.window_size > out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max) {
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max = rlc_ctx.u.am_rx.window_size;
        }
        out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.total += rlc_ctx.u.am_rx.window_size;   
    }	
     
    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
