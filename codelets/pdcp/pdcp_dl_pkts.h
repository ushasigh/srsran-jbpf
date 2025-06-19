// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_APP_PDCP_SDUS
#define JRTC_APP_PDCP_SDUS


#define PDCP_REPORT_DL
#define PDCP_REPORT_UL
#define PDCP_REPORT_DL_DELAY_QUEUE

#define PDCP_QUEUE_SAMPLING_RATE (5)   /* i.e. 1 in 5 packets will be processed */

#define PDCP_DL_DELAY_HASH_KEY(__rbid, __cu_ue_index) \
  (uint32_t) (((uint64_t)(__rbid & 0xFFFF) << 15) << 1 | ((uint64_t)(__cu_ue_index & 0xFFFF)))


#define MAX_NUM_UE_RB (256)
//#define MAX_SDU_IN_FLIGHT (256 * 32 * 4)
#define MAX_SDU_IN_FLIGHT (256 * 32 * 1)
#define MAX_SDU_QUEUES (256)

#define PDCP_DELAY_MAX (1000000) /* 1 second in nanoseconds */
#define PDCP_MAX_LARGE_SDUS (16) /* 1 second in nanoseconds */


typedef struct {
    uint64_t sdu_arrival_ns;
    uint64_t pdcpTx_ns;
    uint64_t rlcTxStarted_ns;
    uint64_t rlcDelivered_ns;
    uint32_t sdu_length;

    uint32_t count; 
    uint32_t large_sdu_delay_idx;  // temp field to provide debug info for large delay SDUs
} t_sdu_evs;

typedef struct {
    t_sdu_evs map[MAX_SDU_IN_FLIGHT];
    uint32_t map_count;
} t_sdu_events;


typedef struct {
    uint32_t pkts;
    uint32_t bytes;
} t_queue;


typedef struct {
    t_queue map[MAX_SDU_QUEUES];
    uint32_t map_count;
} t_sdu_queues;

typedef struct {
    uint32_t ack[MAX_SDU_IN_FLIGHT];
    uint32_t ack_count;
} t_last_acked;


#endif