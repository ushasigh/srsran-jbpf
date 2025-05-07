// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"


#include "../utils/misc_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)




//#define DEBUG_PRINT

extern "C" SEC("jbpf_srsran_generic")
uint64_t jbpf_main(void* state)
{
    struct jbpf_ran_generic_ctx *ctx = (jbpf_ran_generic_ctx *)state;
    
    const jbpf_e1_ctx_info& e1_ctx = *reinterpret_cast<const jbpf_e1_ctx_info*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&e1_ctx) + sizeof(jbpf_e1_ctx_info) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    //uint64_t timestamp = jbpf_time_get_ns();
    uint64_t ue_index = e1_ctx.ue_index; 
    uint64_t gnb_cu_cp_ue_e1ap_id = e1_ctx.gnb_cu_cp_ue_e1ap_id; 
    uint64_t gnb_cu_up_ue_e1ap_id = e1_ctx.gnb_cu_up_ue_e1ap_id; 
    uint32_t success = ctx->srs_meta_data1;

    jbpf_printf_debug("e1_cuup_bearer_context_modification: ue_index=%d, gnb_cu_cp_ue_e1ap_id=%d, gnb_cu_up_ue_e1ap_id=%d\n", 
        ue_index, gnb_cu_cp_ue_e1ap_id, gnb_cu_up_ue_e1ap_id);
    jbpf_printf_debug("                                     success=%d\n", success);


    return JBPF_CODELET_SUCCESS;
}