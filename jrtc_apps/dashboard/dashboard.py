# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import os
import sys
import ctypes
from dataclasses import dataclass

JRTC_APP_PATH = os.environ.get("JRTC_APP_PATH")
if JRTC_APP_PATH is None:
    raise ValueError("JRTC_APP_PATH not set")
sys.path.append(f"{JRTC_APP_PATH}")

import jrtc_app
from jrtc_app import *

# Import the protobuf py modules
mac_sched_crc_indication = sys.modules.get('mac_sched_crc_indication')
mac_sched_ul_bsr_indication = sys.modules.get('mac_sched_ul_bsr_indication')
mac_sched_ul_phr_indication = sys.modules.get('mac_sched_ul_phr_indication')
pdcp_dl_delivery = sys.modules.get('pdcp_dl_delivery')
pdcp_dl_new_sdu = sys.modules.get('pdcp_dl_new_sdu')
pdcp_ul_delivery = sys.modules.get('pdcp_ul_delivery')
rrc_ue_add = sys.modules.get('rrc_ue_add')
rrc_ue_procedure = sys.modules.get('rrc_ue_procedure')
rrc_ue_remove = sys.modules.get('rrc_ue_remove')
rrc_ue_update_context = sys.modules.get('rrc_ue_update_context')
rrc_ue_update_id = sys.modules.get('rrc_ue_update_id')
fapi_gnb_dl_config_stats = sys.modules.get('fapi_gnb_dl_config_stats')
fapi_gnb_ul_config_stats = sys.modules.get('fapi_gnb_ul_config_stats')
fapi_gnb_crc_stats = sys.modules.get('fapi_gnb_crc_stats')
fapi_gnb_rach_stats = sys.modules.get('fapi_gnb_rach_stats')

from mac_sched_crc_indication import struct__mac_sched_crc_indication
from mac_sched_ul_bsr_indication import struct__mac_sched_ul_bsr_indication
from mac_sched_ul_phr_indication import struct__mac_sched_ul_phr_indication
from pdcp_dl_delivery import struct__pdcp_dl_delivery
from pdcp_dl_new_sdu import struct__pdcp_dl_new_sdu
from pdcp_ul_delivery import struct__pdcp_ul_delivery
from rrc_ue_add import struct__rrc_ue_add
from rrc_ue_procedure import struct__rrc_ue_procedure
from rrc_ue_remove import struct__rrc_ue_remove
from rrc_ue_update_context import struct__rrc_ue_update_context
from rrc_ue_update_id import struct__rrc_ue_update_id
from fapi_gnb_dl_config_stats import struct__dl_config_stats
from fapi_gnb_ul_config_stats import struct__ul_config_stats
from fapi_gnb_crc_stats import struct__crc_stats
from fapi_gnb_rach_stats import struct__rach_stats


##########################################################################
# Define the state variables for the application
class AppStateVars(ctypes.Structure):
    _fields_ = [
        ("app", ctypes.POINTER(JrtcApp))
    ]        


