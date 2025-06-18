// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_dl_pkts.h"
#include "pdcp_dl_south_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"



struct jbpf_load_map_def SEC("maps") dl_south_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl_south = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_south_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_south_hash, MAX_NUM_UE_RB);

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
struct jbpf_load_map_def SEC("maps") sdu_events = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_events),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(delay_hash, MAX_SDU_IN_FLIGHT);
#endif


//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;

    const jbpf_pdcp_ctx_info& pdcp_ctx = *reinterpret_cast<const jbpf_pdcp_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&pdcp_ctx) + sizeof(jbpf_pdcp_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_south_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    dl_south_stats *out = (dl_south_stats *)jbpf_map_lookup_elem(&stats_map_dl_south, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    t_sdu_events *events = (t_sdu_events *)jbpf_map_lookup_elem(&sdu_events, &zero_index);
    if (!events)
        return JBPF_CODELET_FAILURE;
#endif

    // out->timestamp = jbpf_time_get_ns();
    // out->cu_ue_index = pdcp_ctx.cu_ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->count = ctx->srs_meta_data1 >> 32;
    // out->window_size = ctx->srs_meta_data1 & 0xFFFFFFFF;

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);    

    uint32_t count = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t pdu_length = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t window_size = (uint32_t) (ctx->srs_meta_data2 & 0xFFFFFFFF);
    uint32_t is_retx = (uint32_t) (ctx->srs_meta_data2 >> 32);

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL TX PDU : cu_ue_index=%d, rb_id=%d, count=%d ", 
        pdcp_ctx.cu_ue_index, rb_id, count);
    jbpf_printf_debug("sdu_length=%d, window_size=%d, is_retx=%d ", 
        sdu_length, window_size, is_retx);
#endif

    // Update stats
    int new_val = 0;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_south_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    if (new_val) {
        memset(&out->stats[ind % MAX_NUM_UE_RB], 0, sizeof(t_dls_stats));
        out->stats[ind % MAX_NUM_UE_RB].cu_ue_index = pdcp_ctx.cu_ue_index;
        out->stats[ind % MAX_NUM_UE_RB].is_srb = pdcp_ctx.is_srb;
        out->stats[ind % MAX_NUM_UE_RB].rb_id = pdcp_ctx.rb_id;
        out->stats[ind % MAX_NUM_UE_RB].window.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].rlc_tx_delay.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].total_delay.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.min = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.min = UINT32_MAX;
    }

    out->stats[ind % MAX_NUM_UE_RB].window.count++;
    out->stats[ind % MAX_NUM_UE_RB].window.total += window_size;
    if (out->stats[ind % MAX_NUM_UE_RB].window.min > window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.min = window_size;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].window.max < window_size) {
        out->stats[ind % MAX_NUM_UE_RB].window.max = window_size;
    }

    *not_empty_stats = 1;

#ifdef PDCP_REPORT_DL_DELAY_QUEUE

    if (count % PDCP_QUEUE_SAMPLING_RATE != 0) {
        return JBPF_CODELET_SUCCESS;
    }  

    uint32_t delay_hash_key = PDCP_DL_DELAY_HASH_KEY(rb_id, pdcp_ctx.cu_ue_index);

    int sdu_length = 0;

    // Just find the key, don't add it. It was added in dl_new_sdu.
    // It should always be found, but maybe the hash has been cleaned, then ignore
    uint64_t compound_key = ((uint64_t)count << 31) << 1 | (uint64_t)delay_hash_key; 
    uint32_t *pind = (uint32_t *)jbpf_map_lookup_elem(&delay_hash, &compound_key); 
    if (pind) {
        uint32_t aind = *pind;

        uint64_t now_ns = jbpf_time_get_ns();
        events->map[aind % MAX_SDU_IN_FLIGHT].pdcpTx_ns = now_ns;

        // get sdu length
        sdu_length = events->map[aind % MAX_SDU_IN_FLIGHT].sdu_length;

        // update SDU traffic stats
        if (is_retx) {
            out->stats[ind % MAX_NUM_UE_RB].sdu_retx_bytes.count++; 
            out->stats[ind % MAX_NUM_UE_RB].sdu_retx_bytes.total += sdu_length;
        } else {
            out->stats[ind % MAX_NUM_UE_RB].sdu_tx_bytes.count++; 
            out->stats[ind % MAX_NUM_UE_RB].sdu_tx_bytes.total += sdu_length;
        }

        // only calculate pdcp_tx_delay if we have a valid sdu arrival time
        if ((events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns > 0) &&
            (events->map[aind % MAX_SDU_IN_FLIGHT].pdcpTx_ns > events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns)) {

            uint64_t delay = events->map[aind % MAX_SDU_IN_FLIGHT].pdcpTx_ns - events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns;

#ifdef DEBUG_PRINT
            jbpf_printf_debug("PDCP DL TX PDU,  : count=%d, delay=%d\n", 
                count, delay);
#endif       

            out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.count++; 
            out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.total += delay;
            if (out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.min > delay) {
                out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.min = delay;
            }
            if (out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.max < delay) {
                out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.max = delay;
            }

        } else {
            out->stats[ind % MAX_NUM_UE_RB].pdcp_tx_delay.count = 0;
        }

    } else {
        // Just find the key, don't add it. 
        // It should always be found, but maybe the hash has been cleaned, then ignore
//#ifdef DEBUG_PRINT
        jbpf_printf_debug("PDCP DL TX PDU KEY NOT FOUND: count=%d \n", 
            count);
//#endif
    }    

#endif
    
    return JBPF_CODELET_SUCCESS;
}
