# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
#
# This codelet simply forwards the message.
#
#
# UE Indexing Across Subsystems
#
# This comment outlines how UE (User Equipment) indexes are managed and tracked across 
# various subsystems (DU, CU-CP, and CU-UP).
#
# All functions invoked as hooks for UE-specific operations will include a "UE index".
# However, the DU, CU-CP, and CU-UP subsystems manage their UE indexes independently.
# As a result, the same UE may have different index values in each subsystem.
#
# To clarify this in the code, the context structures use the following field names:
#     - du_index
#     - cu_cp_index
#     - cu_up_index
#
# Mapping UE indexes across subsystems involves the following conventions:
#
# DU (Distributed Unit):
# -----------------------
# The function `du_ue_ctx_creation` is called when a UE is created at the DU.
# Parameters:
#     - du_index
#     - plmn
#     - nci
#     - pci
#     - tac
#     - crnti
#
# CU-CP (Central Unit - Control Plane):
# -------------------------------------
# The function `cucp_uemgr_ue_add` is called when a UE is created at the CU-CP.
# Parameters:
#     - cu_cp_index
#     - plmn
#     - pci
#     - rnti
#
# The `cu_cp_index` can be mapped to a `du_index` based on matching (plmn, pci, rnti).
#
# CU-UP (Central Unit - User Plane):
# ----------------------------------
# The UE context in the CU-UP is set up via the E1AP Bearer Setup procedure.
# The following hooks are invoked:
#
#     - `e1_cucp_bearer_context_setup`
#         Parameters: cu_cp_index, gnb_cu_cp_ue_e1ap_id
#
#     - `e1_cuup_bearer_context_setup`
#         Parameters: cu_cp_index, gnb_cu_cp_ue_e1ap_id, gnb_cu_up_ue_e1ap_id
#
# Mapping details:
#     - `gnb_cu_cp_ue_e1ap_id` corresponds to `cu_cp_index`
#     - (`gnb_cu_cp_ue_e1ap_id`, `gnb_cu_up_ue_e1ap_id`) together identify the `cu_up_index`
#
# PDCP (Packet Data Convergence Protocol):
# ----------------------------------------
# PDCP hooks are invoked in both CU-CP (for SRBs) and CU-UP (for DRBs), and share a unified 
# context structure:
#
#     struct jbpf_pdcp_ctx_info {
#         uint16_t ctx_id;       # Context ID (implementation specific)
#         uint32_t cu_index;  # SRB: cu_cp_index, DRB: cu_up_index
#         uint8_t  is_srb;       # true = SRB, false = DRB
#         uint8_t  rb_id;        # SRB: 0=srb0, 1=srb1, 2=srb2
#                                # DRB: 1=drb1, 2=drb2, 3=drb3, etc.
#         uint8_t  rlc_mode;     # 0 = UM, 1 = AM
#     }
#
# Notes:
#     - In CU-CP, hooks are called for SRBs. Thus, `cu_index` refers to `cu_cp_index`.
#     - In CU-UP, hooks are called for DRBs. Thus, `cu_index` refers to `cu_up_index`.
#
# Example hook flow ...
#
#   hook_du_ue_ctx_creation: du_index 0 tac 1 nrcgi=[ plmn=61712 nci=6733824 ] pci 1 tc_rnti 17922
#   hook_cucp_uemgr_ue_add: cu_cp_index 1 plmn 00101 pci=1 rnti=17922
#   hook_pdcp_dl_creation: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_creation: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_e1_cucp_bearer_context_setup, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1
#   hook_pdcp_dl_creation: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_pdcp_ul_creation: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_e1_cuup_bearer_context_setup success, cu_up_index 0  gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_e1_cucp_bearer_context_modification, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_e1_cuup_bearer_context_modification success cu_up_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_pdcp_dl_creation: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_creation: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_e1_cucp_bearer_context_release, cu_cp_index=1 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_pdcp_ul_deletion: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_pdcp_dl_deletion: cu_index 0 drb=1 rlc_mode 1    ==> since it is DRB, cu_index represents cu_up_index
#   hook_e1_cuup_bearer_context_release success cu_up_index=0 gnb_cu_cp_ue_e1ap_id=1 gnb_cu_up_ue_e1ap_id=1
#   hook_du_ue_ctx_deletion: du_index 0
#   hook_pdcp_ul_deletion: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_dl_deletion: cu_index 1 srb=2 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_ul_deletion: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_pdcp_dl_deletion: cu_index 1 srb=1 rlc_mode 1    ==> since it is SRB, cu_index represents cu_cp_index
#   hook_cucp_uemgr_ue_remove: cu_cp_index 1
#

import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple


