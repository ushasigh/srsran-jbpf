# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import time
import json
import os
import sys
import ctypes
import socket
import threading
from dataclasses import dataclass, asdict
from typing import Dict

JRTC_APP_PATH = os.environ.get("JRTC_APP_PATH")
if JRTC_APP_PATH is None:
    raise ValueError("JRTC_APP_PATH not set")
sys.path.append(f"{JRTC_APP_PATH}")

import jrtc_app
from jrtc_app import *


include_ue_contexts = True
include_perf = True
include_rrc = True
include_ngap = True
include_pdcp = True
include_rlc = True
include_mac = True
include_fapi = True
include_xran = False


# always include the logger modules
logger = sys.modules.get('logger')
from logger import Logger
la_logger = sys.modules.get('la_logger')
from la_logger import LaLogger, LaLoggerConfig

# always include the ue_contexts_map module
ue_contexts_map = sys.modules.get('ue_contexts_map')    
from ue_contexts_map import UeContextsMap, JbpfNgapProcedure, JbpRrcProcedure

# Import the protobuf py modules
if include_ue_contexts:
    ue_contexts = sys.modules.get('ue_contexts')
    from ue_contexts import struct__du_ue_ctx_creation, struct__du_ue_ctx_update_crnti, struct__du_ue_ctx_deletion, \
                            struct__cucp_ue_ctx_creation, struct__cucp_ue_ctx_update, struct__cucp_ue_ctx_deletion, \
                            struct__e1ap_cucp_bearer_ctx_setup, struct__e1ap_cuup_bearer_ctx_setup, struct__e1ap_cuup_bearer_ctx_release
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
if include_ngap:
    ngap = sys.modules.get('ngap')
    from ngap import struct__ngap_procedure_started, struct__ngap_procedure_completed, struct__ngap_reset
if include_pdcp:
    pdcp_dl_north_stats = sys.modules.get('pdcp_dl_north_stats')
    pdcp_dl_south_stats = sys.modules.get('pdcp_dl_south_stats')
    pdcp_ul_stats = sys.modules.get('pdcp_ul_stats')
    from pdcp_dl_north_stats import struct__dl_north_stats
    from pdcp_dl_south_stats import struct__dl_south_stats
    from pdcp_ul_stats import struct__ul_stats
if include_rlc:
    rlc_dl_north_stats = sys.modules.get('rlc_dl_north_stats')
    rlc_dl_south_stats = sys.modules.get('rlc_dl_south_stats')
    rlc_ul_stats = sys.modules.get('rlc_ul_stats')
    from rlc_dl_north_stats import struct__rlc_dl_north_stats
    from rlc_dl_south_stats import struct__rlc_dl_south_stats
    from rlc_ul_stats import struct__rlc_ul_stats
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


# create lock.
# This is used by "json_handler" and "app_handler" to ensure they use the resources safely.
app_lock = threading.Lock()



##########################################################################
def rrc_procedure_to_str(procedure: int) -> str:
    if procedure == JbpRrcProcedure.RRC_PROCEDURE_SETUP:
        return "RRC_SETUP"
    elif procedure == JbpRrcProcedure.RRC_PROCEDURE_RECONFIGURATION:
        return "RRC_RECONFIGURATION"
    elif procedure == JbpRrcProcedure.RRC_PROCEDURE_REESTABLISHMENT:
        return "RRC_REESTABLISHMENT"
    elif procedure == JbpRrcProcedure.RRC_PROCEDURE_UE_CAPABILITY:
        return "RRC_UE_CAPABILITY"
    else:
        return "UNKNOWN"


##########################################################################
def ngap_procedure_to_str(procedure: int) -> str:
    if procedure == JbpfNgapProcedure.NGAP_PROCEDURE_INITIAL_CONTEXT_SETUP:
        return "INITIAL_CONTEXT_SETUP"
    elif procedure == JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
        return "UE_CONTEXT_RELEASE"
    elif procedure == JbpfNgapProcedure.NGAP_PROCEDURE_PDU_SESSION_SETUP:
        return "PDU_SESSION_SETUP"
    elif procedure == JbpfNgapProcedure.NGAP_PROCEDURE_PDU_SESSION_MODIFY:
        return "PDU_SESSION_MODIFY"
    elif procedure == JbpfNgapProcedure.NGAP_PROCEDURE_PDU_SESSION_RELEASE:
        return "PDU_SESSION_RELEASE"
    elif procedure == JbpfNgapProcedure.NGAP_PROCEDURE_RESOURCE_ALLOCATION:
        return "RESOURCE_ALLOCATION"
    else:
        return "UNKNOWN"


##########################################################################
# Define the state variables for the application
@dataclass
class AppStateVars:
    logger: Logger
    ue_map: UeContextsMap
    app: JrtcApp



