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

#define MAX_NUM_UE_RB (256)

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


struct jbpf_load_map_def SEC("maps") sdu_arrivals = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_arrivals),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") sdu_queues = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_queues),
    .max_entries = 1,
};


// DEFINE_PROTOHASH_64(delay_hash, MAX_SDU_IN_FLIGHT);
// DEFINE_PROTOHASH_64(queue_hash, MAX_SDU_QUEUES);




//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL DELIVER SDU START\n"); 
#endif


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

    t_sdu_arrivals *arrivals = (t_sdu_arrivals *)jbpf_map_lookup_elem(&sdu_arrivals, &zero_index);
    if (!arrivals)
        return JBPF_CODELET_FAILURE;

    t_sdu_queues *queues = (t_sdu_queues *)jbpf_map_lookup_elem(&sdu_queues, &zero_index);
    if (!queues)
        return JBPF_CODELET_FAILURE;


    // out->timestamp = jbpf_time_get_ns();
    // out->ue_index = pdcp_ctx.ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->notif_count = ctx->srs_meta_data1 >> 32;
    // out->window_size = ctx->srs_meta_data1 & 0xFFFFFFFF;


    uint32_t sdu_length = (uint32_t )(ctx->srs_meta_data1 >> 32);
    uint32_t window_size = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t notif_count = (uint32_t) (ctx->srs_meta_data1 >> 32);

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL DELIVER SDU: ue_index=%d, rb_id=%d, notif_count=%d\n", 
        pdcp_ctx.ue_index, pdcp_ctx.rb_id, notif_count);
#endif


    // Find matching arrival and queue size info
    // NOTE: This has to be here to appease the verifier.
    uint32_t key1 = 
        ((uint64_t)(pdcp_ctx.rb_id & 0xFFFF) << 15) << 1 | 
        ((uint64_t)(pdcp_ctx.ue_index & 0xFFFF));

    int anew_val = 0;
    //uint32_t aind = JBPF_PROTOHASH_LOOKUP_ELEM_64(arrivals, map, delay_hash, key1, notif_count, anew_val);
    uint32_t aind = 0;
    
    int qnew_val = 0;
    //uint32_t qind = JBPF_PROTOHASH_LOOKUP_ELEM_64(queues, map, queue_hash, pdcp_ctx.ue_index, pdcp_ctx.rb_id, qnew_val);
    uint32_t qind = 0;


    // Update stats
    int new_val = 0;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_south_hash, pdcp_ctx.rb_id, pdcp_ctx.ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].total_sdu = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_count = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_sdu = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_sdu = 0;
        out->stats[ind % MAX_NUM_UE_RB].total_win = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_win = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_win = 0;
        out->stats[ind % MAX_NUM_UE_RB].delay_count = 0;
        out->stats[ind % MAX_NUM_UE_RB].total_delay = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_delay = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_delay = 0;

        out->stats[ind % MAX_NUM_UE_RB].queue_count = 0;
        out->stats[ind % MAX_NUM_UE_RB].total_queue_B = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_queue_B = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_queue_B = 0;
        out->stats[ind % MAX_NUM_UE_RB].total_queue_pkt = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_queue_pkt = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_queue_pkt = 0;
    }


    out->stats[ind % MAX_NUM_UE_RB].sdu_count++; 

    out->stats[ind % MAX_NUM_UE_RB].total_sdu += sdu_length;
    if (out->stats[ind % MAX_NUM_UE_RB].min_sdu > sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].min_sdu = sdu_length;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].max_sdu < sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].max_sdu = sdu_length;
    }

    out->stats[ind % MAX_NUM_UE_RB].total_win += window_size;
    if (out->stats[ind % MAX_NUM_UE_RB].min_win > window_size) {
        out->stats[ind % MAX_NUM_UE_RB].min_win = window_size;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].max_win < window_size) {
        out->stats[ind % MAX_NUM_UE_RB].max_win = window_size;
    }


    // Calculate delay per SDU

    sdu_length = 0;
    if (!anew_val) {
        // It should always be found, but maybe the hash has been cleaned, then ignore
        uint64_t delay = jbpf_time_get_ns() - arrivals->map[aind % MAX_SDU_IN_FLIGHT].arrival_ns;
        sdu_length = arrivals->map[aind % MAX_SDU_IN_FLIGHT].sdu_length;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("PDCP DL DELIVER DELAY: ue_index=%d, sdu_length=%d, delay=%d\n", 
            pdcp_ctx.ue_index, sdu_length, delay);
#endif
    
        out->stats[ind % MAX_NUM_UE_RB].delay_count++; 

        out->stats[ind % MAX_NUM_UE_RB].total_delay += delay;
        if (out->stats[ind % MAX_NUM_UE_RB].min_delay > delay) {
            out->stats[ind % MAX_NUM_UE_RB].min_delay = delay;
        }
        if (out->stats[ind % MAX_NUM_UE_RB].max_delay < delay) {
            out->stats[ind % MAX_NUM_UE_RB].max_delay = delay;
        }
    
    }


    // Calculate queue size

    if (!qnew_val) {
        queues->map[qind % MAX_SDU_QUEUES].pkts --;
        queues->map[qind % MAX_SDU_QUEUES].bytes -= sdu_length;

        out->stats[ind % MAX_NUM_UE_RB].queue_count++; 

        uint32_t pkts = queues->map[qind % MAX_SDU_QUEUES].pkts;
        uint32_t bytes = queues->map[qind % MAX_SDU_QUEUES].bytes;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("PDCP DL DELIVER QUEUE: ue_index=%d, pkts=%d, bytes=%d\n", 
            pdcp_ctx.ue_index, pkts, bytes);
#endif

        out->stats[ind % MAX_NUM_UE_RB].total_queue_pkt += pkts;
        if (out->stats[ind % MAX_NUM_UE_RB].min_queue_pkt > pkts) {
            out->stats[ind % MAX_NUM_UE_RB].min_queue_pkt = pkts;
        }
        if (out->stats[ind % MAX_NUM_UE_RB].max_queue_pkt < pkts) {
            out->stats[ind % MAX_NUM_UE_RB].max_queue_pkt = pkts;
        }
        out->stats[ind % MAX_NUM_UE_RB].total_queue_B += bytes;
        if (out->stats[ind % MAX_NUM_UE_RB].min_queue_B > bytes) {
            out->stats[ind % MAX_NUM_UE_RB].min_queue_B = bytes;
        }
        if (out->stats[ind % MAX_NUM_UE_RB].max_queue_B < bytes) {
            out->stats[ind % MAX_NUM_UE_RB].max_queue_B = bytes;
        }

    }

    
    *not_empty_stats = 1;


    return JBPF_CODELET_SUCCESS;
}
