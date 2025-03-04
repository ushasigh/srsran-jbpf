# Copyright (c) Microsoft Corporation. All rights reserved.

import time
import os
import sys
import ctypes
from typing import Any
from dataclasses import dataclass


JRTC_PYTHON_INC = os.environ.get("JRTC_PYTHON_INC")
if JRTC_PYTHON_INC is None:
    raise ValueError("JRTC_PYTHON_INC not set")
sys.path.append(f"{JRTC_PYTHON_INC}")

import jrtc_app
from jrtc_app import *

JRTC_PATH = f'{os.environ.get("JRTC_PATH")}'
if JRTC_PATH is None:
    raise ValueError("JRTC_PATH not set")


JBPF_CODELETS = os.environ.get("JBPF_CODELETS")
if JBPF_CODELETS is None:
    raise ValueError("JBPF_CODELETS not set")
PROTO_PATH = f'{JBPF_CODELETS}/xran_packets'
sys.path.append(PROTO_PATH)
from xran_packet_info import struct__packet_stats


########################################################
# state variables
########################################################
@dataclass
class AppStateVars:
    wrapper: JrtcPythonApp


# ######################################################
# # Main function called from JRTC core
def jrtc_start_app(capsule):

    XRAN_CODELET_OUT_SIDX = 0

    ########################################################
    # configuration
    ########################################################
    app_cfg = AppCfg(
        context="xran_packets",
        q_size=100, 
        streams=[
            # XRAN_CODELET_OUT_SIDX
            StreamCfg(
                sid=StreamIdCfg(
                    destination=JRTC_ROUTER_REQ_DEST_ANY, 
                    device_id=JRTC_ROUTER_REQ_DEVICE_ID_ANY, 
                    stream_source="xran_packets_deployment://jbpf_agent/xran_packets/reporter", 
                    io_map="output_map"),
                is_rx=True
            )
        ], 
        sleep_timeout_secs=0.25,
        inactivity_timeout_secs=2.0
    )

    ########################################################
    # message handler
    ########################################################
    def app_handler(timeout: bool, stream_idx: int, data_entry: struct_jrtc_router_data_entry, state: AppStateVars) -> None:

        if timeout:

            ## timeout processing

            pass

        elif stream_idx == XRAN_CODELET_OUT_SIDX:

            data_ptr = ctypes.cast(
                data_entry.data, ctypes.POINTER(struct__packet_stats)
            )

            data = data_ptr.contents
            ul_data_stats = data.ul_packet_stats.data_packet_stats
            dl_data_stats = data.dl_packet_stats.data_packet_stats
            dl_control_stats = data.dl_packet_stats.ctrl_packet_stats

            print("----------------------------")
            print(f"Hi App 1: timestamp: {data.timestamp}")
            print(f"DL Ctl: {dl_control_stats.Packet_count} {list(dl_control_stats.packet_inter_arrival_info.hist)}")
            print(f"DL Data: {dl_data_stats.Packet_count} {dl_data_stats.Prb_count} {list(dl_data_stats.packet_inter_arrival_info.hist)}")

        else:
            pass

    ########################################################
    # App execution handler
    ########################################################
    state = AppStateVars(wrapper=None)
    state.wrapper = JrtcPythonApp(capsule, app_cfg, app_handler, state)
    state.wrapper.run()
