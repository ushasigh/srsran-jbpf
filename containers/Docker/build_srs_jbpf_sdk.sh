#!/bin/bash

IMAGE_TAG=latest

Usage()
{
   # Display Help
   echo "Build srsRan=Jbpf base image"
   echo "options:"
   echo "[-s]    Optional srsRan image tag.  Default='latest'"
   echo
}

# Get the options
while getopts "s:" option; do
	case $option in
		s) # Set image tag
			IMAGE_TAG="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

echo IMAGE_TAG $IMAGE_TAG


# First build the jbpf_protobuf image

pushd . > /dev/null
cd ../../jbpf_protobuf/

# To build for a particular OS, run:
OS=azurelinux
docker build -t jbpfp-$OS:latest -f deploy/$OS.Dockerfile .

# And to create a jbpf_protobuf_cli image from that container, run:
docker build --build-arg builder_image=jbpfp-$OS --build-arg builder_image_tag=latest -t jbpf_protobuf_cli:latest - < deploy/jbpf_protobuf_cli.Dockerfile

popd > /dev/null



docker build \
    --build-arg SRS_JBPF_IMAGE_TAG=${IMAGE_TAG} \
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE=jbpf_protobuf_cli \
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE_TAG=latest \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk:${IMAGE_TAG} -f SRS-jbpf-sdk.Dockerfile .

exit 0
