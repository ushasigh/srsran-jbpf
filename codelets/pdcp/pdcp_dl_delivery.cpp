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


struct jbpf_load_map_def SEC("maps") last_deliv_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(last_deliv_acked_hash, MAX_NUM_UE_RB);

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
struct jbpf_load_map_def SEC("maps") sdu_events = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_sdu_events),
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

    t_last_acked *last_deliv_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_deliv_acked_map, &zero_index);
    if (!last_deliv_acked) {
        return JBPF_CODELET_FAILURE;
    }

#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    t_sdu_events *events = (t_sdu_events *)jbpf_map_lookup_elem(&sdu_events, &zero_index);
    if (!events)
        return JBPF_CODELET_FAILURE;

    t_sdu_queues *queues = (t_sdu_queues *)jbpf_map_lookup_elem(&sdu_queues, &zero_index);
    if (!queues)
        return JBPF_CODELET_FAILURE;
#endif

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);    

    uint32_t window_size = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);
    uint32_t notif_count = (uint32_t) (ctx->srs_meta_data1 >> 32);

#ifdef DEBUG_PRINT
    // jbpf_printf_debug("PDCP DL DELIVER SDU: cu_ue_index=%d, window_size=%d, notif_count=%d\n", 
    //     pdcp_ctx.cu_ue_index, window_size, notif_count);
    jbpf_printf_debug("PDCP DL DELIVER SDU: cu_ue_index=%d, rb_id=%d, notif_count=%d\n", 
        pdcp_ctx.cu_ue_index, rb_id, notif_count);
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

// Still not fully debugged so allowing to be disabled
#ifdef PDCP_REPORT_DL_DELAY_QUEUE
    // Calculate delay per SDU
    uint32_t total_sdu_length = 0;
    uint32_t total_sdu_cnt = 0;

    // At the beginning, 0 is not acked so set to "-1".
    uint32_t ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_deliv_acked, ack, last_deliv_acked_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    if (new_val) {
        last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;
    }

    uint32_t delta = notif_count - last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB];   // modulo arithmetic

    if (delta > 500) {

        jbpf_printf_debug("PDCP DL DELIVER SDU: cu_ue_index=%d, rb_id=%d delta too big !!!  ", 
            pdcp_ctx.cu_ue_index, rb_id);
        jbpf_printf_debug("delta=%d notif_count=%d last_deliv_acked=%d \n", 
            delta, notif_count, last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB]);    
            
        // Reset the notification count
        last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB] = notif_count;
                    
        return JBPF_CODELET_FAILURE;
    }

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL DELIVER SDU:    ACKING: notif_count=%d, last_deliv_acked=%d, delta=%d\n", 
        notif_count, last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB], delta);
