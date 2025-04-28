// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

#ifndef JRTC_APP_PDCP_SDUS
#define JRTC_APP_PDCP_SDUS

#define MAX_SDU_IN_FLIGHT (65536 * 1024)
#define MAX_SDU_QUEUES (256)

typedef struct {
    uint16_t ue_index;
    uint16_t rb_id;
    uint32_t count;
    uint64_t arrival_ns;
    uint32_t sdu_length;
} t_arrival;

typedef struct {
    t_arrival map[MAX_SDU_IN_FLIGHT];
    uint32_t map_count;
} t_sdu_arrivals;


typedef struct {
    uint16_t ue_index;
    uint16_t rb_id;
    uint32_t pkts;
    uint32_t bytes;
} t_queue;


typedef struct {
    t_queue map[MAX_SDU_QUEUES];
    uint32_t map_count;
} t_sdu_queues;



#endif