##########################################################################
# Handler callback function (this function gets called by the C library)
def app_handler(timeout: bool, stream_idx: int, data_entry_ptr: ctypes.POINTER(struct_jrtc_router_data_entry), state_ptr: int):

    MAC_SCHED_UL_BSR_INDICATION_SIDX = 0
    MAC_SCHED_CRC_INDICATION_SIDX = 1
    MAC_SCHED_UL_PHR_INDICATION_SIDX = 2
    PDCP_DL_DELIVERY_SIDX = 3
    PDCP_DL_NEW_SDU_SIDX = 4
    PDCP_UL_DELIVERY_SIDX = 5
    RRC_UE_ADD_SIDX = 6
    RRC_UE_PROCEDURE_SIDX = 7
    RRC_UE_REMOVE_SIDX = 8
    RRC_UE_UPDATE_CONTEXT_SIDX = 9
    RRC_UE_UPDATE_ID_SIDX = 10
    FAPI_DL_CONFIG_SIDX = 11
    FAPI_UL_CONFIG_SIDX = 12
    FAPI_CRC_STATS_SIDX = 13
    FAPI_RACH_STATS_SIDX = 14
    

    if timeout:

        ## timeout processing

        pass

    else:
        
        # Dereference the pointer arguments
        state = ctypes.cast(state_ptr, ctypes.POINTER(AppStateVars)).contents        
        data_entry = data_entry_ptr.contents


        # Check the stream index and process the data accordingly
        if stream_idx == MAC_SCHED_UL_BSR_INDICATION_SIDX:

            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__mac_sched_ul_bsr_indication)
            )
            data = data_ptr.contents
            print(f"MAC_SCHED_UL_BSR_INDICATION: timestamp: {data.timestamp}, cell_index: {data.cell_index}, ue_index: {data.ue_index}, crnti: {data.crnti}, type: {data.type}")
 
        elif stream_idx == MAC_SCHED_CRC_INDICATION_SIDX:
            
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__mac_sched_crc_indication)
            )
            data = data_ptr.contents
            print(f"MAC_SCHED_CRC_INDICATION: timestamp: {data.timestamp}, ue_index: {data.ue_index}, harq_id: {data.harq_id}, tb_crc_success: {data.tb_crc_success}, ul_sinr_dB: {data.ul_sinr_dB}, ul_rsrp_dBFS: {data.ul_rsrp_dBFS}, time_advance_offset: {data.time_advance_offset}")

        elif stream_idx == MAC_SCHED_UL_PHR_INDICATION_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__mac_sched_ul_phr_indication)
            )
            data = data_ptr.contents
            print(f"MAC_SCHED_UL_PHR_INDICATION: timestamp: {data.timestamp}, ue_index: {data.ue_index}, rnti: {data.rnti}")
            # Need to cast to the correct type: , ph_reports: {list(data.ph_reports)}

        elif stream_idx == PDCP_DL_DELIVERY_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__pdcp_dl_delivery)
            )
            data = data_ptr.contents
            print(f"PDCP_DL_DELIVERY: timestamp: {data.timestamp}, ue_index: {data.ue_index}, is_srb: {data.is_srb}, rb_id: {data.rb_id}, rlc_mode: {data.rlc_mode}, notif_count: {data.notif_count}, window_size: {data.window_size}")

        elif stream_idx == PDCP_DL_NEW_SDU_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__pdcp_dl_new_sdu)
            )
            data = data_ptr.contents
            print(f"PDCP_DL_NEW_SDU: timestamp: {data.timestamp}, ue_index: {data.ue_index}, is_srb: {data.is_srb}, rb_id: {data.rb_id}, rlc_mode: {data.rlc_mode}, sdu_length: {data.sdu_length}, count: {data.count}")

        elif stream_idx == PDCP_UL_DELIVERY_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__pdcp_ul_delivery)
            )
            data = data_ptr.contents
            print(f"PDCP_UL_DELIVERY: timestamp: {data.timestamp}, ue_index: {data.ue_index}, is_srb: {data.is_srb}, rb_id: {data.rb_id}, rlc_mode: {data.rlc_mode}, sdu_length: {data.sdu_length}, window_size: {data.window_size}")

        elif stream_idx == RRC_UE_ADD_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_add)
            )
            data = data_ptr.contents
            print(f"RRC_UE_ADD: timestamp: {data.timestamp}, ue_index: {data.ue_index}, c_rnti: {data.c_rnti}, pci: {data.pci}, tac: {data.tac}, plmn: {data.plmn}, nci: {data.nci}")

        elif stream_idx == RRC_UE_PROCEDURE_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_procedure)
            )
            data = data_ptr.contents
            print(f"RRC_UE_PROCEDURE: timestamp: {data.timestamp}, ue_index: {data.ue_index}, procedure: {data.procedure}, success: {data.success}, meta: {data.meta}")

        elif stream_idx == RRC_UE_REMOVE_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_remove)
            )
            data = data_ptr.contents
            print(f"RRC_UE_REMOVE: timestamp: {data.timestamp}, ue_index: {data.ue_index}")

        elif stream_idx == RRC_UE_UPDATE_CONTEXT_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_update_context)
            )
            data = data_ptr.contents
            print(f"RRC_UE_UPDATE_CONTEXT: timestamp: {data.timestamp}, ue_index: {data.ue_index}, old_ue_index: {data.old_ue_index}, c_rnti: {data.c_rnti}, pci: {data.pci}, tac: {data.tac}, plmn: {data.plmn}, nci: {data.nci}")

        elif stream_idx == RRC_UE_UPDATE_ID_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_update_id)
            )
            data = data_ptr.contents
            print(f"RRC_UE_UPDATE_ID: timestamp: {data.timestamp}, ue_index: {data.ue_index}, timsi: {data.timsi}")

        elif stream_idx == FAPI_DL_CONFIG_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__dl_config_stats)
            )

            data = data_ptr.contents
            stats = list(data.stats)
            print("-----------------------------")
            print(f"FAPI_DL_CONFIG: timestamp: {data.timestamp}")
            for stat in stats:
                if stat.rnti > 0:
                    print(f"  cell_id: {stat.cell_id}, rnti: {stat.rnti}, l1_dlc_tx: {stat.l1_dlc_tx}, l1_prb_min: {stat.l1_prb_min}, l1_prb_max: {stat.l1_prb_max}, l1_tbs_min: {stat.l1_tbs_min}, l1_tbs_max: {stat.l1_tbs_max}, l1_mcs_min: {stat.l1_mcs_min}, l1_mcs_max: {stat.l1_mcs_max}, l1_dlc_prb_hist: {list(stat.l1_dlc_prb_hist)}, l1_dlc_mcs_hist: {list(stat.l1_dlc_mcs_hist)}, l1_dlc_tbs_hist: {list(stat.l1_dlc_tbs_hist)}, l1_dlc_ant_hist: {list(stat.l1_dlc_ant_hist)}")

        elif stream_idx == FAPI_UL_CONFIG_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__ul_config_stats)
            )
            data = data_ptr.contents
            stats = list(data.stats)
            print("-----------------------------")
            print(f"FAPI_UL_CONFIG: timestamp: {data.timestamp}")
            for stat in stats:
                if stat.rnti > 0:
                    print(f"  cell_id: {stat.cell_id}, rnti: {stat.rnti}, l1_ulc_tx: {stat.l1_ulc_tx}, l1_prb_min: {stat.l1_prb_min}, l1_prb_max: {stat.l1_prb_max}, l1_tbs_min: {stat.l1_tbs_min}, l1_tbs_max: {stat.l1_tbs_max}, l1_mcs_min: {stat.l1_mcs_min}, l1_mcs_max: {stat.l1_mcs_max}, l1_ulc_prb_hist: {list(stat.l1_ulc_prb_hist)}, l1_ulc_mcs_hist: {list(stat.l1_ulc_mcs_hist)}, l1_ulc_tbs_hist: {list(stat.l1_ulc_tbs_hist)}, l1_ulc_ant_hist: {list(stat.l1_ulc_ant_hist)}")

        elif stream_idx == FAPI_CRC_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__crc_stats)
            )
            data = data_ptr.contents
            stats = list(data.stats)
            print("-----------------------------")
            print(f"FAPI_CRC_STATS: timestamp: {data.timestamp}")
            for stat in stats:
                if stat.rnti > 0:
                    print(f"  cell_id: {stat.cell_id}, rnti: {stat.rnti}, l1_ta_min: {stat.l1_ta_min}, l1_ta_max: {stat.l1_ta_max}, l1_snr_min: {stat.l1_snr_min}, l1_snr_max: {stat.l1_snr_max}, l1_crc_ta_hist: {list(stat.l1_crc_ta_hist)}, l1_crc_snr_hist: {list(stat.l1_crc_snr_hist)}")

        elif stream_idx == FAPI_RACH_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rach_stats)
            )
            data = data_ptr.contents
            print("-----------------------------")
            print(f"FAPI_RACH_STATS: timestamp: {data.timestamp}")
            stats = list(data.l1_rach_ta_hist)
            for stat in stats:
                if stat.rnti > 0:
                    print(f"  ta: {stat.ta}, cnt: {stat.cnt}")
            stats = list(data.l1_rach_pwr_hist)
            for stat in stats:
                if stat.rnti > 0:
                    print(f"  pwr: {stat.pwr}, cnt: {stat.cnt}")

        else:
            print(f"Unknown stream index: {stream_idx}")
            return


