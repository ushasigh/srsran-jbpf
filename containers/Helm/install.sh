##!/bin/bash


CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )



# Helper function
print_image_tag() {
    field="$1"
    # Extracting the image tag
    image_tag=$(echo "$2" | jq -r ".image.$field" | awk -F ':' '{print $NF}')

    # Checking if the image tag is defined
    if [ -n "$image_tag" ]; then
        echo "    Image tag for $field: $image_tag"
    fi
}

Help()
{
   # Display Help
   echo "Install Capgemini RAN."
   echo
   echo "Syntax: install [-h <local_chart_path>|-f <values_file>|-v <image_tag>]"
   echo "options:"
   echo "-?     Show this help message"
   echo "-f     (Optional) Extra values config file"
   echo "-v     (Optional) Helm chart version ($CHART_VERSION is the default)"
   echo "-h     (Optional) Install Helm from a local path given here, instead of Github"
   echo "-b     (Optional) Local path with compiled jbpf codelets (current path is the default)"
   echo "-d     (Optional) Debug mode that doesn't start binaries"
   echo
}

VALUES_FILES=
VERSION=$CHART_VERSION
LOCAL_PATH=
DEBUG=

while getopts "n:f:v:h:db" option; do
    case $option in
        f) # Add extra config file
            VALUES_FILES="$VALUES_FILES $OPTARG";;
        v) # Set chart version
            VERSION="$OPTARG";;
        h) # Set local chart path
            LOCAL_PATH="$OPTARG";;
        b) # Set local chart path
            JBPF_CODELETS="$OPTARG";;
        d) # Enable debug
            DEBUG="DEBUG";;
        \?) # Invalid option
            echo "Invalid option"
            Help
            exit;;
    esac
done

HELM_URL=
if [[ -z "${LOCAL_PATH}" ]]; then
    HELM_URL="oci://ghcr.io/microsoft/jrtc-apps/helm/srs-ran-5g-jbpf --version ${VERSION}"
else
    HELM_URL=${LOCAL_PATH}
    echo "Using Helm from local path: ${LOCAL_PATH}"
fi


EXTRA_VALUES=""
EXTRA_VALUES_SUMMARY=""
for values_file in $VALUES_FILES; do
    if [ ! -f "$values_file" ]; then
        echo "Values file does not exist: $values_file"
        exit 1
    fi
    EXTRA_VALUES="$EXTRA_VALUES -f $values_file"
    EXTRA_VALUES_SUMMARY="$EXTRA_VALUES_SUMMARY $values_file"
done
echo "Extra values files: $EXTRA_VALUES_SUMMARY"



DEBUG_OPTIONS=
if [ ! -z "$DEBUG" ]; then
    DEBUG_OPTIONS="\
    --set         debug_mode.enabled=true"
fi

# Add codelets mount point
if [ -z "$JBPF_CODELETS" ]; then
    JBPF_CODELETS=$(realpath "${CURRENT_DIR}/../../codelets/")
fi
JBPF_OPTIONS=" --set-string  jbpf.codelets_vol_mount=$JBPF_CODELETS "
echo "Codelet mount point: ${JBPF_CODELETS}"


kubectl create namespace ran || true


helm install \
    $EXTRA_VALUES $DEBUG_OPTIONS $JBPF_OPTIONS -n ran ran $HELM_URL



echo ""
echo ""
echo "*** Custom Helm chart configs:"
echo ""

VALUES=$(helm -n ran get values ran --output json)

echo "Custom image tags (if any):"
print_image_tag "srs" "$VALUES"
echo ""

echo "Custom cell config (if any):"
echo "$VALUES" | jq -r '.duConfigs | keys[] as $du_config | "\($du_config): \(.[$du_config].cells | to_entries[] | select(.value.perf != null) | "  Cell: \(.key)\n    Perf structure: \(.value.perf | tojson)" )"'
echo ""

echo Janus out IP: $(echo "$VALUES" | jq -r '.debug_mode.janus.out_ip'):$(echo "$VALUES" | jq -r '.debug_mode.janus.out_port')
echo ""




