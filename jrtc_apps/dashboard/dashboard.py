# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import json
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


include_perf = True
include_rrc = True
include_pdcp = False
include_mac = True
include_fapi = True
include_xran = False

# Import the protobuf py modules
if include_perf:
    jbpf_stats_report = sys.modules.get('jbpf_stats_report')
    from jbpf_stats_report import struct__jbpf_out_perf_list
if include_rrc:
    rrc_ue_add = sys.modules.get('rrc_ue_add')
    rrc_ue_procedure = sys.modules.get('rrc_ue_procedure')
    rrc_ue_remove = sys.modules.get('rrc_ue_remove')
    rrc_ue_update_context = sys.modules.get('rrc_ue_update_context')
    rrc_ue_update_id = sys.modules.get('rrc_ue_update_id')
    from rrc_ue_add import struct__rrc_ue_add
    from rrc_ue_procedure import struct__rrc_ue_procedure
    from rrc_ue_remove import struct__rrc_ue_remove
    from rrc_ue_update_context import struct__rrc_ue_update_context
    from rrc_ue_update_id import struct__rrc_ue_update_id
if include_pdcp:
    pdcp_dl_north_stats = sys.modules.get('pdcp_dl_north_stats')
    pdcp_dl_south_stats = sys.modules.get('pdcp_dl_south_stats')
    pdcp_ul_stats = sys.modules.get('pdcp_ul_stats')
    from pdcp_dl_north_stats import struct__dl_north_stats
    from pdcp_dl_south_stats import struct__dl_south_stats
    # DEBUG
    #from pdcp_ul_stats import struct__pdcp_ul_stats
if include_mac:
    mac_sched_crc_stats = sys.modules.get('mac_sched_crc_stats')
    mac_sched_bsr_stats = sys.modules.get('mac_sched_bsr_stats')
    mac_sched_phr_stats = sys.modules.get('mac_sched_phr_stats')
    from mac_sched_crc_stats import struct__crc_stats
    from mac_sched_bsr_stats import struct__bsr_stats
    from mac_sched_phr_stats import struct__phr_stats
if include_fapi:
    fapi_gnb_dl_config_stats = sys.modules.get('fapi_gnb_dl_config_stats')
    fapi_gnb_ul_config_stats = sys.modules.get('fapi_gnb_ul_config_stats')
    fapi_gnb_crc_stats = sys.modules.get('fapi_gnb_crc_stats')
    fapi_gnb_rach_stats = sys.modules.get('fapi_gnb_rach_stats')
    from fapi_gnb_dl_config_stats import struct__dl_config_stats
    from fapi_gnb_ul_config_stats import struct__ul_config_stats
    from fapi_gnb_crc_stats import struct__crc_stats as struct__fapi_crc_stats
    from fapi_gnb_rach_stats import struct__rach_stats
if include_xran:
    xran_packet_info = sys.modules.get('xran_packet_info')
    from xran_packet_info import struct__packet_stats



