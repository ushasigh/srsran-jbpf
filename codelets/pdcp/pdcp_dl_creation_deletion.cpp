// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "pdcp_helpers.h"
#include "pdcp_dl_pkts.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)


struct jbpf_load_map_def SEC("maps") last_notif_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

struct jbpf_load_map_def SEC("maps") last_deliv_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(last_notif_acked_hash, MAX_NUM_UE_RB);
DEFINE_PROTOHASH_64(last_deliv_acked_hash, MAX_NUM_UE_RB);




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

    t_last_acked *last_notif_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_notif_acked_map, &zero_index);
    if (!last_notif_acked) {
        return JBPF_CODELET_FAILURE;
    }

    t_last_acked *last_deliv_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_deliv_acked_map, &zero_index);
    if (!last_deliv_acked) {
        return JBPF_CODELET_FAILURE;
    }

    // create explicit rbid
    int rb_id = RBID_2_EXPLICIT(pdcp_ctx.is_srb, pdcp_ctx.rb_id);    

#ifdef DEBUG_PRINT
    jbpf_printf_debug("pdcp_creation_deletion: cu_ue_index=%d, rb_id=%d\n", 
        ue_index, rb_id);
#endif

    // When a bearer context is setup, we need to reset the last acked
    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
    uint32_t ack_ind = 0;
    
    ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_notif_acked, ack, last_notif_acked_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    last_notif_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;

    ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_deliv_acked, ack, last_deliv_acked_hash, rb_id, pdcp_ctx.cu_ue_index, new_val);
    last_notif_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;

    return JBPF_CODELET_SUCCESS;
}