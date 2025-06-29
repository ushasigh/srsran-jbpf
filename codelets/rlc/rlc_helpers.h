// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_RLC_HELPERS_H
#define JRTC_RLC_HELPERS_H

#define MAX_NUM_UE_RB (256)


#define RLC_STATS_INIT(dest)   \
    do {                           \
        dest.count = 0;            \
        dest.total = 0;            \
        dest.min = UINT32_MAX;     \
        dest.max = 0;              \
    } while (0)

#define RLC_STATS_UPDATE(dest, src)   \
    do {                                  \
        dest.count++;                     \
        if (src < dest.min) {             \
            dest.min = src;               \
        }                                 \
        if (src > dest.max) {             \
            dest.max = src;               \
        }                                 \
        dest.total += src;                \
    } while (0)



#define RLC_TRAFFIC_STATS_INIT(dest)   \
    do {                           \
        dest.count = 0;            \
        dest.total = 0;            \
    } while (0)

#define RLC_TRAFFIC_STATS_UPDATE(dest, v)   \
    do {                           \
        dest.count++;            \
        dest.total += v;            \
    } while (0)



#define RLC_DL_STATS_INIT(dest, __du_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                       \
        dest.du_ue_index = __du_ue_index;                                      \
        dest.is_srb = __is_srb;                                                \
        dest.rb_id = __rb_id;                                                  \
        dest.rlc_mode = __rlc_mode;                                            \
        RLC_STATS_INIT(dest.sdu_queue_pkts);                                   \
        RLC_STATS_INIT(dest.sdu_queue_bytes);                                  \
        RLC_TRAFFIC_STATS_INIT(dest.sdu_new_bytes);                            \
        RLC_TRAFFIC_STATS_INIT(dest.pdu_tx_bytes);                             \
        RLC_STATS_INIT(dest.sdu_tx_started);                                   \
        RLC_STATS_INIT(dest.sdu_tx_completed);                                 \
        RLC_STATS_INIT(dest.sdu_tx_delivered);                                 \
        dest.has_am = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM);                  \
        if (dest.has_am) {                                                     \
            RLC_TRAFFIC_STATS_INIT(dest.am.pdu_retx_bytes);                    \
            RLC_TRAFFIC_STATS_INIT(dest.am.pdu_status_bytes);                  \
            RLC_STATS_INIT(dest.am.pdu_retx_count);                            \
            RLC_STATS_INIT(dest.am.pdu_window_pkts);                           \
            RLC_STATS_INIT(dest.am.pdu_window_bytes);                          \
        }                                                                      \
    } while (0)


#define RLC_UL_STATS_INIT(dest, __du_ue_index, __is_srb, __rb_id, __rlc_mode)  \
    do {                                                                       \
        dest.du_ue_index = __du_ue_index;                                      \
        dest.is_srb = __is_srb;                                                \
        dest.rb_id = __rb_id;                                                  \
        dest.rlc_mode = __rlc_mode;                                            \
        RLC_TRAFFIC_STATS_INIT(dest.pdu_bytes);                                \
        RLC_TRAFFIC_STATS_INIT(dest.sdu_delivered_bytes);                      \
        RLC_STATS_INIT(dest.sdu_delivered_latency);                            \
        dest.has_um = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_UM);                  \
        if (dest.has_um) {                                                     \
            RLC_STATS_INIT(dest.um.pdu_window_pkts);                           \
        }                                                                      \
        dest.has_am = (rlc_ctx.rlc_mode == JBPF_RLC_MODE_AM);                  \
        if (dest.has_um) {                                                     \
            RLC_STATS_INIT(dest.am.pdu_window_pkts);                           \
        }                                                                      \
    } while (0)



#endif // JRTC_RLC_HELPERS_H