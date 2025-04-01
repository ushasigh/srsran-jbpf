// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"

#include "pdcp_dl_delivery.pb.h"

#include "../utils/misc_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)

jbpf_ringbuf_map(pdcp_dl_delivery_output_map, pdcp_dl_delivery, 256);

struct jbpf_load_map_def SEC("maps") output_map_tmp = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(pdcp_dl_delivery),
  .max_entries = 1,
};


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

    pdcp_dl_delivery *out = (pdcp_dl_delivery *)jbpf_map_lookup_elem(&output_map_tmp, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    out->timestamp = jbpf_time_get_ns();
    out->ue_index = pdcp_ctx.ue_index;
    out->is_srb = pdcp_ctx.is_srb;
    out->rb_id = pdcp_ctx.rb_id;
    out->rlc_mode = pdcp_ctx.rlc_mode;
    /*
    out->notif_count = ctx->meta_data1 >> 32;
    out->window_size = ctx->meta_data1 & 0xFFFFFFFF;
    */
    out->notif_count = 0;
    out->window_size = 0;

    int ret = jbpf_ringbuf_output(&pdcp_dl_delivery_output_map, (void *)out, sizeof(pdcp_dl_delivery));
    jbpf_map_clear(&output_map_tmp);
    if (ret < 0) {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("pdcp_dl_delivery: Failure: jbpf_ringbuf_output\n");
#endif
        return JBPF_CODELET_FAILURE;
    }

    return JBPF_CODELET_SUCCESS;
}
