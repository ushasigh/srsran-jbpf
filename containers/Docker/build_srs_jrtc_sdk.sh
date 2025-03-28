#!/bin/bash

IMAGE_TAG=latest

# First build the jbpf_protobuf image

pushd . > /dev/null
cd ../../jbpf_protobuf/

# To build for a particular OS, run:
OS=azurelinux
docker build -t jbpfp-$OS:latest -f deploy/$OS.Dockerfile .

# And to create a jbpf_protobuf_cli image from that container, run:
docker build --build-arg builder_image=jbpfp-$OS --build-arg builder_image_tag=latest -t jbpf_protobuf_cli:latest - < deploy/jbpf_protobuf_cli.Dockerfile

popd > /dev/null


# Add jrt-controller image
# TBD


# Finally, build a small SDK based on the other two


docker build --no-cache\
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE=jbpf_protobuf_cli \
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE_TAG=latest \
    --build-arg SRS_JBPF_SDK_IMAGE=ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk \
    --build-arg SRS_JBPF_SDK_IMAGE_TAG=latest \
    -t ghcr.io/microsoft/jrtc-apps/srs-jrtc-sdk:${IMAGE_TAG} -f SRS-jrtc-sdk.Dockerfile .

exit 0

