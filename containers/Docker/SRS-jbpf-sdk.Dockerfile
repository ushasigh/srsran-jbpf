# Shell command to build this image:
# docker build -t ghcr.io/microsoft/jrtc-apps/srs-jbpf-proxy:latest -f SRS-jbpf-proxy.Dockerfile .
# docker push ghcr.io/microsoft/jrtc-apps/srs-jbpf-proxy:latest

ARG IMAGE_TAG=latest

FROM ghcr.io/microsoft/jrtc-apps/srs-jbpf:${IMAGE_TAG} AS srsran

FROM mcr.microsoft.com/azurelinux/base/core:3.0

LABEL org.opencontainers.image.source="https://github.com/microsoft/jrtc-apps"
LABEL org.opencontainers.image.authors="Microsoft Corporation"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.description="SDK for SRSRAN with JBPF"

RUN echo "*** Installing packages"
RUN tdnf -y install yaml-cpp-static boost-devel clang

COPY --from=srsran /src/out /src/out
COPY --from=srsran /src/include /src/include
COPY --from=srsran /src/external /src/external
COPY --from=srsran /usr/lib /usr/lib
COPY --from=srsran /usr/local/lib /usr/local/lib

RUN rm -f /usr/local/lib/librte*

ENV LD_LIBRARY_PATH=/usr/local/lib/:/usr/lib

ENV JBPF_OUT_DIR=/src/out
ENV SRSRAN_INC_DIR=/src/include
ENV SRSRAN_EXTERNAL_DIR=/src/external
ENV CPP_INC=/usr/include/c++/13.2.0
ENV VERIFIER_BIN=/src/out/bin/srsran_verifier_cli

WORKDIR /out

ENTRYPOINT ["/bin/bash"]
