#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

git submodule update --init --recursive

pushd . > /dev/null
cd jbpf_protobuf
./init_submodules.sh
popd > /dev/null