class Map:
    def __init__(self):
        self.ue_idx_map = {}  # Maps ue_index to (rnti, timsi)
        self.rnti_map = {}    # Maps rnti to ue_index
        self.timsi_map = {}   # Maps timsi to ue_index

    # def add_ue_idx_rnti(self, ue_idx, rnti):
    #     """Add a (ue_idx, rnti) pair."""
    #     if ue_idx not in self.ue_idx_map:
    #         self.ue_idx_map[ue_idx] = [None, None]
    #     self.ue_idx_map[ue_idx][0] = rnti
    #     self.rnti_map[rnti] = ue_idx

    # def add_ue_idx_timsi(self, ue_idx, timsi):
    #     """Add a (ue_idx, timsi) pair."""
    #     if ue_idx not in self.ue_idx_map:
    #         self.ue_idx_map[ue_idx] = [None, None]
    #     self.ue_idx_map[ue_idx][1] = timsi
    #     self.timsi_map[timsi] = ue_idx



    def add_ue_idx_rnti(self, ue_idx, rnti):
        """Add or update a (ue_idx, rnti) pair."""
        # Remove stale rnti mapping if it exists
        if rnti in self.rnti_map:
            old_ue_idx = self.rnti_map.pop(rnti)
            if old_ue_idx in self.ue_idx_map:
                self.ue_idx_map[old_ue_idx][0] = None

        # Remove stale ue_idx mapping if it exists
        if ue_idx in self.ue_idx_map:
            old_rnti, _ = self.ue_idx_map[ue_idx]
            if old_rnti is not None:
                self.rnti_map.pop(old_rnti, None)

        # Add or update the mapping
        if ue_idx not in self.ue_idx_map:
            self.ue_idx_map[ue_idx] = [None, None]
        self.ue_idx_map[ue_idx][0] = rnti
        self.rnti_map[rnti] = ue_idx

    def add_ue_idx_timsi(self, ue_idx, timsi):
        """Add or update a (ue_idx, timsi) pair."""
        # Remove stale timsi mapping if it exists
        if timsi in self.timsi_map:
            old_ue_idx = self.timsi_map.pop(timsi)
            if old_ue_idx in self.ue_idx_map:
                self.ue_idx_map[old_ue_idx][1] = None

        # Remove stale ue_idx mapping if it exists
        if ue_idx in self.ue_idx_map:
            _, old_timsi = self.ue_idx_map[ue_idx]
            if old_timsi is not None:
                self.timsi_map.pop(old_timsi, None)

        # Add or update the mapping
        if ue_idx not in self.ue_idx_map:
            self.ue_idx_map[ue_idx] = [None, None]
        self.ue_idx_map[ue_idx][1] = timsi
        self.timsi_map[timsi] = ue_idx


    def search_by_rnti(self, rnti):
        """Search for a triplet by rnti."""
        ue_idx = self.rnti_map.get(rnti)
        if ue_idx is not None:
            _, timsi = self.ue_idx_map[ue_idx]
            timsi = timsi if timsi is not None else ""
            return (ue_idx, rnti, timsi)
        return ("", "", "")

    def search_by_ue_idx(self, ue_idx):
        """Search for a triplet by ue_idx."""
        if ue_idx in self.ue_idx_map:
            rnti, timsi = self.ue_idx_map[ue_idx]
            rnti = rnti if rnti is not None else ""
            timsi = timsi if timsi is not None else ""
            return (ue_idx, rnti, timsi)
        return ("", "", "")

    def delete_by_ue_idx(self, ue_idx):
        """Delete all information related to a ue_index."""
        if ue_idx in self.ue_idx_map:
            rnti, timsi = self.ue_idx_map.pop(ue_idx)
            if rnti is not None:
                self.rnti_map.pop(rnti, None)
            if timsi is not None:
                self.timsi_map.pop(timsi, None)


map = Map()


##########################################################################
# Define the state variables for the application
class AppStateVars(ctypes.Structure):
    _fields_ = [
        ("app", ctypes.POINTER(JrtcApp))
    ]        


