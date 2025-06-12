- [1. Introduction](#1-introduction)
- [2. XRAN](#2-xran)
- [3. FAPI](#3-fapi)
  - [3.1. PHY-MAC hooks](#31-phy-mac-hooks)
  - [3.2. MAC-PHY](#32-mac-phy)
- [4. DU UE context creation/deletion](#4-du-ue-context-creationdeletion)
- [5. MAC scheduler](#5-mac-scheduler)
  - [5.1. MAC scheduler context creation/deletion](#51-mac-scheduler-context-creationdeletion)
  - [5.2. MAC scheduler input data](#52-mac-scheduler-input-data)
- [6. PDCP](#6-pdcp)
  - [6.1. PDCP downlink](#61-pdcp-downlink)
  - [6.2. PDCP uplink](#62-pdcp-uplink)
- [7. E1AP procedures](#7-e1ap-procedures)
  - [7.1. E1AP CUCP hooks](#71-e1ap-cucp-hooks)
  - [7.2. E1AP CUUP hooks](#72-e1ap-cuup-hooks)
- [8. CUCP UE Context Management](#8-cucp-ue-context-management)
- [9. NGAP](#9-ngap)
- [10. RRC](#10-rrc)
- [11. RLC](#11-rlc)
  - [11.1. RLC downlink](#111-rlc-downlink)
  - [11.2. RLC uplink](#112-rlc-uplink)


# 1. Introduction

Numerous Jbpf hooks have been added to the srsRAN codebase.

When a codelet is called, all parameters are passed in a "context" parameter.
The following sections describe the hooks, along with the "context" details.
The hook names are listed in bullets in the sections below.

# 2. XRAN

- capture_xran_packet

Context info:  
```c
    data: pointer to start of the XRAN packet
    data_end: pointer to end of the XRAN packet
    direction: 0-tx, 1=rx
```

# 3. FAPI

Context info:  
```c
    cell_id: Cell identifier
    data: pointer to start of the FAPI message
    data_end: pointer to end of the FAPI message
```

## 3.1. PHY-MAC hooks

- __fapi_rx_data_indication__
    
  Context "data" field points to a fapi::rx_data_indication_message structure.
  
- __fapi_crc_indication__
       
  Context "data" field points to a fapi::crc_indication_message structure.

- __fapi_uci_indication__

  Context "data" field points to a fapi::uci_indication_message structure.

- __fapi_srs_indication__
  
  Context "data" field points to a fapi::srs_indication_message structure.

- __fapi_rach_indication__
 
  Context "data" field points to a fapi::rach_indication_message structure.


## 3.2. MAC-PHY
 
- __fapi_dl_tti_request__
  
  Context "data" field points to a fapi::dl_tti_request_message structure.
  
- __fapi_ul_tti_request__
  
  Context "data" field points to a fapi::ul_tti_request_message structure.

- __fapi_ul_dci_request__
  
  Context "data" field points to a fapi::ul_dci_request_message structure.
  
- __fapi_tx_data_request__
  
  Context "data" field points to a fapi::tx_data_request_message structure.


# 4. DU UE context creation/deletion

These hooks have information passed in using a __jbpf_du_ue_ctx_info__ as shown below ..
```c
    struct jbpf_du_ue_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint32_t du_ue_index;
        uint32_t tac;
        uint32_t plmn;
        uint64_t nci;
        uint16_t pci;
        uint16_t crnti;
    };
```

Context info:  
```
    data: pointer to the jbpf_du_ue_ctx_info
    data_end: pointer to end of the jbpf_du_ue_ctx_info
```

- __du_ue_ctx_creation__
  
- __du_ue_ctx_update_crnti__
  
- __du_ue_ctx_deletion__
  

# 5. MAC scheduler

## 5.1. MAC scheduler context creation/deletion

These hooks are called when a scheduler context is created/updated/deleted.

Context info:  
```
    du_ue_index: The index used in the DU entity to identify the UE
```

- __mac_sched_ue_creation__
  
- __mac_sched_ue_reconfig__
  
- __mac_sched_ue_deletion__
  
- __mac_sched_ue_config_applied__
  

## 5.2. MAC scheduler input data

These hooks are called when a scheduler receives information e.g. Buffer-Status-Reports, Power-Headroom-Reports etc.

Context info:  
```
    du_ue_index: The index used in the DU entity to identify the UE
    data: pointer to start of the scheduler input message
    data_end: pointer to end of the scheduler input message

```

- __mac_sched_ul_bsr_indication__
  
    Context "data" field points to an srsran::ul_bsr_indication_message structure.

- __mac_sched_crc_indication__
  
    Context "data" field points to an srsran::ul_crc_pdu_indication structure.
  
- __mac_sched_uci_indication__
  
    Context "data" field points to an srsran::uci_indication::uci_pdu structure.
  
- __mac_sched_dl_mac_ce_indication__
  
    Context "data" field points to an srsran::dl_mac_ce_indication structure.
  
- __mac_sched_ul_phr_indication__
  
    Context "data" field points to an srsran::ul_phr_indication_message structure.
  
- __mac_sched_dl_buffer_state_indication__
  
    Context "data" field points to an srsran::dl_buffer_state_indication_message structure.
  
- __mac_sched_srs_indication__
  
    Context "data" field points to an srsran::srs_indication::srs_indication_pdu structure.

# 6. PDCP

These hooks have information passed in using a __jbpf_pdcp_ctx_info__ as shown below ..
```c
    struct jbpf_pdcp_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint32_t cu_ue_index;   /* if is_srb=True is cu_cp_ue_index, if is_srb=False is cu_up_ue_index */
        uint8_t is_srb; /* true=srb, false=drb */
        uint8_t rb_id;   /* if is_srb=True:    0=srb0, 1=srb1, 2=srb2,
                            if is_srb=False:   1=drb1, 2=drb2, 3-drb3 ... */
        uint8_t rlc_mode;  /* 0=UM, 1=AM*/
    };
```

## 6.1. PDCP downlink

- __pdcp_dl_creation__
     
    Called when a downlink PDCP bearer is created.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

- __pdcp_dl_deletion__
      
    Called when a downlink PDCP bearer is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

- __pdcp_dl_new_sdu__
     
    Called when a new SDU is received from higher layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1:  sdu_length << 32 | count
        srs_meta_data2 = window_size
    ```

-__pdcp_dl_tx_data_pdu__
     
    Called when a PDCP data PDU is sent to RLC.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = pdu_length << 32 | count;
        srs_meta_data2 = is_retx << 32 | window_size
    ```

- __pdcp_dl_tx_control_pdu__
  
    Called when a PDCP control PDU is sent to RLC.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = pdu_length << 32 | window_size
    ```

- __pdcp_dl_handle_tx_notification__
  
    This is a notification when first byte of a PDCP SDU is transmitted by RLC.
   
    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = notif_count << 32 | window_size
    ```

    Note that the notif_count means "up to and including" that count. i.e. in the following example

            pdcp_dl_handle_tx_notification notif_count=0

            pdcp_dl_handle_tx_notification notif_count=1

            pdcp_dl_handle_tx_notification notif_count=5

    the last message means that counts 2-5 are all being notified.

- __pdcp_dl_handle_delivery_notification__
  
    In RLC TM/UM mode, this is a notificaion when all bytes of a PDCP SDU have been sent to lower layers.
    
    In RLC AM mode, this is a notificaion when all bytes of a PDCP SDU have been sent to lower layers, and acknowledged by the UE.
    
    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = notif_count << 32 | window_size
    ```

    Note that the notif_count means "up to and including" that count. i.e. in the following example

           pdcp_dl_handle_delivery_notification notif_count=0

           pdcp_dl_handle_delivery_notification notif_count=1

           pdcp_dl_handle_delivery_notification notif_count=5

    the last message means that counts 2-5 are all being notified.

- __pdcp_dl_discard_pdu__

    Called when an SDU is discarded by the PDCP layer

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1 = count << 32 | window_size
    ```

- __pdcp_dl_reestablish__

    Called when a PDCP DL bearer is restablished.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

## 6.2. PDCP uplink

- __pdcp_ul_creation__
     
    Called when a uplink PDCP bearer is created.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

- __pdcp_dl_deletion__
      
    Called when a uplink PDCP bearer is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

- __pdcp_ul_rx_data_pdu__
      
    Called when a uplink PDCP data PDU is received from lower layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: pdu_length << 32 | header_length
        srs_meta_data2: count << 32 | window_size
    ```

- __pdcp_ul_rx_control_pdu__
      
    Called when a uplink PDCP control PDU is received from lower layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: pdu_length << 32 | window_size
    ```

- __pdcp_ul_deliver_sdu__
      
    Called when PDCP delivers an SDU to higher layers.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
        srs_meta_data1: sdu_length << 32 | window_size
    ```

- __pdcp_ul_reestablish__

    Called when a PDCP DL bearer is restablished.

    Context info:  
    ```
        data: pointer to the jbpf_pdcp_ctx_info
        data_end: pointer to end of the jbpf_pdcp_ctx_info
    ```

# 7. E1AP procedures

## 7.1. E1AP CUCP hooks

These hooks have information passed in using a __jbpf_cucp_e1_ctx_info__ as shown below ..
```c
    struct jbpf_cucp_e1_ctx_info {
        uint16_t ctx_id;   /* Context id (could be implementation specific) */
        uint64_t cu_cp_ue_index; 
        uint64_t gnb_cu_cp_ue_e1ap_id; 
        uint64_t gnb_cu_up_ue_e1ap_id; 
    };
```

All of the CUCP hooks have this context.

    Context info:  
    ```
        data: pointer to the jbpf_cucp_e1_ctx_info
        data_end: pointer to end of the jbpf_cucp_e1_ctx_info
    ```

- __e1_cucp_bearer_context_setup__
     
    Called when CUCP sends a setup request to CUUP.

- __e1_cucp_bearer_context_modification__
     
    Called when CUCP sends a modification request to CUUP.

- __e1_cucp_bearer_context_delete__
     
    Called when CUCP sends a delete request to CUUP.

- __e1_cucp_bearer_context_release__
     
    Called when CUCP determines that a bearer is inactive.

## 7.2. E1AP CUUP hooks

These hooks have information passed in using a __jbpf_cuup_e1_ctx_info__ as shown below ..
```c
struct jbpf_cuup_e1_ctx_info {
    uint16_t ctx_id;   /* Context id (could be implementation specific) */
    uint64_t cu_up_ue_index; 
    uint64_t gnb_cu_cp_ue_e1ap_id; 
    uint64_t gnb_cu_up_ue_e1ap_id; 
};
```

All of the CUUP hooks have this context.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = success/fail
    ```

- __e1_cuup_bearer_context_setup__
     
    Called when CUUP processes a setup request from the CUCP.

- __e1_cuup_bearer_context_modification__
     
    Called when CUUP processes a modification request from the CUCP.

- __e1_cuup_bearer_context_release__
     
    Called when CUUP processes a release request from the CUCP.


# 8. CUCP UE Context Management

These hooks are called when UE contexts are created/upated/deleted in the CUCP.

These hooks have information passed in using a __jbpf_cucp_uemgr_ctx_info__ as shown below ..
```c
struct jbpf_cucp_uemgr_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint16_t du_index;  
    uint32_t plmn;      /* (mcc << 16) || mnc */ 
    uint64_t cu_cp_ue_index; 
};
```

- __cucp_uemgr_ue_add__
     
    Called when a new UE context is created.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = pci_set << 16 | pci
        srs_meta_data2 = rnti_set << 16 | rnti
    ```

- __cucp_uemgr_ue_update__
     
    Called when a new UE context is updated.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
        srs_meta_data1 = pci
        srs_meta_data2 = rnti
    ```

- __cucp_uemgr_ue_remove__
     
    Called when a new UE context is deleted.

    Context info:  
    ```
        data: pointer to the jbpf_cuup_e1_ctx_info
        data_end: pointer to end of the jbpf_cuup_e1_ctx_info
    ```

# 9. NGAP

These hooks are called when NGAP procedures are execured.

These hooks have information passed in using a __jbpf_ngap_ctx_info__ as shown below ..
```c
struct jbpf_ngap_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint64_t cucp_ue_index; 
    uint16_t ran_ue_ngap_id_set;
    uint64_t ran_ue_ngap_id; /* RAN UE NGAP ID */
    uint16_t amf_ue_ngap_id_set;
    uint64_t amf_ue_ngap_id; /* AMF UE NGAP ID */
};
```

The different procedures are identified by this enum ..
```c
typedef enum {
    NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP = 1,
    NGAP_PROCEDURE_UE_CONTEXT_RELEASE,
    NGAP_PROCEDURE_PDU_SESSION_SETUP,
    NGAP_PROCEDURE_PDU_SESSION_MODIFY,
    NGAP_PROCEDURE_PDU_SESSION_RELEASE,
    NGAP_PROCEDURE_RESOURCE_ALLOCATION,
    NGAP_PROCEDURE_MAX
} JbpfNgapProcedure_t;
```

- __ngap_procedure_started__
     
    Called when an NGAP procedure is started.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
        srs_meta_data1: procedure (i.e. JbpfNgapProcedure_t)
    ```

- __ngap_procedure_completed__
     
    Called when an NGAP procedure is completed.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
        srs_meta_data1: = success << 32 | procedure;
    ```

- __ngap_procedure_reset__
     
    Called when an NGAP RESET occurs.

    Context info:  
    ```
        data: pointer to the jbpf_ngap_ctx_info
        data_end: pointer to end of the jbpf_ngap_ctx_info
    ```

# 10. RRC

These hooks are called when RRC procedures are execured.

These hooks have information passed in using a __jbpf_rrc_ctx_info__ as shown below ..
```c
struct jbpf_rrc_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint64_t cu_cp_ue_index; 
};
```

The different procedures are identified by this enum ..
```c
typedef enum {
    RRC_SETUP = 1,
    RRC_RECONFIGURATION,
    RRC_REESTABLISHMENT,
    RRC_UE_CAPABILITY,
    RRC_PROCEDURE_MAX
} JbpfRrcProcedure_t;
```

- __rrc_ue_add__
     
    Called when a UE entity is created in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1 = (c_rnti << 48) | (pci << 32) | tac
        srs_meta_data2 = plmn
        srs_meta_data3 = nci
    ```

- __rrc_ue_update_context__
     
    Called when a UE entity is updated in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1: old_cu_ue_index;
        srs_meta_data2: (c_rnti << 48) | (pci << 32) | tac
        srs_meta_data3: plmn
        srs_meta_data4: nci;   
    ```

- __rrc_ue_update_id__
     
    Called when a UE'd 5GTMSI is updated in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1 =_5gtimsi;
    ```
    
- __rrc_ue_remove__
     
    Called when a UE entity is deleted in RRC.

    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
    ```

- __rrc_ue_procedure_started__
     
    Called when an RRC procedure is started.
       
    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1: procedure (i.e JbpfRrcProcedure_t)
    ```

- __rrc_ue_procedure_started__
     
    Called when an RRC procedure is completed.
       
    Context info:  
    ```
        data: pointer to the jbpf_rrc_ctx_info
        data_end: pointer to end of the jbpf_rrc_ctx_info
        srs_meta_data1:srs_meta_data1 = (success << 32) | procedure;
    ```

# 11. RLC

These hooks have information passed in using a __jbpf_rlc_ctx_info__ as shown below ..
```c
struct jbpf_rlc_ctx_info {
    uint16_t ctx_id;    /* Context id (could be implementation specific) */
    uint64_t gnb_du_id;
    uint16_t du_ue_index; 
    uint8_t is_srb;  /* true=srb, false=drb */
    uint8_t rb_id;   /* if is_srb=True:    0=srb0, 1=srb1, 2=srb2,
                     if is_srb=False:      1=drb1, 2=drb2, 3-drb3 ... */
    JbpfRlcMode_t rlc_mode;  /* 0=TM, 1=UM, 2=AM*/
    struct  {
        uint32_t n_sdus;  ///< Number of buffered SDUs that are not marked as discarded.
        uint32_t n_bytes; ///< Number of buffered bytes that are not marked as discarded.
    } sdu_queue_info;
};
```

These enums are also used ..
```c
typedef enum {
    JBPF_RLC_MODE_TM = 1,
    JBPF_RLC_MODE_UM,
    JBPF_RLC_MODE_AM,
    JBPF_RLC_MODE_MAX
} JbpfRlcMode_t;

typedef enum {
    JBPF_RLC_PDUTYPE_STATUS = 1,
    JBPF_RLC_PDUTYPE_DATA,
    JBPF_RLC_PDUTYPE_DATA_RETX,
    JBPF_RLC_PDUTYPE_MAX
} JbpfRlcPdu_t;
```

## 11.1. RLC downlink

- __rlc_dl_creation__
     
    Called when a downlink RLC bearer is created.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

- __rlc_dl_deletion__
     
    Called when a downlink RLC bearer is deleted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

- __rlc_dl_new_sdu__
     
    Called when a new SDU is received from PDCP.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sdu_length << 32 | pdcp_sn;
    ```

- __rlc_dl_discard_sdu__
     
    Called when a SDU is discarded.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn
    ```

- __rlc_dl_sdu_send_started__
     
    Called when the first byte of an SDU is transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
    ```

- __rlc_dl_sdu_send_completed__
     
    Called when all bytes of the SDU have been transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
    ```

- __rlc_dl_sdu_delivered__
     
    Called when all bytes of the SDU have been received by the peer RLC entity
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdcp_sn << 32 | is_retx
    ```

- __rlc_dl_tx_pdu__
     
    Called when an RLC PDU is transmitted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdu_type << 32 | pdu_len
        srs_meta_data2: window_size
    ```

- __rlc_dl_rx_status__
     
    Called when a STATUS PDU is received from lower layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: window_size
    ```

- __rlc_dl_am_tx_pdu_retx_count__
     
    Called when a PDU is retransmitted, ahd shows thw retx count.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: window_size
        srs_meta_data2 = sn << 32 | retx_count;
    ```

- __rlc_dl_am_tx_pdu_max_retx_count_reached__
     
    Called when the maximum allowed RLC retransmissions is reached.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: window_size
        srs_meta_data2 = sn << 32 | retx_count;
    ```
## 11.2. RLC uplink

- __rlc_ul_creation__
     
    Called when a uplink RLC bearer is created.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

- __rlc_ul_deletion__
     
    Called when a uplink RLC bearer is deleted.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
    ```

- __rlc_ul_rx_pdu__
     
    Called when a PDU is received from lower layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: pdu_type << 32 | pdu_len
        srs_meta_data2: window_size     
    ```

- __rlc_ul_sdu_recv_started__
     
    Called when a PDU is received for an SDU for which no bytes have previously been received.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1 = sn << 32 | window_size
    ```

- __rlc_ul_sdu_delivered__
     
    Called when an SDU is delivered to higher layers.
       
    Context info:  
    ```
        data: pointer to the jbpf_rlc_ctx_info
        data_end: pointer to end of the jbpf_rlc_ctx_info
        srs_meta_data1: sn << 32 | window_size
        srs_meta_data2: sdu_length
    ```