##########################################################################
# Main function to start the app (converted from jrtc_start_app)
def jrtc_start_app(capsule):

    streams = [
        # GENERATOR_OUT_STREAM_IDX
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/mac_detailed/mac_sched_ul_bsr_indication", 
                b"mac_sched_ul_bsr_indication_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/mac_detailed/mac_sched_crc_indication", 
                b"mac_sched_crc_indication_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/mac_detailed/mac_sched_ul_phr_indication", 
                b"mac_sched_ul_phr_indication_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_detailed/pdcp_dl_delivery", 
                b"pdcp_dl_delivery_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_detailed/pdcp_dl_new_sdu", 
                b"pdcp_dl_new_sdu_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_detailed/pdcp_ul_delivery", 
                b"pdcp_ul_delivery_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_add", 
                b"rrc_ue_add_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_procedure", 
                b"rrc_ue_procedure_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_remove", 
                b"rrc_ue_remove_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_context", 
                b"rrc_ue_update_context_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_id", 
                b"rrc_ue_update_id_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_dl_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_ul_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_crc_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ),
        JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_rach_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        )
    ]

    app_cfg = JrtcAppCfg_t(
        b"mac_detailed",                               # context
        100,                                           # q_size
        len(streams),                                  # num_streams
        (JrtcStreamCfg_t * len(streams))(*streams),    # streams
        10.0,                                          # initialization_timeout_secs
        0.25,                                          # sleep_timeout_secs
        2.0                                            # inactivity_timeout_secs
    )

    # Initialize the app
    state = AppStateVars()
    state.app = jrtc_app_create(capsule, app_cfg, app_handler, state)

    # run the app - This is blocking until the app exists
    jrtc_app_run(state.app)

    # clean up app resources
    jrtc_app_destroy(state.app)

