#!/bin/bash
# Copyright (c) Microsoft Corporation. All rights reserved.

source ../set_vars.sh

Help()
{
   # Display Help
   echo "Unload JRTC app."
   echo
   echo "Syntax: $0 -y <deployment-yaml>"
   echo "options:"
   echo "-y     App yaml file with path"
   echo
}

DEPLOYMENT_YAML=""

# Get the options
while getopts "y:" option; do
	case $option in
		y) 
			DEPLOYMENT_YAML="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Help
			exit;;
	esac
done

if [[ -z "$DEPLOYMENT_YAML" || ! -f "$DEPLOYMENT_YAML" ]]; then
    echo "Error: DEPLOYMENT_YAML is either not set or the file does not exist."
    Help
    exit 1
fi

if [[ -z "$JRTC_CTL_BIN" || ! -f "$JRTC_CTL_BIN" ]]; then
    echo "Error: DEPLOYMENT_YAML is either not set or the file does not exist."
    Help
    exit 1
fi

DEPLOYMENT_YAML_FILENAME=$(basename "$DEPLOYMENT_YAML")
DEPLOYMENT_YAML_PATH=$(dirname "$DEPLOYMENT_YAML")

pushd . > /dev/null
cd $DEPLOYMENT_YAML_PATH
$JRTC_CTL_BIN unload -c $DEPLOYMENT_YAML_FILENAME --log-level trace
ret=$?
popd > /dev/null

exit $ret
