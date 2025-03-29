#!/bin/sh

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $CURRENT_DIR/../set_vars.sh

if [ -z "$SRS_JBPF_DOCKER" ]; then
    $JBPF_PROTOBUF_CLI_BIN decoder run # --log-level trace
else
    # Run the decoder in a container
    $DOCKER_CMD run -it --rm -d --name jbpf_decoder --network=host -v $JBPF_CODELETS:/codelets jbpf_protobuf_cli decoder run #  --log-level debug
fi