###########################################################################################
# Class to handle reception of JSON message
###########################################################################################
class JsonUDPServer:

    def __init__(self, ip: str, port: int, state: AppStateVars):
        self.ip = ip
        self.port = port
        self.state = state
        self.running = True
        self.sock = None
        self.start_udp_server_thread()

    def start_udp_server_thread(self):
        self.state.logger.log_msg(True, False, "Dashboard", f"Starting UDP server thread")
        self.server_thread = threading.Thread(target=self.udp_server)
        self.server_thread.daemon = True  # Allows program to exit
        self.server_thread.start()

    def udp_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.ip, self.port))
            self.state.logger.log_msg(True, False, "Dashboard", f"UDP server listening on {self.ip}:{self.port}")

            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    if len(data) > 0:
                        self.json_handler_func(data.decode())
                except Exception as e:
                    print(f"JsonUDPServer: udp_server: error: {e}", flush=True)
        finally:
            if self.sock:
                self.sock.close()
                self.state.logger.log_msg(True, False, "Dashboard", "UDP server socket closed")

    def stop(self):
        self.running = False
        if self.sock:
            try:
                # Sending dummy data to unblock recvfrom
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b'', (self.ip, self.port))
                sock.close()
            except Exception:
                pass
        if self.server_thread:
            self.server_thread.join()
                

    ##########################################################################
    def json_handler_func(self, json_str: str) -> None:
        with app_lock:

            j = json.loads(json_str)

            context_type = j.get("context_type", None)
            event = j.get("event", None)
            if context_type is None or event is None:
                self.state.logger.log_msg(True, True, "Dashboard", f"Error: malformed message from Core {json_str}")
                return
            
            if context_type == "amf-ue":

                output = {
                    "timestamp": j.get("timestamp", 0),
                    "stream_index": "CORE-AMF-UE",
                    "core-msg": j
                }   

                self.state.logger.log_msg(True, True, "Dashboard", f"{output}")

                if event == "ran-ue-remove":

                    self.state.ue_map.hook_core_amf_info_remove(
                        suci=j.get("context", {}).get("suci", None),
                        supi=j.get("context", {}).get("supi", None),
                        home_plmn_id=j.get("context", {}).get("home_plmn_id", None),
                        current_guti_plmn=j.get("context", {}).get("current-guti", {}).get("plmn_id", None),
                        current_guti_amf_id=j.get("context", {}).get("current-guti", {}).get("amf_id", None),
                        current_guti_m_tmsi=j.get("context", {}).get("current-guti", {}).get("m_tmsi", None),
                        next_guti_plmn=j.get("context", {}).get("next-guti", {}).get("plmn_id", None),
                        next_guti_amf_id=j.get("context", {}).get("next-guti", {}).get("amf_id", None),
                        next_guti_m_tmsi=j.get("context", {}).get("next-guti", {}).get("m_tmsi", None),
                        tai_plmn=j.get("context", {}).get("nr_tai", {}).get("plmn_id", None),
                        tai_tac=j.get("context", {}).get("nr_tai", {}).get("tac", None),
                        cgi_plmn=j.get("context", {}).get("nr_cgi", {}).get("plmn_id", None),
                        cgi_cellid=j.get("context", {}).get("nr_cgi", {}).get("cell_id", None)
                    )

                else:

                    self.state.ue_map.hook_core_amf_info(
                        ran_ue_ngap_id=j.get("context", {}).get("ran_ue", {}).get("ran_ue_ngap_id", None),
                        amf_ue_ngap_id=j.get("context", {}).get("ran_ue", {}).get("amf_ue_ngap_id", None),
                        suci=j.get("context", {}).get("suci", None),
                        supi=j.get("context", {}).get("supi", None),
                        home_plmn_id=j.get("context", {}).get("home_plmn_id", None),
                        current_guti_plmn=j.get("context", {}).get("current-guti", {}).get("plmn_id", None),
                        current_guti_amf_id=j.get("context", {}).get("current-guti", {}).get("amf_id", None),
                        current_guti_m_tmsi=j.get("context", {}).get("current-guti", {}).get("m_tmsi", None),
                        next_guti_plmn=j.get("context", {}).get("next-guti", {}).get("plmn_id", None),
                        next_guti_amf_id=j.get("context", {}).get("next-guti", {}).get("amf_id", None),
                        next_guti_m_tmsi=j.get("context", {}).get("next-guti", {}).get("m_tmsi", None),
                        tai_plmn=j.get("context", {}).get("nr_tai", {}).get("plmn_id", None),
                        tai_tac=j.get("context", {}).get("nr_tai", {}).get("tac", None),
                        cgi_plmn=j.get("context", {}).get("nr_cgi", {}).get("plmn_id", None),
                        cgi_cellid=j.get("context", {}).get("nr_cgi", {}).get("cell_id", None)
                    )


