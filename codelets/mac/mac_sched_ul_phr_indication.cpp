// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#include <linux/bpf.h>

#include "jbpf_srsran_contexts.h"
#include "srsran/scheduler/scheduler_feedback_handler.h"
#include "srsran/mac/phr_report.h"

#include "mac_sched_ul_phr_indication.pb.h"

#include "../utils/misc_utils.h"


#define SEC(NAME) __attribute__((section(NAME), used))

#include "jbpf_defs.h"
#include "jbpf_helper.h"

#define MAX_NUM_UE (32)

jbpf_ringbuf_map(mac_sched_ul_phr_indication_output_map, mac_sched_ul_phr_indication, 256);

struct jbpf_load_map_def SEC("maps") output_map_tmp = {
  .type = JBPF_MAP_TYPE_ARRAY,
  .key_size = sizeof(int),
  .value_size = sizeof(mac_sched_ul_phr_indication),
  .max_entries = 1,
};


//#define DEBUG_PRINT

extern "C" SEC("jbpf_ran_mac_sched")
uint64_t jbpf_main(void* state)
{
    int zero_index=0;
    struct jbpf_mac_sched_ctx *ctx = (jbpf_mac_sched_ctx *)state;
    
    const srsran::ul_phr_indication_message& mac_ctx = *reinterpret_cast<const srsran::ul_phr_indication_message*>(ctx->data);

    // Ensure the object is within valid bounds
    if (reinterpret_cast<const uint8_t*>(&mac_ctx) + sizeof(srsran::ul_phr_indication_message) > reinterpret_cast<const uint8_t*>(ctx->data_end)) {
        return JBPF_CODELET_FAILURE;  // Out-of-bounds access
    }

    mac_sched_ul_phr_indication *out = (mac_sched_ul_phr_indication *)jbpf_map_lookup_elem(&output_map_tmp, &zero_index);
    if (!out)
        return JBPF_CODELET_FAILURE;

    out->timestamp = jbpf_time_get_ns();
    out->ue_index = mac_ctx.ue_index;
    out->rnti = (uint32_t) mac_ctx.rnti;

    // NOTE: here I cannot use this call:
    // struct srsran::cell_ph_report rep = static_cast<srsran::cell_ph_report>(mac_ctx.phr.get_se_phr());
    // This seems to be because get_se_phr() calls standard method back() which doesn't seem to verify. 

    auto ph_reports = mac_ctx.phr.get_phr();
    for (int i=0; i<srsran::MAX_NOF_DU_CELLS; i++) {
        if (i < ph_reports.size()) {
            out->ph_reports[i].serv_cell_id = ph_reports[i].serv_cell_id;
            out->ph_reports[i].ph_min = ph_reports[i].ph.start();
            out->ph_reports[i].ph_max = ph_reports[i].ph.stop();
            if (ph_reports[i].p_cmax.has_value()) {
                out->ph_reports[i].p_cmax_min = ph_reports[i].p_cmax.value().start();
                out->ph_reports[i].p_cmax_max = ph_reports[i].p_cmax.value().stop();
            }
        } else {
            out->ph_reports_count = i;
            break;
        }
    }

    int ret = jbpf_ringbuf_output(&mac_sched_ul_phr_indication_output_map, (void *)out, sizeof(mac_sched_ul_phr_indication));
    jbpf_map_clear(&output_map_tmp);
    if (ret < 0) {
#ifdef DEBUG_PRINT
        jbpf_printf_debug("mac_sched_ul_phr_indication: Failure: jbpf_ringbuf_output\n");
#endif
        return JBPF_CODELET_FAILURE;
    }

    return JBPF_CODELET_SUCCESS;
}