##########################################################################
# Handler callback function (this function gets called by the C library)
def app_handler(timeout: bool, stream_idx: int, data_entry_ptr: ctypes.POINTER(struct_jrtc_router_data_entry), state_ptr: int):

    #print(f"DEBUG - app_handler: stream_idx: {stream_idx}, timeout: {timeout}")

    if timeout:

        ## timeout processing

        pass

    else:
        
        # Dereference the pointer arguments
        state = ctypes.cast(state_ptr, ctypes.POINTER(AppStateVars)).contents        
        data_entry = data_entry_ptr.contents
        output = {}

        # Check the stream index and process the data accordingly



        #####################################################
        ### Perf

        if stream_idx == JBPF_STATS_REPORT_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__jbpf_out_perf_list)
            )
            data = data_ptr.contents
            perfs = list(data.hook_perf)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "JBPF_STATS_REPORT",
                "meas_period": data.meas_period,
                "perfs": []
            }
            cnt = 0
            for perf in perfs:
                output["perfs"].append({
                    "hook_name": perf.hook_name,
                    "num": perf.num,
                    "min": perf.min,
                    "max": perf.max,
                    "hist": list(perf.hist)
                })
                cnt += 1
                if cnt >= data.hook_perf_count:
                    break
                # print(f"  hook_name: {perf.hook_name}, "
                #     f"num: {perf.num}, "
                #     f"min: {perf.min}, "
                #     f"max: {perf.max}, "
                #     f"hist: {perf.hist} ")
            print(f"JBPF_STATS_REPORT: {output}")



        #####################################################
        ### RRC

        elif stream_idx == RRC_UE_ADD_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_add)
            )
            data = data_ptr.contents
            map.add_ue_idx_rnti(data.ue_index, data.c_rnti)
            _, _, timsi = map.search_by_ue_idx(data.ue_index)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "RRC_UE_ADD",
                "ue_index": data.ue_index,
                "timsi": timsi,
                "c_rnti": data.c_rnti,
                "pci": data.pci,
                "tac": data.tac,
                "plmn": data.plmn,
                "nci": data.nci
            }
            print(f"RRC_UE_ADD: {output}")
            #print(f"RRC_UE_ADD: timestamp: {data.timestamp}, ue_index: {data.ue_index}, c_rnti: {data.c_rnti}, pci: {data.pci}, tac: {data.tac}, plmn: {data.plmn}, nci: {data.nci}")

        elif stream_idx == RRC_UE_PROCEDURE_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_procedure)
            )
            data = data_ptr.contents
            _, _, timsi = map.search_by_ue_idx(data.ue_index)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "RRC_UE_PROCEDURE",
                "ue_index": data.ue_index,
                "timsi": timsi,
                "procedure": data.procedure,
                "success": data.success,
                "meta": data.meta
            }
            print(f"RRC_UE_PROCEDURE: {output}")
            #print(f"RRC_UE_PROCEDURE: timestamp: {data.timestamp}, ue_index: {data.ue_index}, procedure: {data.procedure}, success: {data.success}, meta: {data.meta}")

        elif stream_idx == RRC_UE_REMOVE_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_remove)
            )
            data = data_ptr.contents
            _, _, timsi = map.search_by_ue_idx(data.ue_index)
            map.delete_by_ue_idx(data.ue_index)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "RRC_UE_REMOVE",
                "ue_index": data.ue_index,
                "timsi": timsi
            }
            print(f"RRC_UE_REMOVE: {output}")
            #print(f"RRC_UE_REMOVE: timestamp: {data.timestamp}, ue_index: {data.ue_index}")

        elif stream_idx == RRC_UE_UPDATE_CONTEXT_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_update_context)
            )
            data = data_ptr.contents
            # Check if the algorithm below corresponds to srsRAN procedure
            _, _, timsi = map.search_by_ue_idx(data.old_ue_index)
            map.delete_by_ue_idx(data.old_ue_index)
            map.add_ue_idx_rnti(data.ue_index, data.c_rnti)
            if timsi:
                map.add_ue_idx_timsi(data.ue_index, timsi)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "RRC_UE_UPDATE_CONTEXT",
                "ue_index": data.ue_index,
                "timsi": timsi,
                "old_ue_index": data.old_ue_index,
                "c_rnti": data.c_rnti,
                "pci": data.pci,
                "tac": data.tac,
                "plmn": data.plmn,
                "nci": data.nci
            }
            print(f"RRC_UE_UPDATE_CONTEXT: {output}")
            #print(f"RRC_UE_UPDATE_CONTEXT: timestamp: {data.timestamp}, ue_index: {data.ue_index}, old_ue_index: {data.old_ue_index}, c_rnti: {data.c_rnti}, pci: {data.pci}, tac: {data.tac}, plmn: {data.plmn}, nci: {data.nci}")

        elif stream_idx == RRC_UE_UPDATE_ID_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rrc_ue_update_id)
            )
            data = data_ptr.contents
            map.add_ue_idx_timsi(data.ue_index, data.timsi)
            output = {
                "timestamp": data.timestamp,
                "stream_index": stream_idx,
                "ue_index": data.ue_index,
                "timsi": data.timsi
            }
            print(f"RRC_UE_UPDATE_ID: {output}")
            # print(f"RRC_UE_UPDATE_ID: timestamp: {data.timestamp}, ue_index: {data.ue_index}, timsi: {data.timsi}")



        #####################################################
        ### PDCP

        elif stream_idx == PDCP_DL_NORTH_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__dl_north_stats)
            )
            data = data_ptr.contents
            dl_north_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "PDCP_DL_NORTH_STATS",
                "stats": []
            }
            cnt = 0
            for stat in dl_north_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi, 
                    "rb_id": stat.rb_id,
                    "avg_sdu": stat.total_sdu / stat.sdu_count,
                    "min_sdu": stat.min_sdu,
                    "max_sdu": stat.max_sdu
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"PDCP_DL_NORTH_STATS: {output}")

        elif stream_idx == PDCP_DL_SOUTH_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__dl_south_stats)
            )
            data = data_ptr.contents
            dl_south_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "PDCP_DL_SOUTH_STATS",
                "stats": []
            }
            cnt = 0
            for stat in dl_south_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi, 
                    "rb_id": stat.rb_id,
                    "sdu_count": stat.sdu_count,
                    "avg_win": stat.total_win / stat.sdu_count,
                    "min_win": stat.min_win,
                    "max_win": stat.max_win,
                    "avg_delay": stat.total_delay / stat.delay_count,
                    "min_delay": stat.min_delay,
                    "max_delay": stat.max_delay,
                    "total_queue_B": stat.total_queue_B / stat.queue_count,
                    "min_queue_B": stat.min_queue_B,
                    "max_queue_B": stat.max_queue_B,
                    "total_queue_pkt": stat.total_queue_pkt / stat.queue_count,
                    "min_queue_pkt": stat.min_queue_pkt,
                    "max_queue_pkt": stat.max_queue_pkt
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"PDCP_DL_SOUTH_STATS: {output}")

        elif stream_idx == PDCP_UL_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__pdcp_ul_stats)
            )
            data = data_ptr.contents
            ul_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "PDCP_UL_STATS",
                "stats": []
            }
            cnt = 0
            for stat in ul_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi,
                    "rb_id": stat.rb_id,
                    "avg_sdu": stat.total_sdu / stat.sdu_count,
                    "min_sdu": stat.min_sdu,
                    "max_sdu": stat.max_sdu,
                    "avg_win": stat.total_win / stat.sdu_count,
                    "min_win": stat.min_win,
                    "max_win": stat.max_win
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"PDCP_UL_STATS: {output}")



        #####################################################
        ### MAC

        elif stream_idx == MAC_SCHED_CRC_STATS_SIDX:
            
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__crc_stats)
            )
            data = data_ptr.contents
            crc_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "MAC_SCHED_CRC_STATS",
                "stats": []
            }
            cnt = 0
            for stat in crc_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi,
                    "cons_min": stat.cons_min,
                    "cons_max": stat.cons_max,
                    "succ_rate": stat.succ_tx / stat.cnt_tx,
                    "min_sinr": stat.min_sinr,
                    "min_rsrp": stat.min_rsrp,
                    "max_sinr": stat.max_sinr,
                    "max_rsrp": stat.max_rsrp,
                    "avg_sinr": stat.sum_sinr / stat.cnt_sinr,
                    "avg_rsrp": stat.sum_rsrp / stat.cnt_rsrp
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"MAC_SCHED_CRC_STATS: {output}")

        elif stream_idx == MAC_SCHED_BSR_STATS_SIDX:

            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__bsr_stats)
            )
            data = data_ptr.contents
            bsr_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "MAC_SCHED_BSR_STATS",
                "stats": []
            }
            cnt = 0
            for stat in bsr_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi,
                    "cnt": stat.cnt
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"MAC_SCHED_BSR_STATS: {output}")
 
        elif stream_idx == MAC_SCHED_PHR_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__phr_stats)
            )
            data = data_ptr.contents
            phr_stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "MAC_SCHED_PHR_STATS",
                "stats": []
            }
            cnt = 0
            for stat in phr_stats:
                _, _, timsi = map.search_by_ue_idx(stat.ue_index)
                output["stats"].append({
                    "ue_index": stat.ue_index,
                    "timsi": timsi,
                    "serv_cell_id": stat.serv_cell_id,
                    "ph_min": stat.ph_min,
                    "ph_max": stat.ph_max,
                    "p_cmax_min": stat.p_cmax_min,
                    "p_cmax_max": stat.p_cmax_max
                })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"MAC_SCHED_PHR_STATS: {output}")



        #####################################################
        ### FAPI

        elif stream_idx == FAPI_DL_CONFIG_SIDX:
            #return
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__dl_config_stats)
            )

            data = data_ptr.contents
            stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "FAPI_DL_CONFIG",
                "ues": []
            }
            cnt = 0
            for stat in stats:
                if stat.rnti > 0:
                    ue_index, _, timsi = map.search_by_rnti(stat.rnti)
                    output["ues"].append({
                        "cell_id": stat.cell_id,
                        "ue_index": ue_index,
                        "timsi": timsi,
                        "rnti": stat.rnti,
                        "l1_dlc_tx": stat.l1_dlc_tx,
                        "l1_prb_min": stat.l1_prb_min,
                        "l1_prb_max": stat.l1_prb_max,
                        "l1_tbs_min": stat.l1_tbs_min,
                        "l1_tbs_max": stat.l1_tbs_max,
                        "l1_mcs_min": stat.l1_mcs_min,
                        "l1_mcs_max": stat.l1_mcs_max,
                        "l1_dlc_prb_hist": list(stat.l1_dlc_prb_hist),
                        "l1_dlc_mcs_hist": list(stat.l1_dlc_mcs_hist),
                        "l1_dlc_tbs_hist": list(stat.l1_dlc_tbs_hist),
                        "l1_dlc_ant_hist": list(stat.l1_dlc_ant_hist)
                    })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"FAPI_DL_CONFIG: {output}")

        elif stream_idx == FAPI_UL_CONFIG_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__ul_config_stats)
            )
            data = data_ptr.contents
            stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "FAPI_UL_CONFIG",
                "ues": []
            }
            cnt = 0
            for stat in stats:
                if stat.rnti > 0:
                    ue_index, _, timsi = map.search_by_rnti(stat.rnti)
                    output["ues"].append({
                        "cell_id": stat.cell_id,
                        "ue_index": ue_index,
                        "timsi": timsi,
                        "rnti": stat.rnti,
                        "l1_ulc_tx": stat.l1_ulc_tx,
                        "l1_prb_min": stat.l1_prb_min,
                        "l1_prb_max": stat.l1_prb_max,
                        "l1_tbs_min": stat.l1_tbs_min,
                        "l1_tbs_max": stat.l1_tbs_max,
                        "l1_mcs_min": stat.l1_mcs_min,
                        "l1_mcs_max": stat.l1_mcs_max,
                        "l1_ulc_prb_hist": list(stat.l1_ulc_prb_hist),
                        "l1_ulc_mcs_hist": list(stat.l1_ulc_mcs_hist),
                        "l1_ulc_tbs_hist": list(stat.l1_ulc_tbs_hist),
                        "l1_ulc_ant_hist": list(stat.l1_ulc_ant_hist)
                    })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"FAPI_UL_CONFIG: {output}")

        elif stream_idx == FAPI_CRC_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__fapi_crc_stats)
            )
            data = data_ptr.contents
            stats = list(data.stats)
            output = {
                "timestamp": data.timestamp,
                "stream_index": "FAPI_CRC_STATS",
                "ues": []
            }
            cnt = 0
            for stat in stats:
                if stat.rnti > 0:
                    ue_index, _, timsi = map.search_by_rnti(stat.rnti)
                    output["ues"].append({
                        "cell_id": stat.cell_id,
                        "ue_index": ue_index,
                        "timsi": timsi,
                        "rnti": stat.rnti,
                        "l1_crc_ta_hist": list(stat.l1_crc_ta_hist),
                        "l1_crc_snr_hist": list(stat.l1_crc_snr_hist),
                        "l1_ta_min": stat.l1_ta_min,
                        "l1_ta_max": stat.l1_ta_max,
                        "l1_snr_min": stat.l1_snr_min,
                        "l1_snr_max": stat.l1_snr_max
                    })
                cnt += 1
                if cnt >= data.stats_count:
                    break
            print(f"FAPI_CRC_STATS: {output}")

        elif stream_idx == FAPI_RACH_STATS_SIDX:
            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__rach_stats)
            )
            data = data_ptr.contents
            output = {
                "timestamp": data.timestamp,
                "stream_index": "FAPI_RACH_STATS",
                "ta": [],
                "pwr": []
            }
            stats = list(data.l1_rach_ta_hist)
            cnt = 0
            for stat in stats:
                output["ta"].append({
                    "ta": stat.ta,
                    "cnt": stat.cnt,
                })
                cnt += 1
                if cnt >= data.l1_rach_ta_hist_count:
                    break
            stats = list(data.l1_rach_pwr_hist)
            cnt = 0
            for stat in stats:
                output["pwr"].append({
                    "pwr": stat.pwr,
                    "cnt": stat.cnt
                })
                cnt += 1
                if cnt >= data.l1_rach_pwr_hist_count:
                    break
            print(f"FAPI_RACH_STATS: {output}")


        ###########
        # XRAN
        
        elif stream_idx == XRAN_CODELET_OUT_SIDX:

            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__packet_stats)
            )

            data = data_ptr.contents
            ul_data_stats = data.ul_packet_stats.data_packet_stats
            dl_data_stats = data.dl_packet_stats.data_packet_stats
            dl_control_stats = data.dl_packet_stats.ctrl_packet_stats

            print("****----------------------------")
            print(f"*Hi App 1: timestamp: {data.timestamp}")
            print(f"*DL Ctl: {dl_control_stats.Packet_count} {list(dl_control_stats.packet_inter_arrival_info.hist)}")
            print(f"*DL Data: {dl_data_stats.Packet_count} {dl_data_stats.Prb_count} {list(dl_data_stats.packet_inter_arrival_info.hist)}")

        else:
            print(f"Unknown stream index: {stream_idx}")
            output = {
                "stream_index": stream_idx,
                "error": "Unknown stream index"
            }

        # Send the output to the dashboard



