// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_dl_pkts.h"
#include "pdcp_dl_north_stats.pb.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE_RB (256)


struct jbpf_load_map_def SEC("maps") dl_north_not_empty = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(uint32_t),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") stats_map_dl_north = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(dl_north_stats),
    .max_entries = 1,
};
  
DEFINE_PROTOHASH_64(dl_north_hash, MAX_NUM_UE_RB);



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
    
    const jbpf_pdcp_ctx_info& pdcp_ctx = *reinterpret_cast<const jbpf_pdcp_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&pdcp_ctx) + sizeof(jbpf_pdcp_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    t_sdu_arrivals *arrivals = (t_sdu_arrivals *)jbpf_map_lookup_elem(&sdu_arrivals, &zero_index);
    if (!arrivals)
        return JBPF_CODELET_FAILURE;

    t_sdu_queues *queues = (t_sdu_queues *)jbpf_map_lookup_elem(&sdu_queues, &zero_index);
    if (!queues)
        return JBPF_CODELET_FAILURE;


    uint32_t *not_empty_stats = (uint32_t*)jbpf_map_lookup_elem(&dl_north_not_empty, &zero_index);
    if (!not_empty_stats) {
        return JBPF_CODELET_FAILURE;
    }

    dl_north_stats *out = (dl_north_stats *)jbpf_map_lookup_elem(&stats_map_dl_north, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;



    // out->timestamp = jbpf_time_get_ns();
    // out->ue_index = pdcp_ctx.ue_index;
    // out->is_srb = pdcp_ctx.is_srb;
    // out->rb_id = pdcp_ctx.rb_id;
    // out->rlc_mode = pdcp_ctx.rlc_mode;
    // out->sdu_length = ctx->srs_meta_data1 >> 32;
    // out->count = ctx->srs_meta_data1 & 0xFFFFFFFF;


    // Store SDU arrival time so we can calculate delay and queue size at the PDCP level
    uint32_t sdu_length = (uint32_t) (ctx->srs_meta_data1 >> 32);
    uint32_t count = (uint32_t) (ctx->srs_meta_data1 & 0xFFFFFFFF);

#ifdef DEBUG_PRINT
    jbpf_printf_debug("PDCP DL NEW SDU: ue_index=%d, rb_id=%d, count=%d\n", 
        pdcp_ctx.ue_index, pdcp_ctx.rb_id, count);
#endif

    int new_val = 0;


    uint32_t ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(out, stats, dl_north_hash, pdcp_ctx.ue_index, pdcp_ctx.rb_id, new_val);
    if (new_val) {
        out->stats[ind % MAX_NUM_UE_RB].total_sdu = 0;
        out->stats[ind % MAX_NUM_UE_RB].sdu_count = 0;
        out->stats[ind % MAX_NUM_UE_RB].min_sdu = UINT32_MAX;
        out->stats[ind % MAX_NUM_UE_RB].max_sdu = 0;
    }

    *not_empty_stats = 1;

    out->stats[ind % MAX_NUM_UE_RB].sdu_count++; 

    out->stats[ind % MAX_NUM_UE_RB].total_sdu += sdu_length;
    if (out->stats[ind % MAX_NUM_UE_RB].min_sdu > sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].min_sdu = sdu_length;
    }
    if (out->stats[ind % MAX_NUM_UE_RB].max_sdu < sdu_length) {
        out->stats[ind % MAX_NUM_UE_RB].max_sdu = sdu_length;
    }

#ifdef DEBUG_PRINT
    jbpf_printf_debug("                 sdu_length=%d, min_sdu=%d, max_sdu=%d\n", 
        sdu_length, 
        out->stats[ind % MAX_NUM_UE_RB].min_sdu,
        out->stats[ind % MAX_NUM_UE_RB].max_sdu);
#endif
    


    // NOTE: There are two potential issues here:
    // - We don't empty the hash once a packet is served. 
    //   We relay on it being cleared once a sec, when reported.
    //   This means that we can have a hash overflow and miss some packets
    // - To prevent overflow, the hash size may have to be large
    //   This can cause large overhead at JBPF codelet level, affecting RAN
    //   We haven't measured this yet.  

    uint32_t key1 = 
        ((uint64_t)(pdcp_ctx.rb_id & 0xFFFF) << 15) << 1 | 
        ((uint64_t)(pdcp_ctx.ue_index & 0xFFFF));
    //ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(arrivals, map, delay_hash, key1, count, new_val);
    ind = 0;
    if (new_val) {
        // It should always be a new value, but maybe the hash is full, then ignore
        arrivals->map[ind % MAX_SDU_IN_FLIGHT].arrival_ns = jbpf_time_get_ns();
        arrivals->map[ind % MAX_SDU_IN_FLIGHT].sdu_length = sdu_length;
    }


    //ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(queues, map, queue_hash, pdcp_ctx.ue_index, pdcp_ctx.rb_id, new_val);
    ind = 0;
    if (new_val) {
        queues->map[ind % MAX_SDU_QUEUES].pkts = 0;
        queues->map[ind % MAX_SDU_QUEUES].bytes = 0;
    }
    queues->map[ind % MAX_SDU_QUEUES].pkts ++;
    queues->map[ind % MAX_SDU_QUEUES].bytes += sdu_length;


    return JBPF_CODELET_SUCCESS;
}