##########################################
@dataclass
class ue_context:
    du_index: int
    cucp_index: int
    cuup_index: int
    plmn: int
    nci: int
    pci: int
    tac: int
    crnti: int
    e1_bearers: List[Tuple[int, int]]     # tuple of (cucp_ue_e1ap_id, cuup_ue_e1ap_id)
    
    def __init__(self, plmn: int, pci: int, crnti: int, du_index: int=None, cucp_index: int=None, cuup_index: int=None,
                 nci: int=None, tac: int=None):
        self.plmn = plmn
        self.pci = pci
        self.crnti = crnti
        # optional
        self.nci = nci
        self.tac = tac
        self.du_index = du_index
        self.cucp_index = cucp_index
        self.cuup_index = cuup_index
        self.e1_bearers = []
        print(f"UEContext created: {self}")

    def used(self) -> bool:
        """
        Check if the UE context is used.
        :return: True if the context is used, False otherwise.
        """
        if self.du_index is not None:
            return True
        if self.cucp_index is not None:
            return True
        if (self.cuup_index is not None) and (len(self.e1_bearers) > 0):
            return True
        return False

    def get_bearer(self, cucp_ue_e1ap_id: int) -> (int, int):
        for bearer in self.e1_bearers:
            if bearer[0] == cucp_ue_e1ap_id:
                return bearer
        return None, None
        
    def __del__(self):
        print(f"UEContext deleted: {self}")

    def __str__(self):
        return (f"UEContext(du_index={self.du_index}, "
                f"cucp_index={self.cucp_index}, cuup_index={self.cuup_index}, "
                f"plmn={self.plmn}, nci={self.nci}, pci={self.pci}, "
                f"tac={self.tac}, crnti={self.crnti}, "
                f"e1_bearers={self.e1_bearers})")


