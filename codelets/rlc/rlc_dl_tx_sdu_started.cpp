// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "rlc_defines.h"
#include "rlc_dl_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"


struct jbpf_load_map_def SEC("maps") dl_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_dl_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_hash, MAX_NUM_UE_RB);




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
    
    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    rlc_dl_stats *out = (rlc_dl_stats *)jbpf_map_lookup_elem(&stats_map_dl, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;


    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(rlc_ctx.is_srb, rlc_ctx.rb_id);

    // Store SDU arrival time so we can calculate delay and queue size at the rlc level
    uint32_t pdcp_sn = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t is_retx = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t latency_ns = (uint32_t)ctx->srs_meta_data2;

#ifdef DEBUG_PRINT
    jbpf_printf_debug("RLC DL TX SDU STARTED: du_ue_index=%d, rb_id=%d, pdu_length=%d\n", 
        rlc_ctx.du_ue_index, rb_id, pdu_len);
#endif

    int new_val = 0;

    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_hash, rlc_ctx.du_ue_index, rb_id, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].du_ue_index = rlc_ctx.du_ue_index;
        out->stats[ind % MAX_NUM_UE_RB].is_srb = rlc_ctx.is_srb;
        out->stats[ind % MAX_NUM_UE_RB].rb_id = rlc_ctx.rb_id;
        out->stats[ind % MAX_NUM_UE_RB].rlc_mode = rlc_ctx.rlc_mode;
        
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.max = 0;
        
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.max = 0;
        
        out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_new_bytes.total = 0;

        out->stats[ind % MAX_NUM_UE_RB].pdu_tx_bytes.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].pdu_tx_bytes.total = 0;

        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.max = 0;

        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_completed.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_completed.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_completed.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_completed.max = 0;

        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_delivered.count = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_delivered.total = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_delivered.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_delivered.max = 0;

        if (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM) {

            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_bytes.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_bytes.total = 0;

            out->stats[ind % MAX_NUM_UE_RB].am.pdu_status_bytes.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_status_bytes.total = 0;

            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_count.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_count.total = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_count.min = UINT32_MAX;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_retx_count.max = 0;

            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.count = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.total = 0;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min = UINT32_MAX;
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max = 0;

            out->stats[ind % MAX_NUM_UE_RB].has_am = true;
        }
    }

    /////////////////////////////////////////////
    // update sdu_queue_pkts and sdu_queue_bytes
    const jbpf_queue_info_t* queue_info = NULL;
    if ((rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM) && (rlc_ctx.u.am_tx.sdu_queue_info.used)) {
        queue_info = &rlc_ctx.u.am_tx.sdu_queue_info;
    } else if ((rlc_ctx.rlc_mode == JBPF_RLC_MODE_UM) && (rlc_ctx.u.um_tx.sdu_queue_info.used)) {
        queue_info = &rlc_ctx.u.um_tx.sdu_queue_info;
    } else if ((rlc_ctx.rlc_mode == JBPF_RLC_MODE_TM) && (rlc_ctx.u.tm_tx.sdu_queue_info.used)) {
        queue_info = &rlc_ctx.u.tm_tx.sdu_queue_info;
    }  
    if (queue_info) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.count++;
        if (queue_info->pkts < out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.min) {
            out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.min = queue_info->pkts;
        }
        if (queue_info->pkts > out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.max) {
            out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.max = queue_info->pkts;
        }
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_pkts.total += queue_info->pkts;

        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.count++;
        if (queue_info->bytes < out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.min) {
            out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.min = queue_info->bytes;
        }
        if (queue_info->bytes > out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.max) {
            out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.max = queue_info->bytes;
        }
        out->stats[ind % MAX_NUM_UE_RB].sdu_queue_bytes.total += queue_info->bytes;
    }

    /////////////////////////////////////////////
    // sdu_tx_started
    out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.count++;
    if (latency_ns < out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.min) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.min = latency_ns;
    }
    if (latency_ns > out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.max) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.max = latency_ns;
    }
    out->stats[ind % MAX_NUM_UE_RB].sdu_tx_started.total += latency_ns;

    /////////////////////////////////////////////
    // AM fields
    if (out->stats[ind % MAX_NUM_UE_RB].has_am) {

        /////////////////////////////////////////////
        // update pdu_window
        const jbpf_queue_info_t* queue_info = &rlc_ctx.u.am_tx.window_info;
        if (!queue_info->used) {
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.count++;
            if (queue_info->pkts < out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min) {
                out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.min = queue_info->pkts;
            }
            if (queue_info->pkts > out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max) {
                out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.max = queue_info->pkts;
            }
            out->stats[ind % MAX_NUM_UE_RB].am.pdu_window.total += queue_info->pkts;  
        } 
    }	

    *not_empty_stats = 1;

    return JBPF_CODELET_SUCCESS;
}