##########################################################################
def app_handler(timeout: bool, stream_idx: int, data_entry: struct_jrtc_router_data_entry, state: AppStateVars):

    with app_lock:

        ##########################################################################
        # main part of function
        if timeout:

            ## timeout processing
            state.logger.process_timeout()

        else:
            
            output = {}

            # Check the stream index and process the data accordingly

            #####################################################
            ### Ue contexts

            if stream_idx == UECTX_DU_ADD_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__du_ue_ctx_creation)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_DU_ADD_SIDX))
                state.ue_map.hook_du_ue_ctx_creation(deviceid,
                                data.du_ue_index,    
                                data.plmn,
                                data.pci,
                                data.crnti,
                                data.tac,
                                data.nci)
                ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_DU_ADD",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                state.logger.log_msg(True, True, "Dashboard", f"{output}")
            
            elif stream_idx == UECTX_DU_UPDATE_CRNTI_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__du_ue_ctx_update_crnti)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_DU_UPDATE_CRNTI_SIDX))
                state.ue_map.hook_du_ue_ctx_update_crnti(deviceid, data.du_ue_index, data.crnti)

                ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_DU_UPDATE_CRNTI",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                if uectx is None:
                    output["du_ue_index"] = data.du_ue_index
                    output["rnti"] = data.rnti

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_DU_DEL_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__du_ue_ctx_deletion)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_DU_DEL_SIDX))

                ueid = state.ue_map.getid_by_du_index(deviceid, data.du_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_DU_DEL",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                if uectx is None:
                    output["du_ue_index"] = data.du_ue_index

                state.ue_map.hook_du_ue_ctx_deletion(deviceid, data.du_ue_index)

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUCP_ADD_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_creation)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUCP_ADD_SIDX))

                if data.has_pci and data.has_crnti:
                    state.ue_map.hook_cucp_uemgr_ue_add(
                                        deviceid,
                                        data.cucp_ue_index,    
                                        data.plmn,
                                        data.pci,
                                        data.crnti)

                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUCP_ADD",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUCP_UPDATE_CRNTI_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_update)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUCP_UPDATE_CRNTI_SIDX))
                state.ue_map.hook_cucp_uemgr_ue_add(
                                    deviceid,
                                    data.cucp_ue_index,    
                                    data.plmn,
                                    data.pci,
                                    data.crnti)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUCP_UPDATE_CRNTI",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUCP_DEL_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__cucp_ue_ctx_deletion)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUCP_DEL_SIDX))

                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUCP_DEL",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.ue_map.hook_cucp_uemgr_ue_remove(deviceid, data.cucp_ue_index)

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUCP_E1AP_BEARER_SETUP_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__e1ap_cucp_bearer_ctx_setup)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUCP_E1AP_BEARER_SETUP_SIDX))
                state.ue_map.hook_e1_cucp_bearer_context_setup(
                                    deviceid,
                                    data.cucp_ue_index, 
                                    data.cucp_ue_e1ap_id)
                
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUCP_E1AP_BEARER_SETUP",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }            

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUUP_E1AP_BEARER_SETUP_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__e1ap_cuup_bearer_ctx_setup)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUUP_E1AP_BEARER_SETUP_SIDX))
                state.ue_map.hook_e1_cuup_bearer_context_setup(
                                    deviceid,
                                    data.cuup_ue_index,
                                    data.cucp_ue_e1ap_id,
                                    data.cuup_ue_e1ap_id,
                                    data.success)

                ueid = state.ue_map.getid_by_cuup_index(deviceid, data.cuup_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUUP_E1AP_BEARER_SETUP",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict(),
                    "success": data.success,
                }            

                if uectx is None:
                    output["cuup_ue_index"] = data.cuup_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == UECTX_CUUP_E1AP_BEARER_DEL_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__e1ap_cuup_bearer_ctx_release)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, UECTX_CUUP_E1AP_BEARER_DEL_SIDX))

                ueid = state.ue_map.getid_by_cuup_index(deviceid, data.cuup_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "UECTX_CUUP_E1AP_BEARER_DEL_SIDX",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict(),
                    "success": data.success,
                }            

                if uectx is None:
                    output["cuup_ue_index"] = data.cuup_ue_index

                state.ue_map.hook_e1_cuup_bearer_context_release(
                                    deviceid,
                                    data.cuup_ue_index,
                                    data.cucp_ue_e1ap_id,
                                    data.cuup_ue_e1ap_id,
                                    data.success)

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            #####################################################
            ### Perf

            elif stream_idx == JBPF_STATS_REPORT_SIDX:
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
                if len(output["perfs"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")


            #####################################################
            ### RRC

            elif stream_idx == RRC_UE_ADD_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rrc_ue_add)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RRC_UE_ADD_SIDX))
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RRC_UE_ADD",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RRC_UE_PROCEDURE_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rrc_ue_procedure)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RRC_UE_PROCEDURE_SIDX))
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RRC_UE_PROCEDURE",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict(),
                    "procedure": rrc_procedure_to_str(data.procedure),
                    "success": data.success,
                    "meta": data.meta
                }

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RRC_UE_REMOVE_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rrc_ue_remove)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RRC_UE_REMOVE_SIDX))
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RRC_UE_REMOVE",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RRC_UE_UPDATE_CONTEXT_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rrc_ue_update_context)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RRC_UE_UPDATE_CONTEXT_SIDX))
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RRC_UE_UPDATE_CONTEXT",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict(),
                    "cucp_ue_index": data.cucp_ue_index,
                    "old_ue_index": data.old_ue_index,
                    "rnti": data.c_rnti,
                    "pci": data.pci,
                    "tac": data.tac,
                    "plmn": data.plmn,
                    "nci": data.nci
                }
                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RRC_UE_UPDATE_ID_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rrc_ue_update_id)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RRC_UE_UPDATE_ID_SIDX))
                state.ue_map.add_tmsi(deviceid, data.cucp_ue_index, data.tmsi)
                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RRC_UE_UPDATE_ID",
                    "ueid": ueid,
                    "ue_ctx": None if uectx is None else uectx.concise_dict()
                }

                if uectx is None:
                    output["cucp_ue_index"] = data.cucp_ue_index

                state.logger.log_msg(True, True, "Dashboard", f"{output}")


            #####################################################
            ### NGAP

            elif stream_idx == NGAP_PROCEDURE_STARTED_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__ngap_procedure_started)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, NGAP_PROCEDURE_STARTED_SIDX))
                
                state.ue_map.hook_ngap_procedure_started(deviceid, data.ue_ctx.cucp_ue_index, 
                                                     data.procedure,
                                                     data.ue_ctx.ran_ue_id, 
                                                     ngap_amf_ue_id = None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)

                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "NGAP_PROCEDURE_STARTED",
                    "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                    "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id,
                    "procedure": ngap_procedure_to_str(data.procedure)
                }

                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.ue_ctx.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)
                if uectx is not None:
                    output["ue_id"] = ueid
                    output["ue_ctx"] = None if uectx is None else uectx.concise_dict()

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == NGAP_PROCEDURE_COMPLETED_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__ngap_procedure_completed)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, NGAP_PROCEDURE_COMPLETED_SIDX))


                # if the procedure is not a context release, run it first, so that the UE will be updated
                if data.procedure != JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
                    state.ue_map.hook_ngap_procedure_completed(deviceid, data.ue_ctx.cucp_ue_index,
                                                            data.procedure,
                                                            data.success,
                                                            data.ue_ctx.ran_ue_id, 
                                                            data.ue_ctx.amf_ue_id)
                
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "NGAP_PROCEDURE_COMPLETED",
                    "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                    "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id,
                    "procedure": ngap_procedure_to_str(data.procedure),
                    "success": data.success
                }

                ueid = state.ue_map.getid_by_cucp_index(deviceid, data.ue_ctx.cucp_ue_index)
                uectx = state.ue_map.getuectx(ueid)
                if uectx is not None:
                    output["ue_id"] = ueid
                    output["ue_ctx"] = None if uectx is None else uectx.concise_dict()


                # if the procedure is a context release, run it now
                if data.procedure == JbpfNgapProcedure.NGAP_PROCEDURE_UE_CONTEXT_RELEASE:
                    state.ue_map.hook_ngap_procedure_completed(deviceid, data.ue_ctx.cucp_ue_index,
                                                            data.procedure,
                                                            data.success,
                                                            data.ue_ctx.ran_ue_id, 
                                                            data.ue_ctx.amf_ue_id)

                state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == NGAP_RESET_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__ngap_reset)
                )
                data = data_ptr.contents

                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, NGAP_RESET_SIDX))
             
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "NGAP_RESET",
                    "ngap_ran_ue_id": None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                    "ngap_amf_ue_id": None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id
                }

                ueid = state.ue_map.getid_by_ngap_ue_ids(
                            None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                            None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)
                uectx = state.ue_map.getuectx(ueid)
                if uectx is not None:
                    output["ue_id"] = ueid
                    output["ue_ctx"] = None if uectx is None else uectx.concise_dict()

                state.ue_map.hook_ngap_reset(deviceid, data.ue_ctx.cucp_ue_index, 
                                             ngap_ran_ue_id = None if data.ue_ctx.has_ran_ue_id is False else data.ue_ctx.ran_ue_id,
                                             ngap_amf_ue_id = None if data.ue_ctx.has_amf_ue_id is False else data.ue_ctx.amf_ue_id)

                state.logger.log_msg(True, True, "Dashboard", f"{output}")


            #####################################################
            ### RLC
            elif stream_idx == RLC_DL_NORTH_STATS_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rlc_dl_north_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RLC_DL_NORTH_STATS_SIDX))
                dl_north_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RLC_DL_NORTH_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in dl_north_stats:

                    report_stat = False

                    ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index) 
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s['du_ue_index']: stat.du_ue_index

                    if stat.sdu_new_bytes.count > 0:
                        s["sdu_new_bytes"] = {
                            "count": stat.sdu_new_bytes.count,
                            "total": stat.sdu_new_bytes.total
                        }
                        report_stat = True
                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RLC_DL_SOUTH_STATS_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rlc_dl_south_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RLC_DL_SOUTH_STATS_SIDX))
                dl_south_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RLC_DL_SOUTH_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in dl_south_stats:

                    report_stat = False

                    ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index) 
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s['du_ue_index']: stat.du_ue_index

                    if stat.pdu_window.count > 0:
                        s["pdu_window"] = {
                            "count": stat.pdu_window.count,
                            "total": stat.pdu_window.total,
                            "avg": stat.pdu_window.total / stat.pdu_window.count,
                            "min": stat.pdu_window.min,
                            "max": stat.pdu_window.max
                        }
                        report_stat = True

                    if stat.pdu_tx_bytes.count > 0:
                        s["pdu_tx_bytes"] = {
                            "count": stat.pdu_tx_bytes.count,
                            "total": stat.pdu_tx_bytes.total
                        }
                        report_stat = True

                    if stat.pdu_retx_bytes.count > 0:
                        s["pdu_retx_bytes"] = {
                            "count": stat.pdu_retx_bytes.count,
                            "total": stat.pdu_retx_bytes.total
                        }
                        report_stat = True

                    if stat.pdu_status_bytes.count > 0:
                        s["pdu_status_bytes"] = {
                            "count": stat.pdu_status_bytes.count,
                            "total": stat.pdu_status_bytes.total
                        }
                        report_stat = True

                    if stat.pdu_retx_count.count > 0:
                        s["pdu_retx_count"] = {
                            "count": stat.pdu_retx_count.count,
                            "total": stat.pdu_retx_count.total,
                            "avg": stat.pdu_retx_count.total / stat.pdu_retx_count.count,
                            "min": stat.pdu_retx_count.min,
                            "max": stat.pdu_retx_count.max
                        }
                        report_stat = True

                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == RLC_UL_STATS_SIDX:

                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__rlc_ul_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, RLC_UL_STATS_SIDX))
                ul_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "RLC_UL_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in ul_stats:

                    report_stat = False

                    ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index) 
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s['du_ue_index']: stat.du_ue_index

                    if stat.pdu_window.count > 0:
                        s["pdu_window"] = {
                            "count": stat.pdu_window.count,
                            "total": stat.pdu_window.total,
                            "avg": stat.pdu_window.total / stat.pdu_window.count,
                            "min": stat.pdu_window.min,
                            "max": stat.pdu_window.max
                        }
                        report_stat = True

                    if stat.pdu_bytes.count > 0:
                        s["pdu_bytes"] = {
                            "count": stat.pdu_bytes.count,
                            "total": stat.pdu_bytes.total
                        }
                        report_stat = True

                    if stat.sdu_delivered_bytes.count > 0:
                        s["sdu_delivered_bytes"] = {
                            "count": stat.sdu_delivered_bytes.count,
                            "total": stat.sdu_delivered_bytes.total,
                        }
                        report_stat = True

                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")


            #####################################################
            ### PDCP

            elif stream_idx == PDCP_DL_NORTH_STATS_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__dl_north_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, PDCP_DL_NORTH_STATS_SIDX))
                dl_north_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "PDCP_DL_NORTH_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in dl_north_stats:

                    report_stat = False

                    # if SRB: cu_ue_index means cucp_ue_index, else cu_ue_index means cuup_ue_index
                    if stat.is_srb:
                        ueid = state.ue_map.getid_by_cucp_index(deviceid, stat.cu_ue_index) 
                        ue_index_key = "cucp_ue_index"
                    else:
                        ueid = state.ue_map.getid_by_cuup_index(deviceid, stat.cu_ue_index)
                        ue_index_key = "cuup_ue_index"
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s[ue_index_key]: stat.cu_ue_index

                    if stat.sdu_bytes.count > 0:
                        s["sdu_bytes"] = {
                            "count": stat.sdu_bytes.count,
                            "total": stat.sdu_bytes.total,
                            "avg": stat.sdu_bytes.total / stat.sdu_bytes.count,
                            "min": stat.sdu_bytes.min,
                            "max": stat.sdu_bytes.max
                        }
                        report_stat = True
                    if stat.window.count > 0:
                        s["window"] = {
                            "count": stat.window.count,
                            "total": stat.window.total,
                            "avg": stat.window.total / stat.window.count,
                            "min": stat.window.min,
                            "max": stat.window.max
                        }
                        report_stat = True
                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == PDCP_DL_SOUTH_STATS_SIDX:

                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__dl_south_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, PDCP_DL_SOUTH_STATS_SIDX))
                dl_south_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "PDCP_DL_SOUTH_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in dl_south_stats:

                    report_stat = False

                    # if SRB: cu_ue_index means cucp_ue_index, else cu_ue_index means cuup_ue_index
                    if stat.is_srb:
                        ueid = state.ue_map.getid_by_cucp_index(deviceid, stat.cu_ue_index) 
                        ue_index_key = "cucp_ue_index"
                    else:
                        ueid = state.ue_map.getid_by_cuup_index(deviceid, stat.cu_ue_index)
                        ue_index_key = "cuup_ue_index"
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s[ue_index_key]: stat.cu_ue_index

                    # window stats
                    if stat.window.count > 0:
                        s["window"] = {
                            "count": stat.window.count,
                            "total": stat.window.total,
                            "avg": stat.window.total / stat.window.count,
                            "min": stat.window.min,
                            "max": stat.window.max
                        }
                        report_stat = True
                    # pdcp_tx_delay stats
                    if stat.pdcp_tx_delay.count > 0:
                        s["pdcp_tx_delay"] = {
                            "count": stat.pdcp_tx_delay.count,
                            "total": stat.pdcp_tx_delay.total,
                            "avg": stat.pdcp_tx_delay.total / stat.pdcp_tx_delay.count,
                            "min": stat.pdcp_tx_delay.min,
                            "max": stat.pdcp_tx_delay.max
                        }
                        report_stat = True
                    # rlc_tx_delay stats
                    if stat.rlc_tx_delay.count > 0:
                        s["rlc_tx_delay"] = {
                            "count": stat.rlc_tx_delay.count,
                            "total": stat.rlc_tx_delay.total,
                            "avg": stat.rlc_tx_delay.total / stat.rlc_tx_delay.count,
                            "min": stat.rlc_tx_delay.min,
                            "max": stat.rlc_tx_delay.max
                        }
                        report_stat = True
                    # rlc_deliv_delay stats
                    if stat.rlc_deliv_delay.count > 0:
                        s["rlc_deliv_delay"] = {
                            "count": stat.rlc_deliv_delay.count,
                            "total": stat.rlc_deliv_delay.total,
                            "avg": stat.rlc_deliv_delay.total / stat.rlc_deliv_delay.count,
                            "min": stat.rlc_deliv_delay.min,
                            "max": stat.rlc_deliv_delay.max
                        }
                        report_stat = True
                    # total_delay stats
                    if stat.total_delay.count > 0:
                        s["total_delay"] = {
                            "count": stat.total_delay.count,
                            "total": stat.total_delay.total,
                            "avg": stat.total_delay.total / stat.total_delay.count,
                            "min": stat.total_delay.min,
                            "max": stat.total_delay.max
                        }
                        report_stat = True
                    # tx_queue_bytes stats
                    if stat.tx_queue_bytes.count > 0:
                        s["tx_queue_bytes"] = {
                            "count": stat.tx_queue_bytes.count,
                            "total": stat.tx_queue_bytes.total,
                            "avg": stat.tx_queue_bytes.total / stat.tx_queue_bytes.count,
                            "min": stat.tx_queue_bytes.min,
                            "max": stat.tx_queue_bytes.max
                        }
                        report_stat = True
                    # tx_queue_pkt stats
                    if stat.tx_queue_pkt.count > 0:
                        s["tx_queue_pkt"] = {
                            "count": stat.tx_queue_pkt.count,
                            "total": stat.tx_queue_pkt.total,
                            "avg": stat.tx_queue_pkt.total / stat.tx_queue_pkt.count,
                            "min": stat.tx_queue_pkt.min,
                            "max": stat.tx_queue_pkt.max
                        }
                        report_stat = True
                    # sdu_tx_bytes stats
                    if stat.sdu_tx_bytes.count > 0:
                        s["sdu_tx_bytes"] = {
                            "count": stat.sdu_tx_bytes.count,
                            "total": stat.sdu_tx_bytes.total
                        }
                        report_stat = True
                    # sdu_retx_bytes stats
                    if stat.sdu_retx_bytes.count > 0:
                        s["sdu_retx_bytes"] = {
                            "count": stat.sdu_retx_bytes.count,
                            "total": stat.sdu_retx_bytes.total
                        }
                        report_stat = True
                    # sdu_discarded_bytes stats
                    if stat.sdu_discarded_bytes.count > 0:
                        s["sdu_discarded_bytes"] = {
                            "count": stat.sdu_discarded_bytes.count,
                            "total": stat.sdu_discarded_bytes.total,
                        }
                        report_stat = True

                    # Add the stat to the output
                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == PDCP_UL_STATS_SIDX:

                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__ul_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, PDCP_UL_STATS_SIDX))
                ul_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "PDCP_UL_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in ul_stats:

                    report_stat = False

                    # if SRB: cu_ue_index means cucp_ue_index, else cu_ue_index means cuup_ue_index
                    if stat.is_srb:
                        ueid = state.ue_map.getid_by_cucp_index(deviceid, stat.cu_ue_index) 
                        ue_index_key = "cucp_ue_index"
                    else:
                        ueid = state.ue_map.getid_by_cuup_index(deviceid, stat.cu_ue_index)
                        ue_index_key = "cuup_ue_index"
                    uectx = state.ue_map.getuectx(ueid)

                    s = {
                        "ueid": ueid,
                        "ue_ctx": None if uectx is None else uectx.concise_dict(),
                        "is_srb": stat.is_srb,
                        "rb_id": stat.rb_id
                    }

                    if uectx is None:
                        s[ue_index_key]: stat.cu_ue_index

                    # window stats
                    if stat.window.count > 0:
                        s["window"] = {
                            "count": stat.window.count,
                            "total": stat.window.total,
                            "avg": stat.window.total / stat.window.count,
                            "min": stat.window.min,
                            "max": stat.window.max
                        }
                        report_stat = True
                    # sdu_bytes stats
                    if stat.sdu_bytes.count > 0:
                        s["sdu_bytes"] = {
                            "count": stat.sdu_bytes.count,
                            "total": stat.sdu_bytes.total,
                            "avg": stat.sdu_bytes.total / stat.sdu_bytes.count,
                            "min": stat.sdu_bytes.min,
                            "max": stat.sdu_bytes.max
                        }
                        report_stat = True

                    if report_stat:
                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break

                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")



            #####################################################
            ### MAC

            elif stream_idx == MAC_SCHED_CRC_STATS_SIDX:
                
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__crc_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, MAC_SCHED_CRC_STATS_SIDX))
                crc_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "MAC_SCHED_CRC_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in crc_stats:
                    if stat.cnt_tx > 0:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s ={
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "cons_min": stat.cons_min,
                            "cons_max": stat.cons_max,
                            "succ_rate": stat.succ_tx / stat.cnt_tx,
                            "min_sinr": stat.min_sinr,
                            "min_rsrp": stat.min_rsrp,
                            "max_sinr": stat.max_sinr,
                            "max_rsrp": stat.max_rsrp,
                            "avg_sinr": stat.sum_sinr / stat.cnt_sinr,
                            "avg_rsrp": stat.sum_rsrp / stat.cnt_rsrp
                        }
                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index,

                        output["stats"].append(s)
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

            elif stream_idx == MAC_SCHED_BSR_STATS_SIDX:

                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__bsr_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, MAC_SCHED_BSR_STATS_SIDX))
                bsr_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "MAC_SCHED_BSR_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in bsr_stats:
                    if  stat.cnt > 0:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "cnt": stat.cnt
                        }
                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index
                                                
                        output["stats"].append(s)                    
        
                        cnt += 1
                        if cnt >= data.stats_count:
                            break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")
    
            elif stream_idx == MAC_SCHED_PHR_STATS_SIDX:
                data_ptr = ctypes.cast(
                    data_entry.data, ctypes.POINTER(struct__phr_stats)
                )
                data = data_ptr.contents
                deviceid = str(jrtc_app_router_stream_id_get_device_id(state.app, MAC_SCHED_PHR_STATS_SIDX))
                phr_stats = list(data.stats)
                output = {
                    "timestamp": data.timestamp,
                    "stream_index": "MAC_SCHED_PHR_STATS",
                    "stats": []
                }
                cnt = 0
                for stat in phr_stats:
                    if stat.ph_max > 0:
                        ueid = state.ue_map.getid_by_du_index(deviceid, stat.du_ue_index)
                        uectx = state.ue_map.getuectx(ueid)
                        s = {
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "serv_cell_id": stat.serv_cell_id,
                            "ph_min": stat.ph_min,
                            "ph_max": stat.ph_max,
                            "p_cmax_min": stat.p_cmax_min,
                            "p_cmax_max": stat.p_cmax_max
                        }

                        if uectx is None:
                            s["du_ue_index"] = stat.du_ue_index
                                                
                        output["stats"].append(s)           

                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["stats"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")



            #####################################################
            ### FAPI

            elif stream_idx == FAPI_DL_CONFIG_SIDX:
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
                        ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                        uectx = state.ue_map.getuectx(ueid)
                        s = {
                            "cell_id": stat.cell_id,
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
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
                        }

                        if uectx is None:
                            s["rnti"] = stat.rnti
                                                
                        output["ues"].append(s)                    
                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["ues"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

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
                        ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                        uectx = state.ue_map.getuectx(ueid)
                        s = {
                            "cell_id": stat.cell_id,
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
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
                        }

                        if uectx is None:
                            s["rnti"] = stat.rnti
                                                
                        output["ues"].append(s)   

                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["ues"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

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
                        ueid = state.ue_map.getid_by_pci_rnti(stat.cell_id, stat.rnti)                    
                        uectx = state.ue_map.getuectx(ueid)
                        s = {
                            "cell_id": stat.cell_id,
                            "ueid": ueid,
                            "ue_ctx": None if uectx is None else uectx.concise_dict(),
                            "l1_crc_ta_hist": list(stat.l1_crc_ta_hist),
                            "l1_crc_snr_hist": list(stat.l1_crc_snr_hist),
                            "l1_ta_min": stat.l1_ta_min,
                            "l1_ta_max": stat.l1_ta_max,
                            "l1_snr_min": stat.l1_snr_min,
                            "l1_snr_max": stat.l1_snr_max
                        }

                        if uectx is None:
                            s["rnti"] = stat.rnti
                                                
                        output["ues"].append(s)   

                    cnt += 1
                    if cnt >= data.stats_count:
                        break
                if len(output["ues"]) > 0:
                    state.logger.log_msg(True, True, "Dashboard", f"{output}")

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
                state.logger.log_msg(True, True, "Dashboard", f"{output}")


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

                state.logger.log_msg(True, False, "", "****----------------------------")
                state.logger.log_msg(True, False, "", f"*Hi App 1: timestamp: {data.timestamp}")
                state.logger.log_msg(True, False, "", f"*DL Ctl: {dl_control_stats.Packet_count} {list(dl_control_stats.packet_inter_arrival_info.hist)}")
                state.logger.log_msg(True, False, "", f"*DL Data: {dl_data_stats.Packet_count} {dl_data_stats.Prb_count} {list(dl_data_stats.packet_inter_arrival_info.hist)}")


            else:
                state.logger.log_msg(True, False, "", f"Unknown stream index: {stream_idx}")
                output = {
                    "stream_index": stream_idx,
                    "error": "Unknown stream index"
                }

                # Send the output to the dashboard
                state.logger.log_msg(True, True, "Dashboard", f"{output}")



##########################################################################
# Main function to start the app (converted from jrtc_start_app)
def jrtc_start_app(capsule):

    global UECTX_DU_ADD_SIDX
    global UECTX_DU_UPDATE_CRNTI_SIDX
    global UECTX_DU_DEL_SIDX
    global UECTX_CUCP_ADD_SIDX
    global UECTX_CUCP_UPDATE_CRNTI_SIDX 
    global UECTX_CUCP_DEL_SIDX
    global UECTX_CUCP_E1AP_BEARER_SETUP_SIDX 
    global UECTX_CUUP_E1AP_BEARER_SETUP_SIDX
    global UECTX_CUUP_E1AP_BEARER_DEL_SIDX
    global MAC_SCHED_CRC_STATS_SIDX
    global MAC_SCHED_BSR_STATS_SIDX
    global MAC_SCHED_PHR_STATS_SIDX
    global RLC_DL_NORTH_STATS_SIDX
    global RLC_DL_SOUTH_STATS_SIDX
    global RLC_UL_STATS_SIDX
    global PDCP_DL_NORTH_STATS_SIDX
    global PDCP_DL_SOUTH_STATS_SIDX
    global PDCP_UL_STATS_SIDX
    global RRC_UE_ADD_SIDX
    global RRC_UE_PROCEDURE_SIDX
    global RRC_UE_REMOVE_SIDX
    global RRC_UE_UPDATE_CONTEXT_SIDX
    global RRC_UE_UPDATE_ID_SIDX 
    global NGAP_PROCEDURE_STARTED_SIDX
    global NGAP_PROCEDURE_COMPLETED_SIDX
    global NGAP_RESET_SIDX
    global FAPI_DL_CONFIG_SIDX 
    global FAPI_UL_CONFIG_SIDX 
    global FAPI_CRC_STATS_SIDX 
    global FAPI_RACH_STATS_SIDX 
    global JBPF_STATS_REPORT_SIDX
    global XRAN_CODELET_OUT_SIDX

    UECTX_DU_ADD_SIDX = -1
    UECTX_DU_UPDATE_CRNTI_SIDX = -1
    UECTX_DU_DEL_SIDX = -1
    UECTX_CUCP_ADD_SIDX = -1
    UECTX_CUCP_UPDATE_CRNTI_SIDX = -1
    UECTX_CUCP_DEL_SIDX = -1
    UECTX_CUCP_E1AP_BEARER_SETUP_SIDX = -1
    UECTX_CUUP_E1AP_BEARER_SETUP_SIDX = -1
    UECTX_CUUP_E1AP_BEARER_DEL_SIDX = -1
    MAC_SCHED_CRC_STATS_SIDX = -1
    MAC_SCHED_BSR_STATS_SIDX = -1
    MAC_SCHED_PHR_STATS_SIDX = -1
    RLC_DL_NORTH_STATS_SIDX = -1
    RLC_DL_SOUTH_STATS_SIDX = -1
    RLC_UL_STATS_SIDX = -1
    PDCP_DL_NORTH_STATS_SIDX = -1
    PDCP_DL_SOUTH_STATS_SIDX = -1
    PDCP_UL_STATS_SIDX = -1
    RRC_UE_ADD_SIDX = -1
    RRC_UE_PROCEDURE_SIDX = -1
    RRC_UE_REMOVE_SIDX = -1
    RRC_UE_UPDATE_CONTEXT_SIDX = -1
    RRC_UE_UPDATE_ID_SIDX = -1
    NGAP_PROCEDURE_STARTED_SIDX = -1
    NGAP_PROCEDURE_COMPLETED_SIDX = -1
    NGAP_RESET_SIDX = -1
    FAPI_DL_CONFIG_SIDX = -1
    FAPI_UL_CONFIG_SIDX = -1
    FAPI_CRC_STATS_SIDX = -1
    FAPI_RACH_STATS_SIDX = -1
    JBPF_STATS_REPORT_SIDX = -1
    XRAN_CODELET_OUT_SIDX = -1

    last_cnt = 0

    streams = []

    la_workspace_id = os.environ.get("LA_WORKSPACE_ID", "")
    la_primary_key = os.environ.get("LA_PRIMARY_KEY", "")

    if la_workspace_id == "" or la_primary_key == "":
        print("Log Analytics workspace ID or primary key not set. Using local logger only.", flush=True)
        la_logger = None
    else:
        print("Log Analytics workspace ID and primary key are set. Will do remote logging to Log Analytics.", flush=True)
        # Create the Log Analytics logger
        la_logger = LaLogger(
            LaLoggerConfig(
                "jrtc_dashboard",  # Log type
                la_workspace_id,         
                la_primary_key,         
                100,          # 100 packets per batch
                1024 * 1024,  # 1 MB per batch
                5             # Timeout for batch sending (5 seconds)
            ), 
            dbg=False
        )

    stream_id = "dashboard"
    stream_type = "dashboard"

    # TODO: pass hostname into JRTC pod
    hostname = ""

    # Initialize the app
    
    state = AppStateVars(
        logger=Logger(hostname, stream_id, stream_type, remote_logger=la_logger),
        ue_map=UeContextsMap(dbg=False) if include_ue_contexts else None, 
        app=None)
    

    #####################################################
    ### UE contexts

    if include_ue_contexts:

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_creation", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_ADD_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_ADD_SIDX: {UECTX_DU_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_update_crnti", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_UPDATE_CRNTI_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_UPDATE_CRNTI_SIDX: {UECTX_DU_UPDATE_CRNTI_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/du_ue_ctx_deletion", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_DU_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_DU_DEL_SIDX: {UECTX_DU_DEL_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_add", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_ADD_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_ADD_SIDX: {UECTX_CUCP_ADD_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_update", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_UPDATE_CRNTI_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_UPDATE_CRNTI_SIDX: {UECTX_CUCP_UPDATE_CRNTI_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/cucp_uemgr_ue_remove", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_DEL_SIDX: {UECTX_CUCP_DEL_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cucp_bearer_context_setup", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUCP_E1AP_BEARER_SETUP_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUCP_E1AP_BEARER_SETUP_SIDX: {UECTX_CUCP_E1AP_BEARER_SETUP_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cuup_bearer_context_setup", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUUP_E1AP_BEARER_SETUP_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUUP_E1AP_BEARER_SETUP_SIDX: {UECTX_CUUP_E1AP_BEARER_SETUP_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ue_contexts/e1_cuup_bearer_context_release", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        UECTX_CUUP_E1AP_BEARER_DEL_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"UECTX_CUUP_E1AP_BEARER_DEL_SIDX: {UECTX_CUUP_E1AP_BEARER_DEL_SIDX}")
        last_cnt += 1



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
        state.logger.log_msg(True, False, "", f"JBPF_STATS_REPORT_SIDX: {JBPF_STATS_REPORT_SIDX}")
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
        state.logger.log_msg(True, False, "", f"RRC_UE_ADD_SIDX: {RRC_UE_ADD_SIDX}")
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
        state.logger.log_msg(True, False, "", f"RRC_UE_PROCEDURE_SIDX: {RRC_UE_PROCEDURE_SIDX}")
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
        state.logger.log_msg(True, False, "", f"RRC_UE_REMOVE_SIDX: {RRC_UE_REMOVE_SIDX}")
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
        state.logger.log_msg(True, False, "", f"RRC_UE_UPDATE_CONTEXT_SIDX: {RRC_UE_UPDATE_CONTEXT_SIDX}")
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
        state.logger.log_msg(True, False, "", f"RRC_UE_UPDATE_ID_SIDX: {RRC_UE_UPDATE_ID_SIDX}")
        last_cnt += 1



    #####################################################
    ### NGAP

    if include_ngap:
    
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_procedure_started", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_PROCEDURE_STARTED_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_PROCEDURE_STARTED_SIDX: {NGAP_PROCEDURE_STARTED_SIDX}")
        last_cnt += 1    

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_procedure_completed", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_PROCEDURE_COMPLETED_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_PROCEDURE_COMPLETED_SIDX: {NGAP_PROCEDURE_COMPLETED_SIDX}")
        last_cnt += 1    

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/ngap/ngap_reset", 
                b"output_map"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        NGAP_RESET_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"NGAP_RESET_SIDX: {NGAP_RESET_SIDX}")
        last_cnt += 1



    #####################################################
    ### RLC

    if include_rlc:
        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rlc_stats/rlc_collect", 
                b"output_map_dl_north"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RLC_DL_NORTH_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RLC_DL_NORTH_STATS_SIDX: {RLC_DL_NORTH_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rlc_stats/rlc_collect", 
                b"output_map_dl_south"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RLC_DL_SOUTH_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RLC_DL_SOUTH_STATS_SIDX: {RLC_DL_SOUTH_STATS_SIDX}")
        last_cnt += 1

        streams.append(JrtcStreamCfg_t(
            JrtcStreamIdCfg_t(
                JRTC_ROUTER_REQ_DEST_ANY, 
                JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                b"dashboard://jbpf_agent/rlc_stats/rlc_collect", 
                b"output_map_ul"),
            True,   # is_rx
            None    # No AppChannelCfg 
        ))
        RLC_UL_STATS_SIDX = last_cnt
        state.logger.log_msg(True, False, "", f"RLC_UL_STATS_SIDX: {RLC_UL_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"PDCP_DL_NORTH_STATS_SIDX: {PDCP_DL_NORTH_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"PDCP_DL_SOUTH_STATS_SIDX: {PDCP_DL_SOUTH_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"PDCP_UL_STATS_SIDX: {PDCP_UL_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"MAC_SCHED_CRC_STATS_SIDX: {MAC_SCHED_CRC_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"MAC_SCHED_BSR_STATS_SIDX: {MAC_SCHED_BSR_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"MAC_SCHED_PHR_STATS_SIDX: {MAC_SCHED_PHR_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"FAPI_DL_CONFIG_SIDX: {FAPI_DL_CONFIG_SIDX}")
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
        state.logger.log_msg(True, False, "", f"FAPI_UL_CONFIG_SIDX: {FAPI_UL_CONFIG_SIDX}")
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
        state.logger.log_msg(True, False, "", f"FAPI_CRC_STATS_SIDX: {FAPI_CRC_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"FAPI_RACH_STATS_SIDX: {FAPI_RACH_STATS_SIDX}")
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
        state.logger.log_msg(True, False, "", f"XRAN_CODELET_OUT_SIDX: {XRAN_CODELET_OUT_SIDX}")
        last_cnt += 1

    app_cfg = JrtcAppCfg_t(
        b"dashboard",                                  # context
        100,                                           # q_size
        len(streams),                                  # num_streams
        (JrtcStreamCfg_t * len(streams))(*streams),    # streams
        10.0,                                          # initialization_timeout_secs
        0.25,                                          # sleep_timeout_secs
        2.0                                            # inactivity_timeout_secs
    )

    state.app = jrtc_app_create(capsule, app_cfg, app_handler, state)

    state.logger.log_msg(True, True, "Unstructured", f"Number of subscribed streams: {len(streams)}")

    # start thread for json port
    json_udp_server = JsonUDPServer("0.0.0.0", 20790, state)

    # run the app - This is blocking until the app exists
    jrtc_app_run(state.app)

    json_udp_server.stop()

    # clean up app resources
    jrtc_app_destroy(state.app)

