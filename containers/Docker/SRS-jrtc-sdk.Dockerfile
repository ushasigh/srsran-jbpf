ARG JBPF_PROTOBUF_BUILDER_IMAGE=jbpf_protobuf_cli       
ARG JBPF_PROTOBUF_BUILDER_IMAGE_TAG=latest
ARG SRS_JBPF_SDK_IMAGE=ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk
ARG SRS_JBPF_SDK_IMAGE_TAG=latest

FROM ${JBPF_PROTOBUF_BUILDER_IMAGE}:${JBPF_PROTOBUF_BUILDER_IMAGE_TAG} AS jbpf_protobuf_builder
FROM ${SRS_JBPF_SDK_IMAGE}:${SRS_JBPF_SDK_IMAGE_TAG}

LABEL org.opencontainers.image.source="https://github.com/microsoft/jrtc-apps"
LABEL org.opencontainers.image.authors="Microsoft Corporation"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.description="SDK for SRSRAN with JBPF and JRTC"

COPY --from=jbpf_protobuf_builder /jbpf-protobuf/3p/nanopb /nanopb
COPY --from=jbpf_protobuf_builder jbpf-protobuf/out/bin/jbpf_protobuf_cli /usr/local/bin/jbpf_protobuf_cli

RUN tdnf upgrade tdnf --refresh -y && tdnf -y update
RUN tdnf install -y build-essential make python3-pip

RUN pip install ctypesgen

RUN python3 -m pip install -r /nanopb/requirements.txt

RUN tdnf -y install  clang

ENV JBPF_PROTOBUF_CLI_BIN=/usr/local/bin/jbpf_protobuf_cli
ENV NANO_PB=/nanopb