##########################################################################
# Main function to start the app (converted from jrtc_start_app)
def jrtc_start_app(capsule):

    global MAC_SCHED_CRC_STATS_SIDX
    global MAC_SCHED_BSR_STATS_SIDX
    global MAC_SCHED_PHR_STATS_SIDX
    global PDCP_DL_NORTH_STATS_SIDX
    global PDCP_DL_SOUTH_STATS_SIDX
    global PDCP_UL_STATS_SIDX
    global RRC_UE_ADD_SIDX
    global RRC_UE_PROCEDURE_SIDX
    global RRC_UE_REMOVE_SIDX
    global RRC_UE_UPDATE_CONTEXT_SIDX
    global RRC_UE_UPDATE_ID_SIDX 
    global FAPI_DL_CONFIG_SIDX 
    global FAPI_UL_CONFIG_SIDX 
    global FAPI_CRC_STATS_SIDX 
    global FAPI_RACH_STATS_SIDX 
    global JBPF_STATS_REPORT_SIDX
    global XRAN_CODELET_OUT_SIDX

    MAC_SCHED_CRC_STATS_SIDX = -1
    MAC_SCHED_BSR_STATS_SIDX = -1
    MAC_SCHED_PHR_STATS_SIDX = -1
    PDCP_DL_NORTH_STATS_SIDX = -1
    PDCP_DL_SOUTH_STATS_SIDX = -1
    PDCP_UL_STATS_SIDX = -1
    RRC_UE_ADD_SIDX = -1
    RRC_UE_PROCEDURE_SIDX = -1
    RRC_UE_REMOVE_SIDX = -1
    RRC_UE_UPDATE_CONTEXT_SIDX = -1
    RRC_UE_UPDATE_ID_SIDX = -1
    FAPI_DL_CONFIG_SIDX = -1
    FAPI_UL_CONFIG_SIDX = -1
    FAPI_CRC_STATS_SIDX = -1
    FAPI_RACH_STATS_SIDX = -1
    JBPF_STATS_REPORT_SIDX = -1
    XRAN_CODELET_OUT_SIDX = -1

    last_cnt = 0


    streams = []


    #####################################################
    ### Perf

    if include_perf:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/jbpf_stats/jbpf_stats_report", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        JBPF_STATS_REPORT_SIDX = last_cnt
        print(f"JBPF_STATS_REPORT_SIDX: {JBPF_STATS_REPORT_SIDX}")
        last_cnt += 1



    #####################################################
    ### RRC

    if include_rrc:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_add", 
                b"rrc_ue_add_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_ADD_SIDX = last_cnt
        print(f"RRC_UE_ADD_SIDX: {RRC_UE_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_procedure", 
                b"rrc_ue_procedure_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_PROCEDURE_SIDX = last_cnt
        print(f"RRC_UE_PROCEDURE_SIDX: {RRC_UE_PROCEDURE_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_remove", 
                b"rrc_ue_remove_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_REMOVE_SIDX = last_cnt
        print(f"RRC_UE_REMOVE_SIDX: {RRC_UE_REMOVE_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_context", 
                b"rrc_ue_update_context_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_UPDATE_CONTEXT_SIDX = last_cnt
        print(f"RRC_UE_UPDATE_CONTEXT_SIDX: {RRC_UE_UPDATE_CONTEXT_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rrc/rrc_ue_update_id", 
                b"rrc_ue_update_id_output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RRC_UE_UPDATE_ID_SIDX = last_cnt
        print(f"RRC_UE_UPDATE_ID_SIDX: {RRC_UE_UPDATE_ID_SIDX}")
        last_cnt += 1



    #####################################################
    ### PDCP

    if include_pdcp:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_stats/pdcp_collect", 
                b"output_map_dl_north"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        PDCP_DL_NORTH_STATS_SIDX = last_cnt
        print(f"PDCP_DL_NORTH_STATS_SIDX: {PDCP_DL_NORTH_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_stats/pdcp_collect", 
                b"output_map_dl_south"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        PDCP_DL_SOUTH_STATS_SIDX = last_cnt
        print(f"PDCP_DL_SOUTH_STATS_SIDX: {PDCP_DL_SOUTH_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/pdcp_stats/pdcp_collect", 
                b"output_map_ul"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        PDCP_UL_STATS_SIDX = last_cnt
        print(f"PDCP_UL_STATS_SIDX: {PDCP_UL_STATS_SIDX}")
        last_cnt += 1



    #####################################################
    ### MAC

    if include_mac:
        # MAC SCHEDULER
        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_crc"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_CRC_STATS_SIDX = last_cnt
        print(f"MAC_SCHED_CRC_STATS_SIDX: {MAC_SCHED_CRC_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_bsr"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_BSR_STATS_SIDX = last_cnt
        print(f"MAC_SCHED_BSR_STATS_SIDX: {MAC_SCHED_BSR_STATS_SIDX}")
        last_cnt += 1
        
        streams.append(JrtcStreamCfg_t(
                JrtcStreamIdCfg_t(
                    JRTC_ROUTER_REQ_DEST_ANY, 
                    JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    b"dashboard://jbpf_agent/mac_stats/mac_stats_collect", 
                    b"output_map_phr"),
                True,   # is_rx
                None    # No AppChannelCfg 
            ))
        MAC_SCHED_PHR_STATS_SIDX = last_cnt
        print(f"MAC_SCHED_PHR_STATS_SIDX: {MAC_SCHED_PHR_STATS_SIDX}")
        last_cnt += 1



    #####################################################
    ### FAPI

    if include_fapi:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_dl_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_DL_CONFIG_SIDX = last_cnt
        print(f"FAPI_DL_CONFIG_SIDX: {FAPI_DL_CONFIG_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_ul_config_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_UL_CONFIG_SIDX = last_cnt
        print(f"FAPI_UL_CONFIG_SIDX: {FAPI_UL_CONFIG_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_crc_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_CRC_STATS_SIDX = last_cnt
        print(f"FAPI_CRC_STATS_SIDX: {FAPI_CRC_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/fapi_gnb_rach_stats/codelet2", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        FAPI_RACH_STATS_SIDX = last_cnt
        print(f"FAPI_RACH_STATS_SIDX: {FAPI_RACH_STATS_SIDX}")
        last_cnt += 1


    #####################################################
    ### XRAN

    if include_xran:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/xran_packets/reporter", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        XRAN_CODELET_OUT_SIDX = last_cnt
        print(f"XRAN_CODELET_OUT_SIDX: {XRAN_CODELET_OUT_SIDX}")
        last_cnt += 1


    print(f"Number of subscribed streams: {len(streams)}")


    app_cfg = JrtcAppCfg_t(
        b"dashboard",                                  # context
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