#endif

    uint32_t delay_hash_key = PDCP_DL_DELAY_HASH_KEY(rb_id, pdcp_ctx.cu_ue_index);

    for (uint32_t ncnt = 1; ncnt <= delta; ncnt++) {
        uint32_t notif = last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB] + ncnt;         // wraps if necessary
    
        if (notif % PDCP_QUEUE_SAMPLING_RATE != 0) {
            continue;
        }

        // Just find the key, don't add it. It was added in dl_new_sdu.
        // It should always be found, but maybe the hash has been cleaned, then ignore
        uint64_t compound_key = JBPF_PROTOHASH_COMPOUND_KEY_64(delay_hash_key, notif);
        uint32_t *pind = (uint32_t *)jbpf_map_lookup_elem(&delay_hash, &compound_key); 
        if (pind) {
            uint32_t aind = *pind;

            uint64_t now_ns = jbpf_time_get_ns();
            events->map[aind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns = now_ns;

            // only calculate rlc_deliv_delay if we have a valid rlcTxStarted_ns
            if ((events->map[aind % MAX_SDU_IN_FLIGHT].rlcTxStarted_ns > 0) &&
                (events->map[aind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns > events->map[aind % MAX_SDU_IN_FLIGHT].rlcTxStarted_ns)) {

                uint64_t delay = events->map[aind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns - events->map[aind % MAX_SDU_IN_FLIGHT].rlcTxStarted_ns;  
                
                out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.count++; 
                out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.total += delay;
                if (out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.min > delay) {
                    out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.min = delay;
                }
                if (out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.max < delay) {
                    out->stats[ind % MAX_NUM_UE_RB].rlc_deliv_delay.max = delay;
                }
            }

            // only calculate total_delay if we have a valid sdu arrival time
            if ((events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns > 0) &&
                (events->map[aind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns > events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns)) {

                uint64_t delay = events->map[aind % MAX_SDU_IN_FLIGHT].rlcDelivered_ns - events->map[aind % MAX_SDU_IN_FLIGHT].sdu_arrival_ns;  
                
                out->stats[ind % MAX_NUM_UE_RB].total_delay.count++; 
                out->stats[ind % MAX_NUM_UE_RB].total_delay.total += delay;
                if (out->stats[ind % MAX_NUM_UE_RB].total_delay.min > delay) {
                    out->stats[ind % MAX_NUM_UE_RB].total_delay.min = delay;
                }
                if (out->stats[ind % MAX_NUM_UE_RB].total_delay.max < delay) {
                    out->stats[ind % MAX_NUM_UE_RB].total_delay.max = delay;
                }
            }

            // get sdu length
            uint32_t sdu_length = events->map[aind % MAX_SDU_IN_FLIGHT].sdu_length;
            total_sdu_length += sdu_length;
            total_sdu_cnt ++;

            int res;
            // Remove the SDU from the arrival map
            // Repeat lookup in case of concurrent accesses
            for (uint8_t i = 0; i < 3; i++) {
                res = JBPF_PROTOHASH_REMOVE_ELEM_64(events, map, delay_hash, delay_hash_key, notif);
                if (res == JBPF_MAP_SUCCESS) {
                    break;
                }
            }
            
#ifdef DEBUG_PRINT
            jbpf_printf_debug("    DELIVER DELAY: notif=%d, sdu_length=%d, delay=%d\n", 
                notif, sdu_length, delay);
#endif
        
        } 
        else {
            // Just find the key, don't add it. 
            // It should always be found, but maybe the hash has been cleaned, then ignore
#ifdef DEBUG_PRINT
            jbpf_printf_debug("PDCP DL DELIVER KEY NOT FOUND: notif=%d, notif_count=%d, last_deliv_acked=%d\n", 
                notif, notif_count, last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB]);
#endif
        }    
    }

    // Reset the notification count
    last_deliv_acked->ack[ack_ind % MAX_NUM_UE_RB] = notif_count;


    // Calculate queue size

    // Just find the key, don't add it. It was added in dl_new_sdu.
    // It should always be found, but maybe the hash has been cleaned, then ignore
    uint64_t compound_key = JBPF_PROTOHASH_COMPOUND_KEY_64(pdcp_ctx.cu_ue_index, rb_id); 
    uint32_t *pind = (uint32_t *)jbpf_map_lookup_elem(&queue_hash, &compound_key); 

    if (pind) {
        uint32_t qind = *pind;

        // Make sure the queues are always positive as we have no way of flushing queues
        // if a UE detaches and another one gets the same cu_ue_index
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

        uint32_t pkts = queues->map[qind % MAX_SDU_QUEUES].pkts;
        uint32_t bytes = queues->map[qind % MAX_SDU_QUEUES].bytes;

#ifdef DEBUG_PRINT
        jbpf_printf_debug("    DELIVER QUEUE: cu_ue_index=%d, pkts=%d, bytes=%d\n", 
            pdcp_ctx.cu_ue_index, pkts, bytes);
#endif

        out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.count++;
        out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.total += pkts;
        if (out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.min > pkts) {
            out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.min = pkts;
        }
        if (out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.max < pkts) {
            out->stats[ind % MAX_NUM_UE_RB].tx_queue_pkt.max = pkts;
        }

        out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.count++;
        out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.total += bytes;
        if (out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.min > bytes) {
            out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.min = bytes;
        }
        if (out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.max < bytes) {
            out->stats[ind % MAX_NUM_UE_RB].tx_queue_bytes.max = bytes;
        }
    }
#endif
    
    *not_empty_stats = 1;


    return JBPF_CODELET_SUCCESS;
}
