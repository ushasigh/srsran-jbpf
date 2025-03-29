#!/bin/sh

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

SDK_IMAGE_TAG=latest
CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $CURRENT_DIR/../set_vars.sh

set -e

Usage()
{
   # Display Help
   echo "Unload schemas"
   echo "options:"
   echo "-c      Mandatory.  Full path of codeletSet yaml file"
   echo
}

# Get the options
while getopts "c:" option; do
	case $option in
		c) # codeletSet yaml file
			codeletSet_yaml="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

# Check if codeletSet_yaml is set
if [ -z "$codeletSet_yaml" ]; then
    echo "Error: -c <codeletSet yaml file> is mandatory."
    Usage
    exit 1
fi
# check it exists
if [ ! -e "$codeletSet_yaml" ]; then
    echo "$codeletSet_yaml does not exist."
    exit 1
fi


echo "Unloading schemas from codeletSet yaml file: $codeletSet_yaml"

if [ "$SRS_JBPF_DOCKER" -eq 1 ]; then
    yaml_file_path=$(dirname "$codeletSet_yaml")
    tmp_yaml=$yaml_file_path/tmp.yaml 
    $CURRENT_DIR/add_stream_ids.sh $codeletSet_yaml $tmp_yaml

    tmp_yaml_short="${tmp_yaml/#$JBPF_CODELETS/\/codelets}"

    $DOCKER_CMD run --network=host \
        -v $JBPF_CODELETS:/codelets \
        -e "JBPF_CODELETS=/codelets" \
        --entrypoint /usr/local/bin/jbpf_protobuf_cli \
        ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk:$SDK_IMAGE_TAG \
        decoder unload -c $tmp_yaml_short

    rm -f $tmp_yaml
else
    $JBPF_PROTOBUF_CLI_BIN decoder unload -c $codeletSet_yaml
fi

exit 0