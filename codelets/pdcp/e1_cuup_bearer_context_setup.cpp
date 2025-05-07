// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "pdcp_dl_pkts.h"

#include "../utils/misc_utils.h"
#include "../utils/hashmap_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)


struct jbpf_load_map_def SEC("maps") last_acked_map = {
    .type = JBPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(t_last_acked),
    .max_entries = 1,
};

DEFINE_PROTOHASH_64(last_acked_hash, MAX_NUM_UE_RB);




//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    
    const jbpf_e1_ctx_info& e1_ctx = *reinterpret_cast<const jbpf_e1_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&e1_ctx) + sizeof(jbpf_e1_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    t_last_acked *last_acked = (t_last_acked*)jbpf_map_lookup_elem(&last_acked_map, &zero_index);
    if (!last_acked) {
        return JBPF_CODELET_FAILURE;
    }

    //uint64_t timestamp = jbpf_time_get_ns();
    uint64_t ue_index = e1_ctx.ue_index; 
    uint64_t gnb_cu_cp_ue_e1ap_id = e1_ctx.gnb_cu_cp_ue_e1ap_id; 
    uint64_t gnb_cu_up_ue_e1ap_id = e1_ctx.gnb_cu_up_ue_e1ap_id; 
    uint32_t success = ctx->srs_meta_data1;

#ifdef DEBUG_PRINT
    jbpf_printf_debug("e1_cuup_bearer_context_setup: ue_index=%d, gnb_cu_cp_ue_e1ap_id=%d, gnb_cu_up_ue_e1ap_id=%d\n", 
        ue_index, gnb_cu_cp_ue_e1ap_id, gnb_cu_up_ue_e1ap_id);
    jbpf_printf_debug("                              success=%d\n", success);
#endif

    // TBD - pass from srsRAN
    uint32_t rb_id = 1;

    // When a bearer context is setup, we need to reset the last acked
    // At the beginning, 0 is not acked so set to "-1".
    int new_val = 0;
    uint32_t ack_ind = JBPF_PROTOHASH_LOOKUP_ELEM_64(last_acked, ack, last_acked_hash, rb_id, ue_index, new_val);
    last_acked->ack[ack_ind % MAX_NUM_UE_RB] = UINT32_MAX;


    return JBPF_CODELET_SUCCESS;
}