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


struct jbpf_load_map_def SEC("maps") last_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(last_acked_hash, MAX_NUM_UE_RB);

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
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

DEFINE_PROTOHASH_64(delay_hash, MAX_SDU_IN_FLIGHT);
DEFINE_PROTOHASH_64(queue_hash, MAX_SDU_QUEUES);
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

    t_last_acked *last_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_acked_map, &zero_index);
    if (!last_acked) {
        return JBPF_CODELET_FAILURE;
    }

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    t_sdu_arrivals *arrivals = (t_sdu_arrivals *)jbpf_map_lookup_elem(&sdu_arrivals, &zero_index);
    if (!arrivals)
        return JBPF_CODELET_FAILURE;

    t_sdu_queues *queues = (t_sdu_queues *)jbpf_map_lookup_elem(&sdu_queues, &zero_index);
    if (!queues)
        return JBPF_CODELET_FAILURE;
#endif


    // out->timestamp = jbpf_time_get_ns();
    // out->ue_index = pdcp_ctx.ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->notif_count = ctx->srs_meta_data1 >> 32;
    // out->window_size = ctx->srs_meta_data1 & 0xFFFFFFFF;


    uint32_t window_size = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t notif_count = (uint32_t) (ctx->srs_meta_data1 >> 32);

#ifdef DEBUG_PRINT
    // jbpf_printf_debug("PDCP DL DELIVER SDU: ue_index=%d, window_size=%d, notif_count=%d\n", 
    //     pdcp_ctx.ue_index, window_size, notif_count);
    jbpf_printf_debug("PDCP DL DELIVER SDU: ue_index=%d, rb_id=%d, notif_count=%d\n", 
        pdcp_ctx.ue_index, pdcp_ctx.rb_id, notif_count);
#endif

    


    // Update stats
    int new_val = 0;
    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_south_hash, pdcp_ctx.rb_id, pdcp_ctx.ue_index, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].sdu_count = 0;
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

    out->stats[ind % MAX_NUM_UE_RB].total_win += window_size;
    if (out->stats[ind % MAX_NUM_UE_RB].min_win > window_size) {
        out->stats[ind % MAX_NUM_UE_RB].min_win = window_size;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].max_win < window_size) {
        out->stats[ind % MAX_NUM_UE_RB].max_win = window_size;
    }


// Still not fully debugged so allowing to be disabled
#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    // Calculate delay per SDU
    uint32_t total_sdu_length = 0;
    uint32_t total_sdu_cnt = 0;

    uint32_t delay_key = 
        ((uint64_t)(pdcp_ctx.rb_id & 0xFFFF) << 15) << 1 | 
        ((uint64_t)(pdcp_ctx.ue_index & 0xFFFF));


    // At the beginning, 0 is not acked so set to "-1".
    uint32_t ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_acked, ack, last_acked_hash, pdcp_ctx.rb_id, pdcp_ctx.ue_index, new_val);
    if (new_val) {
        last_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;
    }

    uint32_t delta = notif_count - last_acked->ack[ack_ind % MAX_NUM_UE_RB];   // modulo arithmetic
    #ifdef DEBUG_PRINT
            jbpf_printf_debug("    ACKING: notif_count=%d, last_acked=%d, delta=%d\n", 
                notif_count, last_acked->ack[ack_ind % MAX_NUM_UE_RB], delta);
    #endif
    for (uint32_t ncnt = 1; ncnt <= delta; ncnt++) {
        uint32_t notif = last_acked->ack[ack_ind % MAX_NUM_UE_RB] + ncnt;         // wraps if necessary

        // Just find the key, don't add it. It was added in dl_new_sdu.
        // It should always be found, but maybe the hash has been cleaned, then ignore
        uint64_t compound_key = ((uint64_t)notif << 31) << 1 | (uint64_t)delay_key; 
        uint32_t *pind = (uint32_t *)jbpf_map_lookup_elem(&delay_hash, &compound_key); 
        if (pind) {
            uint32_t aind = *pind;

            uint64_t delay = jbpf_time_get_ns() - arrivals->map[aind % MAX_SDU_IN_FLIGHT].arrival_ns;
            uint32_t sdu_length = arrivals->map[aind % MAX_SDU_IN_FLIGHT].sdu_length;
            total_sdu_length += sdu_length;
            total_sdu_cnt ++;

            int res;
            // Remove the SDU from the arrival map
            // Repeat lookup in case of concurrent accesses
            for (uint8_t i = 0; i < 3; i++) {
                res = JBPF_PROTOHASH_REMOVE_ELEM_64(arrivals, map, delay_hash, delay_key, notif);
                if (res == JBPF_MAP_SUCCESS) {
                    break;
                }
            }
            
    #ifdef DEBUG_PRINT
            jbpf_printf_debug("    DELIVER DELAY: notif=%d, sdu_length=%d, delay=%d\n", 
                notif, sdu_length, delay);
    #endif
        
            out->stats[ind % MAX_NUM_UE_RB].delay_count++; 
    
            out->stats[ind % MAX_NUM_UE_RB].total_delay += delay;
            if (out->stats[ind % MAX_NUM_UE_RB].min_delay > delay) {
                out->stats[ind % MAX_NUM_UE_RB].min_delay = delay;
            }
            if (out->stats[ind % MAX_NUM_UE_RB].max_delay < delay) {
                out->stats[ind % MAX_NUM_UE_RB].max_delay = delay;
            }
    
        } else {
            // Just find the key, don't add it. 
            // It should always be found, but maybe the hash has been cleaned, then ignore
//#ifdef DEBUG_PRINT
            jbpf_printf_debug("PDCP DL DELIVER KEY NOT FOUND: notif=%d, notif_count=%d, last_acked=%d\n", 
                notif, notif_count, last_acked->ack[ack_ind % MAX_NUM_UE_RB]);
//#endif
        }    
    }

    // Reset the notification count
    last_acked->ack[ack_ind % MAX_NUM_UE_RB] = notif_count;


    // Calculate queue size

    // Just find the key, don't add it. It was added in dl_new_sdu.
    // It should always be found, but maybe the hash has been cleaned, then ignore
    uint64_t compound_key = ((uint64_t)pdcp_ctx.rb_id << 31) << 1 | (uint64_t)pdcp_ctx.ue_index; 
    uint32_t *pind = (uint32_t *)jbpf_map_lookup_elem(&queue_hash, &compound_key); 

    if (pind) {
        uint32_t qind = *pind;

        // Make sure the queues are always positive as we have no way of flushing queues
        // if a UE detaches and another one gets the same ue_index
        if (queues->map[qind % MAX_SDU_QUEUES].pkts > total_sdu_cnt) {
            queues->map[qind % MAX_SDU_QUEUES].pkts -= total_sdu_cnt;
        } else {
            queues->map[qind % MAX_SDU_QUEUES].pkts = 0;
        }
        if (queues->map[qind % MAX_SDU_QUEUES].bytes > total_sdu_length) {
            queues->map[qind % MAX_SDU_QUEUES].bytes -= total_sdu_length;
        } else {
            queues->map[qind % MAX_SDU_QUEUES].bytes = 0;
        }

        out->stats[ind % MAX_NUM_UE_RB].queue_count++; 

        uint32_t pkts = queues->map[qind % MAX_SDU_QUEUES].pkts;
        uint32_t bytes = queues->map[qind % MAX_SDU_QUEUES].bytes;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("    DELIVER QUEUE: ue_index=%d, pkts=%d, bytes=%d\n", 
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
#endif
    
    *not_empty_stats = 1;


    return JBPF_CODELET_SUCCESS;
}
