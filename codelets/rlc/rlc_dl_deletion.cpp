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


#define MAX_NUM_UE_RB (256)

jbpf_ringbuf_map(output_map_dl, rlc_dl_stats, 1000);

// We store stats in this (single entry) map across runs
struct jbpf_load_map_def SEC("maps") stats_map_dl = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(rlc_dl_stats),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(dl_hash, MAX_NUM_UE_RB);



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


    // When a bearer context is setup, we need to reset the last acked
    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
    uint32_t ack_ind = 0;
    
    rlc_dl_stats *out = (rlc_dl_stats *)jbpf_map_lookup_elem(&stats_map_dl, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_hash, rb_id, rlc_ctx.du_ue_index, new_val);

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

    out->stats[ind % MAX_NUM_UE_RB].has_am = false;


    return JBPF_CODELET_SUCCESS;
}