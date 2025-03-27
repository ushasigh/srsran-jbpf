# Shell command to build this image:
# docker build -t ghcr.io/microsoft/jrtc-apps/srs:latest -f SRS.Dockerfile .
# docker push ghcr.io/microsoft/jrtc-apps/srs:latest


ARG LIB=dpdk
ARG LIB_VERSION=23.11

ARG BASE_IMAGE_TAG=latest
FROM ghcr.io/microsoft/jrtc-apps/srs:${BASE_IMAGE_TAG}

ADD srsRAN_Project /src 

ENV PKG_CONFIG_PATH=/opt/dpdk-23.11/build/meson-private:/usr/lib/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig:$PKG_CONFIG_PATH

# extra modules required when ENABLE_JBPF=ON
RUN tdnf -y install yaml-cpp-static boost-devel clang doxygen

WORKDIR /src
RUN mkdir build
WORKDIR /src/build
RUN cmake .. -DENABLE_DPDK=True -DENABLE_JBPF=ON -DINITIALIZE_SUBMODULES=OFF
RUN make -j
RUN make install

ADD Scripts /opt/Scripts
WORKDIR /opt/Scripts
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "run.sh" ]