###########################################################################################################
class srsRAN_UEContexts:
    """
    This class is used to manage UE contexts in the srsRAN system.
    It provides methods to create, delete, and modify UE contexts.
    """

    ####################################################################
    def __init__(self, dbg: bool=False):
        self.dbg = dbg
        self.context_id = 0       # will just increase by 1 for each new context.  No need to handle wrap as we'll never reach that
        self.contexts = {}
        self.contexts_by_du_index = {}
        self.contexts_by_cucp_index = {}
        self.contexts_by_cuup_index = {}
        self.contexts_by_cucp_ue_e1ap_id = {}
        self.contexts_by_cuup_ue_e1ap_id = {}

    ####################################################################
    def context_create(self, plmn: int, pci: int, crnti: int, du_index: int=None, cucp_index: int=None, cuup_index: int=None,
        nci: int=None, tac: int=None) -> None:
        if self.dbg:
            print(f"context_create: plmn={plmn} pci={pci} crnti={crnti} du_index={du_index} cucp_index={cucp_index} cuup_index={cuup_index} nci={nci} tac={tac}")
        ue = ue_context(plmn, pci, crnti, du_index=du_index, cucp_index=cucp_index, cuup_index=cuup_index, nci=nci, tac=tac)
        # add mappings
        self.contexts[self.context_id] = ue
        if ue.du_index is not None:
            self.set_du_index(self.context_id, du_index)
        if ue.cucp_index is not None:
            self.set_cucp_index(self.context_id, cucp_index)
        if ue.cuup_index is not None:
            self.set_cuup_index(self.context_id, cuup_index)
        # increment context id for next context
        self.context_id += 1

    ####################################################################
    def context_delete(self, ue_id: int) -> None:
        if self.dbg:
            print(f"context_delete: ue_id={ue_id}")
        if ue_id in self.contexts:
            ue = self.contexts[ue_id]
            # Also remove from the other mappings
            self.contexts_by_du_index.pop(ue.du_index, None)
            self.contexts_by_cucp_index.pop(ue.cucp_index, None)
            self.contexts_by_cuup_index.pop(ue.cuup_index, None)
            for b in ue.e1_bearers:
                self.contexts_by_cucp_ue_e1ap_id.pop(b[0], None)
                self.contexts_by_cuup_ue_e1ap_id.pop(b[1], None)
            # remove context
            self.contexts.pop(ue_id, None)

    ####################################################################
    def delete_unused_context(self, ue_id: int) -> None:
        if self.dbg:
            print(f"delete_unused_context: ue_id={ue_id}")
        if ue_id in self.contexts:
            if self.contexts[ue_id].used():
                return
            self.contexts.pop(ue_id, None)

    ####################################################################
    def set_du_index(self, ue_id: int, du_index: int) -> None:
        if self.dbg:
            print(f"set_du_index: ue_id={ue_id} du_index={du_index}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        self.contexts[ue_id].du_index = du_index
        self.contexts_by_du_index[du_index] = ue_id

    ####################################################################
    def clear_du_index(self, ue_id: int) -> None:
        if self.dbg:
            print(f"clear_du_index: ue_id={ue_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        du_index = self.contexts[ue_id].du_index
        self.contexts[ue_id].du_index = None
        self.contexts_by_du_index.pop(du_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cucp_index(self, ue_id: int, cucp_index: int) -> None:
        if self.dbg:
            print(f"set_cucp_index: ue_id={ue_id} cucp_index={cucp_index}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        self.contexts[ue_id].cucp_index = cucp_index
        self.contexts_by_cucp_index[cucp_index] = ue_id

    ####################################################################
    def clear_cucp_index(self, ue_id: int) -> None:
        if self.dbg:
            print(f"clear_cucp_index: ue_id={ue_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        cucp_index = self.contexts[ue_id].cucp_index
        self.contexts[ue_id].cucp_index = None
        self.contexts_by_cucp_index.pop(cucp_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cuup_index(self, ue_id: int, cuup_index: int) -> None:
        if self.dbg:
            print(f"set_cuup_index: ue_id={ue_id} cuup_index={cuup_index}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        self.contexts[ue_id].cuup_index = cuup_index
        self.contexts_by_cuup_index[cuup_index] = ue_id

    ####################################################################
    def clear_cuup_index(self, ue_id: int) -> None:
        if self.dbg:
            print(f"clear_cuup_index: ue_id={ue_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        cuup_index = self.contexts[ue_id].cuup_index
        self.contexts[ue_id].cuup_index = None
        self.contexts_by_cuup_index.pop(cuup_index, None)
        self.delete_unused_context(ue_id)

    ####################################################################
    def set_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: int) -> None:
        if self.dbg:
            print(f"set_cucp_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        bearer = (cucp_ue_e1ap_id, None)
        self.contexts[ue_id].e1_bearers.append(bearer)
        self.contexts_by_cucp_ue_e1ap_id[cucp_ue_e1ap_id] = ue_id

    ####################################################################
    def clear_cucp_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: int) -> None:
        if self.dbg: 
            print(f"clear_cucp_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        
        # remove the bearer with the matching cucp_ue_e1ap_id
        bearer = None
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[0] == cucp_ue_e1ap_id:
                bearer = self.contexts[ue_id].e1_bearers.pop(i)
                
        if bearer is not None:
            self.contexts_by_cucp_ue_e1ap_id.pop(bearer[0], None)
            self.contexts_by_cuup_ue_e1ap_id.pop(bearer[1], None)
            # if no more bearers are present, remove the cuup_index too
            if len(self.contexts[ue_id].e1_bearers) == 0:
                self.clear_cuup_index(ue_id)
            self.delete_unused_context(ue_id)
        

    ####################################################################
    def set_cuup_ue_e1ap_id(self, ue_id: int, cucp_ue_e1ap_id: int, cuup_ue_e1ap_id: int) -> None:
        if self.dbg:
            print(f"set_cuup_ue_e1ap_id: ue_id={ue_id} cucp_ue_e1ap_id={cucp_ue_e1ap_id} cuup_ue_e1ap_id={cuup_ue_e1ap_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        
        # update the bearer with the matching cucp_ue_e1ap_id with the cuup_ue_e1ap_id
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[0] == cucp_ue_e1ap_id:
                self.contexts[ue_id].e1_bearers[i] = (b[0], cuup_ue_e1ap_id)
                break
        else:
            print(f"Bearer with cucp_ue_e1ap_id {cucp_ue_e1ap_id} not found in UE context {ue_id}.")
            return
        self.contexts_by_cuup_ue_e1ap_id[cuup_ue_e1ap_id] = ue_id

    ####################################################################
    def clear_cuup_ue_e1ap_id(self, ue_id: int, cuup_ue_e1ap_id: int) -> None:
        if self.dbg:
            print(f"clear_cuup_ue_e1ap_id: ue_id={ue_id} cuup_ue_e1ap_id={cuup_ue_e1ap_id}")
        if ue_id not in self.contexts:
            print(f"UE context with ID {ue_id} does not exist.")
            return
        
        # remove the bearer with the matching cuup_ue_e1ap_id
        bearer = None
        for i, b in enumerate(self.contexts[ue_id].e1_bearers):
            if b[1] == cuup_ue_e1ap_id:
                bearer = self.contexts[ue_id].e1_bearers.pop(i)

        if bearer is not None:
            self.contexts_by_cucp_ue_e1ap_id.pop(bearer[0], None)
            self.contexts_by_cuup_ue_e1ap_id.pop(bearer[1], None)
            # if no more bearers are present, remove the cuup_index too
            if len(self.contexts[ue_id].e1_bearers) == 0:
                self.clear_cuup_index(ue_id)
            self.delete_unused_context(ue_id)        

    ####################################################################
    def getid_by_du_cucp_unique_info(self, plmn: int, pci:int, rnti: int) -> int:
        if self.dbg:
            print(f"getid_by_du_cucp_unique_info: plmn={plmn} pci={pci} rnti={rnti}")
        filtered_contexts = {
            k: v for k, v in self.contexts.items()
            if v.plmn == plmn and v.pci == pci and v.crnti == rnti
        }
        if len(filtered_contexts) == 1:
            return list(filtered_contexts.keys())[0]
        elif len(filtered_contexts) > 1:
            raise ValueError("Multiple UE contexts found for the given PLMN, PCI, and RNTI.")

        # if we reach here, it means no context was found
        return None 
        
    #####################################################################
    def getue_by_id(self, ue_id: int) -> int:
        return self.contexts.get(ue_id, None)
    
    #####################################################################
    def getid_by_du_index(self, du_index: int) -> int:
        return self.contexts_by_du_index.get(du_index, None)

    #####################################################################
    def getid_by_cucp_index(self, cucp_index: int) -> int:
        return self.contexts_by_cucp_index.get(cucp_index, None)

    #####################################################################
    def getid_by_cuup_index(self, cuup_index: int) -> int:
        return self.contexts_by_cuup_index.get(cuup_index, None)

    #####################################################################
    def getid_by_cucp_ue_e1ap_id(self, cucp_ue_e1ap_id: int) -> int:
        return self.contexts_by_cucp_ue_e1ap_id.get(cucp_ue_e1ap_id, None)
    
    #####################################################################
    def getid_by_cuup_ue_e1ap_id(self, cuup_ue_e1ap_id: int) -> int:
        return self.contexts_by_cuup_ue_e1ap_id.get(cuup_ue_e1ap_id, None)

    ####################################################################
    def get_e1_bearer(self, cucp_ue_e1ap_id: int) -> (int, Tuple[int, int]):
        ue_id = self.getid_by_cucp_ue_e1ap_id(cucp_ue_e1ap_id)
        if ue_id is None:
            if self.dbg:
                print(f"get_e1_bearer: UE context with cucp_ue_e1ap_id {cucp_ue_e1ap_id} not found.")
            return None, (None, None)
        return ue_id, self.contexts[ue_id].get_bearer(cucp_ue_e1ap_id)

    ####################################################################
    def hook_du_ue_ctx_creation(self, du_index: int, plmn: int, pci: int, crnti: int, tac: int, nci: int) -> None:
        """
        Create a UE context in the DU subsystem.

        :param du_index: The index of the UE in the DU subsystem.
        :param tac: Tracking Area Code.
        :param plmn: Public Land Mobile Network identifier.
        :param nci: NR Cell Identity.
        :param pci: Physical Cell Identity.
        :param crnti: C-RNTI (Cell Radio Network Temporary Identifier).
        """

        if self.dbg:
            print(f"hook_du_ue_ctx_creation: du_index {du_index} plmn={plmn} pci {pci} tc_rnti {crnti} tac {tac} nci={nci} ] ")
        
        # Check if the UE context with the du index already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_du_index(du_index)
        if ue_id is not None:
            print(f"Unexpected UE context with index {du_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        # Check if the UE context with the unique info already exists
        # It should not exist, do if it does, delete it
        ue_id = self.getid_by_du_cucp_unique_info(plmn, pci, crnti)
        if ue_id is not None:
            print(f"Unexpected UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        # Create a new UE context
        self.context_create(plmn, pci, crnti, du_index, nci=nci, tac=tac)

    ####################################################################
    def hook_cucp_uemgr_ue_add(self, cucp_index: int, plmn: int, pci: int, crnti: int) -> None:
        """
        Create a UE context in the CU-CP subsystem.

        :param cu_cp_index: The index of the UE in the CU-CP subsystem.
        :param plmn: Public Land Mobile Network identifier.
        :param pci: Physical Cell Identity.
        :param crnti: C-RNTI (Cell Radio Network Temporary Identifier).
        """

        if self.dbg:
            print(f"hook_cucp_uemgr_ue_add: cucp_index {cucp_index} plmn {plmn} pci={pci} rnti={crnti}")

        # Check if a UE context with the cucp index already exists
        # It should not, so delete it if it does 
        ue_id = self.getid_by_cucp_index(cucp_index)
        if ue_id is not None:
            print(f"Unexpected UE context with index {cucp_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id)

        # Check if a UE context with the unique info already exists
        # If it does not 
        #    create a new one
        # If it does, 
        #   check if the cucp index is currently set.
        #   If it is, delete the UE and create a new one
        #   If it is not, just update the cucp index
        ue_id = self.getid_by_du_cucp_unique_info(plmn, pci, crnti)
        if ue_id is None:
            # Create a new UE context
            self.context_create(plmn, pci, crnti, cucp_index=cucp_index)
        else:
            if self.contexts[ue_id].cucp_index is not None:
                print(f"Unexpected UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Stale UE will be deleted")
                self.context_delete(ue_id)
                # Create a new UE context
                self.context_create(plmn, pci, crnti, cucp_index=cucp_index)
            else:
                print(f"UE context with [plmn={plmn} pci={pci} crnti={crnti}] already exists.  Setting cucp index")
                self.set_cucp_index(ue_id, cucp_index)
                print(f"UE context updated: {self.contexts[ue_id]}")

    ####################################################################
    def hook_e1_cucp_bearer_context_setup(self, cucp_index: int, gnb_cucp_ue_e1ap_id: int) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-CP.

        :param cucp_index: The index of the UE in the CU-CP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        """

        if self.dbg:
            print(f"hook_e1_cucp_bearer_context_setup, cucp_index={cucp_index} gnb_cucp_ue_e1ap_id={gnb_cucp_ue_e1ap_id}")

        # Check if a UE context with the gnb_cucp_ue_e1ap_id already exists
        # It should not, so clear it if it does 
        ue_id = self.getid_by_cucp_ue_e1ap_id(gnb_cucp_ue_e1ap_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with gnb_ccup_ue_e1ap_id {gnb_cucp_ue_e1ap_id} already exists")
            self.clear_cucp_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id)

        # Check if a UE context with the cucp index already exists
        # It should, so return if it does not
        ue_id = self.getid_by_cucp_index(cucp_index)    
        if ue_id is None:
            print(f"UE context with index {cucp_index} not found. !!")
            return
    
        # update the gnb_cucp_ue_e1ap_id
        self.set_cucp_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id)

    ####################################################################
    def hook_e1_cuup_bearer_context_setup(self, cuup_index: int, gnb_cucp_ue_e1ap_id: int, gnb_cuup_ue_e1ap_id: int, success: bool) -> None:
        """
        Handle the E1AP Bearer Context Setup for CU-UP.

        :param cuup_index: The index of the UE in the CU-UP subsystem.
        :param gnb_cu_cp_ue_e1ap_id: The E1AP ID for the CU-CP.
        :param gnb_cu_up_ue_e1ap_id: The E1AP ID for the CU-UP.
        """

        if self.dbg:
            print(f"hook_e1_cuup_bearer_context_setup success={success}, cu_up_index {cuup_index}  gnb_cu_cp_ue_e1ap_id={gnb_cucp_ue_e1ap_id} gnb_cu_up_ue_e1ap_id={gnb_cuup_ue_e1ap_id}")

        # Check if a UE context with the gnb_cuup_ue_e1ap_id already exists
        # It should not, so clear it if it does 
        ue_id = self.getid_by_cuup_ue_e1ap_id(gnb_cuup_ue_e1ap_id)
        if ue_id is not None:
            if self.dbg:
                print(f"Unexpected UE context with gnb_cuup_ue_e1ap_id {gnb_cuup_ue_e1ap_id} already exists")
            self.clear_cuup_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id)

        # check that the e1 bearer has cuup_ue_e1ap_id=None.
        # If it is set, clear the beafer
        ue_id, bearer = self.get_e1_bearer(gnb_cucp_ue_e1ap_id)
        if ue_id is None:
            # the bearer does not exist, the mapping cannot be done
            return
        if bearer[1] is not None and bearer[1] != gnb_cuup_ue_e1ap_id:
            # the bearer already has a cuup_ue_e1ap_id, clear it
            self.clear_cuup_ue_e1ap_id(ue_id, bearer[1])
            # the mapping cannot be done
            return

        # if this point it reached, it means we have the ue context with a matching bearer (cucp_ue_e1ap_id, None)

        # check if the cucp index is different

        ue_id2 = self.getid_by_cuup_index(cuup_index)
        if ue_id2 is not None and ue_id2 != ue_id:
            if self.dbg:
                print(f"Unexpected UE context with cuup_index {cuup_index} already exists.  Stale UE will be deleted")
            self.context_delete(ue_id2)
            return

        # if this is a failure, clear the cucp_ue_e1ap_id
        if success is False:
            # remove the cucp_ue_e1ap_id from the context
            s.clear_cucp_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id)
            return

        # set the cuup_ue_e1ap_id
        self.set_cuup_ue_e1ap_id(ue_id, gnb_cucp_ue_e1ap_id, gnb_cuup_ue_e1ap_id)
        # update the cuup index
        self.set_cuup_index(ue_id, cuup_index)

    ####################################################################
    def hook_du_ue_ctx_deletion(self, du_index: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_du_ue_ctx_deletion: du_index {du_index}")
        ue_id = self.getid_by_du_index(du_index)
        if ue_id is not None:
            self.clear_du_index(ue_id)

    ####################################################################
    def hook_cucp_uemgr_ue_remove(self, cucp_index: int) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_cucp_uemgr_ue_remove: cu_cp_index {cucp_index}")
        ue_id = self.getid_by_cucp_index(cucp_index)
        if ue_id is not None:
            self.clear_cucp_index(ue_id)

    #####################################################################
    def hook_e1_cuup_bearer_context_release(self, cuup_index: int, cucp_ue_e1ap_id: int, cuup_ue_e1ap_id: int, success: bool) -> None:
        if self.dbg:
            print("-------------------------------------------------")
            print(f"hook_e1_cuup_bearer_context_release success {success} cuup_index {cuup_index} gnb_cucp_ue_e1ap_id={cucp_ue_e1ap_id} gnb_cuup_ue_e1ap_id={cuup_ue_e1ap_id}")

        if success is False:
            return
        
        ue_id = self.getid_by_cucp_ue_e1ap_id(cucp_ue_e1ap_id)
        if ue_id is not None:
            self.clear_cucp_ue_e1ap_id(ue_id, cucp_ue_e1ap_id)

        ue_id = self.getid_by_cuup_ue_e1ap_id(cuup_ue_e1ap_id)
        if ue_id is not None:
            self.clear_cuup_ue_e1ap_id(ue_id, cuup_ue_e1ap_id)

    ####################################################################
    def get_num_contexts(self) -> int:
        return len(self.contexts)

    ####################################################################
    def __str__(self):
        return (
            f"srsRAN_UEContexts(\n"
            f"  contexts={self.contexts},\n"
            f"  contexts_by_du_index={self.contexts_by_du_index},\n"
            f"  contexts_by_cucp_index={self.contexts_by_cucp_index},\n"
            f"  contexts_by_cuup_index={self.contexts_by_cuup_index},\n"
            f"  contexts_by_cucp_ue_e1ap_id={self.contexts_by_cucp_ue_e1ap_id},\n"
            f"  contexts_by_cuup_ue_e1ap_id={self.contexts_by_cuup_ue_e1ap_id}\n"
            f")"
        )

##########################################################################################################
if __name__ == "__main__":

    s = srsRAN_UEContexts(dbg=True)


    #############################################################################
    # create a new UE context
    s.hook_du_ue_ctx_creation(0,   # du_index
                              101,   # plmn
                              400,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1
    

    #############################################################################
    # Use same du_index.  This will overwrite the previous context
    s.hook_du_ue_ctx_creation(0,   # du_index
                              101,   # plmn
                              401,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(0)
    assert ue_id == 1
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index == 0 and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    ############################################################################
    # Use same plmn, pci, crnti.  This will overwrite the previous context
    s.hook_du_ue_ctx_creation(1,   # du_index
                              101,   # plmn
                              401,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(1) 
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==1 and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    ###########################################################################
    # Create 2nd UE context with different du_index
    s.hook_du_ue_ctx_creation(2,   # du_index
                              101,   # plmn
                              401,   # pci
                              20001, # crnti
                              12,    # tac
                              201)   # nci
    assert s.get_num_contexts() == 2
    ue_id = s.getid_by_du_index(1) 
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==1 and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000
    ue_id = s.getid_by_du_index(2) 
    assert ue_id == 3
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==2 and ue.cucp_index is None and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20001

    
    
    ############################################################################
    # Add a cucp UE where there is no existing context with the matching plmn, pci, crnti
    s.hook_cucp_uemgr_ue_add(0,     # cucp_index
                             101,   # plmn
                             499,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(0) 
    assert ue_id == 4
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==0 and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==499 and ue.tac is None and ue.crnti==20000


    ############################################################################
    # Add a cucp UE where there is an existing context with the matching plmn, pci, crnti
    s.hook_cucp_uemgr_ue_add(1,     # cucp_index
                             101,   # plmn
                             401,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(1)
    assert ue_id == 2
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==1 and ue.cucp_index==1 and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==401 and ue.tac==12 and ue.crnti==20000


    ############################################################################
    # Add a cucp UE where there is an existing context with the matching plmn, pci, crnti, with cucp_index != None
    s.hook_cucp_uemgr_ue_add(1,     # cucp_index
                             101,   # plmn
                             401,   # pci
                             20000), # crnti
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(1)
    assert ue_id == 5
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==1 and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==401 and ue.tac is None and ue.crnti==20000


    ############################################################################
    # Call hook_e1_cucp_bearer_context_setup top add the id to an existing UE
    s.hook_e1_cucp_bearer_context_setup(1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 3
    ue_id = s.getid_by_cucp_index(1)
    assert ue_id == 5
    ue_id = s.getid_by_cucp_ue_e1ap_id(2000)
    assert ue_id == 5
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index is None and ue.cucp_index==1 and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci is None and ue.pci==401 and ue.tac is None and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==2000 and ue.e1_bearers[0][1] is None
    
    
    ############################################################################
    # Call hook_e1_cucp_bearer_context_setup again.  Ths will delete the context
    s.hook_e1_cucp_bearer_context_setup(1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 3


    #############################################################################
    # delete s and start fresh
    s = srsRAN_UEContexts(dbg=True)


    #############################################################################
    # create DU UE context
    s.hook_du_ue_ctx_creation(0,   # du_index
                              101,   # plmn
                              400,   # pci
                              20000, # crnti
                              12,    # tac
                              201)   # nci
    # create cucp context
    s.hook_cucp_uemgr_ue_add(1,     # cucp_index
                             101,   # plmn
                             400,   # pci
                             20000), # crnti
    # create cucp e1ap id
    s.hook_e1_cucp_bearer_context_setup(1,    # cucp_index
                                        2000) # cucp_ue_e1ap_id
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(0)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_index(1)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_ue_e1ap_id(2000)
    assert ue_id == 0
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==0 and ue.cucp_index==1 and ue.cuup_index is None \
           and ue.plmn==101 and ue.nci==201 and ue.pci==400 and ue.tac==12 and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==2000 and ue.e1_bearers[0][1] is None

    #############################################################################
    # add cuup e1 context
    s.hook_e1_cuup_bearer_context_setup(10,    # cuup_index
                                        2000,  # gnb_cucp_ue_e1ap_id,
                                        12000, # gnb_cuup_ue_e1ap_id
                                        True)  # succees
    assert s.get_num_contexts() == 1
    ue_id = s.getid_by_du_index(0)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_index(1)
    assert ue_id == 0
    ue_id = s.getid_by_cucp_ue_e1ap_id(2000)
    assert ue_id == 0
    ue = s.getue_by_id(ue_id)
    assert ue is not None and ue.du_index==0 and ue.cucp_index==1 and ue.cuup_index==10 \
           and ue.plmn==101 and ue.nci==201 and ue.pci==400 and ue.tac==12 and ue.crnti==20000 \
           and len(ue.e1_bearers)==1 and ue.e1_bearers[0][0]==2000 and ue.e1_bearers[0][1] ==12000

    #############################################################################
    # Try to do it again - thil cause the bearer to be deleted
    s.hook_e1_cuup_bearer_context_setup(11,    # cuup_index
                                        2000,  # gnb_cucp_ue_e1ap_id,
                                        12000, # gnb_cuup_ue_e1ap_id
                                        True)  # succees
    assert s.get_num_contexts() == 1

    
    #############################################################################
    # delete s and start fresh
    s = srsRAN_UEContexts(dbg=True)


    #############################################################################
    # create UE bearers, with 2 e1 bearers per ue
    num_ue = 10
    num_e1 = 3
    crnti_off = 20000
    du_off = 100
    cucp_off = 200
    cuup_off = 300
    cucp_e1Off = 20000
    cuup_e1Off = 30000

    for ue in range(0, num_ue):
        s.hook_du_ue_ctx_creation(  du_off+ue,   # du_index
                                    101,   # plmn
                                    400,   # pci
                                    crnti_off+ue, # crnti
                                    12,    # tac
                                    201)   # nci
        # create cucp context
        s.hook_cucp_uemgr_ue_add(   cucp_off+ue,     # cucp_index
                                    101,   # plmn
                                    400,   # pci
                                    crnti_off+ue), # crnti
        for e1 in range(0, num_e1):
            # create cucp e1ap id
            e1off = (ue * num_e1) + e1
            s.hook_e1_cucp_bearer_context_setup(    cucp_off+ue,    # cucp_index
                                                    cucp_e1Off+e1off) # cucp_ue_e1ap_id
            s.hook_e1_cuup_bearer_context_setup(    cuup_off+ue,    # cuup_index
                                                    cucp_e1Off+e1off,  # gnb_cucp_ue_e1ap_id,
                                                    cuup_e1Off+e1off, # gnb_cuup_ue_e1ap_id
                                                    True)  # succees

    assert s.get_num_contexts() == num_ue

    for ue in range(0, num_ue):
        ue_id = s.getid_by_du_index(du_off+ue)
        assert ue_id == ue
        ue_id = s.getid_by_cucp_index(cucp_off+ue)
        assert ue_id == ue
        ue_id = s.getid_by_cuup_index(cuup_off+ue)
        assert ue_id == ue
        for e1 in range(0, num_e1):
            e1off = (ue * num_e1) + e1
            ue_id = s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+e1off)
            assert ue_id == ue
            ue_id = s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+e1off)
            assert ue_id == ue
        ctx = s.getue_by_id(ue_id)
        assert ctx is not None and ctx.du_index==du_off+ue and ctx.cucp_index==cucp_off+ue and ctx.cuup_index==cuup_off+ue \
               and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
               and len(ctx.e1_bearers)==num_e1 and \
               all(ctx.e1_bearers[i][0]==cucp_e1Off+(ue*num_e1)+i and ctx.e1_bearers[i][1]==cuup_e1Off+(ue*num_e1)+i for i in range(0, num_e1))


    #############################################################################
    # Test accessors
    print("200 : ",s)
    assert s.getid_by_du_index(du_off+0) == 0
    assert s.getid_by_du_index(du_off+9) == 9
    assert s.getid_by_du_index(du_off+10) is None

    assert s.getid_by_cucp_index(cucp_off+0) == 0
    assert s.getid_by_cucp_index(cucp_off+9) == 9
    assert s.getid_by_cucp_index(cucp_off+10) is None

    assert s.getid_by_cuup_index(cuup_off+0) == 0
    assert s.getid_by_cuup_index(cuup_off+9) == 9
    assert s.getid_by_cuup_index(cuup_off+10) is None

    assert s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+(0*num_e1)+0) == 0
    assert s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+(0*num_e1)+2) == 0
    assert s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+(9*num_e1)+0) == 9
    assert s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+(9*num_e1)+2) == 9
    assert s.getid_by_cucp_ue_e1ap_id(cucp_e1Off+(10*num_e1)+0) is None

    assert s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+(0*num_e1)+0) == 0
    assert s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+(0*num_e1)+2) == 0
    assert s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+(9*num_e1)+0) == 9
    assert s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+(9*num_e1)+2) == 9
    assert s.getid_by_cuup_ue_e1ap_id(cuup_e1Off+(10*num_e1)+0) is None


    #############################################################################
    # Test deletion - du index, then cucp index, then cuup index.  Context will only be deleted when all 3 are cleared
    ue_to_delete = num_ue-1
    ue = s.getid_by_du_index(du_off+ue_to_delete)
    s.hook_du_ue_ctx_deletion(du_off+ue_to_delete)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index==cucp_off+ue and ctx.cuup_index==cuup_off+ue \
            and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
            and len(ctx.e1_bearers)==num_e1 and \
            all(ctx.e1_bearers[i][0]==cucp_e1Off+(ue*num_e1)+i and ctx.e1_bearers[i][1]==cuup_e1Off+(ue*num_e1)+i for i in range(0, num_e1))
    s.hook_cucp_uemgr_ue_remove(cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index is None and ctx.cucp_index is None and ctx.cuup_index==cuup_off+ue \
            and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
            and len(ctx.e1_bearers)==num_e1 and \
            all(ctx.e1_bearers[i][0]==cucp_e1Off+(ue*num_e1)+i and ctx.e1_bearers[i][1]==cuup_e1Off+(ue*num_e1)+i for i in range(0, num_e1))
    for e1 in range(0, num_e1):
        e1off = (ue * num_e1) + e1
        s.hook_e1_cuup_bearer_context_release(cuup_off+ue, cucp_e1Off+e1off, cuup_e1Off+e1off, True)
        if e1 < num_e1-1:
            assert s.get_num_contexts() == num_ue
        else:
            # context should be deleted after removing the last e1 bearer
            assert s.get_num_contexts() == num_ue-1
            num_ue = num_ue-1
    ctx = s.getue_by_id(ue)
    assert ctx is None

    ###############################################################################
    # Test deletion - cuup, then cucp, then du
    ue_to_delete = num_ue-1
    ue = s.getid_by_du_index(du_off+ue_to_delete)
    for e1 in range(0, num_e1):
        e1off = (ue * num_e1) + e1
        s.hook_e1_cuup_bearer_context_release(cuup_off+ue, cucp_e1Off+e1off, cuup_e1Off+e1off, True)
        assert s.get_num_contexts() == num_ue
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==du_off+ue and ctx.cucp_index==cucp_off+ue and ctx.cuup_index is None \
        and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
        and len(ctx.e1_bearers)==0 
    s.hook_cucp_uemgr_ue_remove(cucp_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is not None and ctx.du_index==du_off+ue and ctx.cucp_index is None and ctx.cuup_index is None \
        and ctx.plmn==101 and ctx.nci==201 and ctx.pci==400 and ctx.tac==12 and ctx.crnti==crnti_off+ue \
        and len(ctx.e1_bearers)==0 
    s.hook_du_ue_ctx_deletion(du_off+ue)
    ctx = s.getue_by_id(ue)
    assert ctx is None


    print("201 : ",s)
#    assert s.get_num_contexts() == num_ue




    sys.exit(0)
