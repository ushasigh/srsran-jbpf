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

docker build \
    --build-arg IMAGE_TAG=${IMAGE_TAG} \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf-proxy:${IMAGE_TAG} -f SRS-jbpf-proxy.Dockerfile .

exit 0
