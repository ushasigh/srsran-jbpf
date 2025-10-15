### Terminal 1 
```bash
git clone https://github.com/ushasigh/srsran-jbpf.git
cd srsran-jbpf
./init_submodules.sh
```

#### Build all necessary images
```bash
cd containers/Docker
chmod a+x build_base.sh
sudo ./build_base.sh [-b base]
chmod a+x build_srs_jbpf.sh
sudo ./build_srs_jbpf.sh [-b base] [-s janus_srsran/gnb] [-c]
chmod a+x build_srs_jbpf_sdk.sh
sudo ./build_srs_jbpf_sdk.sh [-s janus_srsran/gnb]
```

#### Install k3d
```bash
TODO
```

#### Create the RAN cluster
```bash
k3d cluster delete janus-cluster # Delete any existing cluster
k3d cluster create janus-cluster --volume /home/wcsng-23/gitrepos/srsran-jbpf:/home/wcsng-23/gitrepos/srsran-jbpf --port "30400-30500:30400-30500@loadbalancer"
k3d kubeconfig merge janus-cluster --kubeconfig-switch-context
k3d cluster list
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl create namespace ran
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl wait --for=condition=ready pod -l app=multus -n kube-system --timeout=60s
```

#### RAN deploymnet with JRTC
```bash
cd srsran-jbpf/containers/Helm
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm install ran . -n ran -f jrtc.yaml -f k3d-values.yaml

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl get pods -n ran

#### Exec into containers
## Check the container running in the pod:
kubectl get pod srs-gnb-du1-0 -n ran -o jsonpath="{.spec.containers[*].name}"

## Exec into a container:
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash

## upgrade a pod
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm upgrade ran . -n ran -f jrtc.yaml -f k3d-values.yaml
```

### Terminal 2 - Core Network
#### Open5gs deployment
```bash
cd /home/wcsng-23/gitrepos/srsran-jbpf/open5gs
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm dependency list

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl create namespace open5gs

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm install open5gs . -n open5gs -f values-5g.yaml
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm upgrade open5gs /home/wcsng-23/gitrepos/srsran-jbpf/open5gs -n open5gs --values /home/wcsng-23/gitrepos/srsran-jbpf/open5gs/values.yaml
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl get pods -n open5gs -o wide
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it open5gs-populate-7796b9d4db-q79g6 -n open5gs -- open5gs-dbctl showall
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec open5gs-populate-7796b9d4db-q79g6 -n open5gs -- open5gs-dbctl add 001010123456789 00112233445566778899aabbccddeeff 63bfa50ee6523365ff14c1f45f88737d
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it open5gs-upf-59bcf7bbb8-6pz4m -n open5gs -- ip addr show
```

### Terminal 3 - start srsRAN 
```bash
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm upgrade ran . -n ran -f jrtc.yaml -f k3d-values.yaml
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash
cd /src
./make-ran.sh
./run_gnb_multi_ue.sh
```

#### Terminal 4 - jrtc controller logs 
```bash
kubectl -n ran logs -f jrtc-0
```
#### Terminall 5 - jrtc decoder logs
```bash
kubectl -n ran logs -f jrtc-0 -c jrtc-decoder
```



## Old stuff (refer for loading and unloading codelets)
### Terminal 1 - build all necessary containers
```bash
cd jrtc-apps
./init_submodules.sh
cd containers/Docker
sudo ./build_base.sh [-b base]
sudo ./build_srs_jbpf.sh [-b base] [-s janus_srsran/gnb] [-c] 

sudo ./build_srs_jbpf_sdk.sh [-s janus_srsran/gnb]
```

#### Start the open5gs core network
```bash
cd ../../..
sudo docker-compose up --build 5gc
```

### Terminal 2 - start the srsran-jbpf-sdk container
```bash
## Start the srsran-jbpf
sudo docker-compose up gnb
```
### Terminal 3 - Build and start RAN

```bash 
## Build and start the RAN
sudo docker exec -it janus_srsran_gnb bash
# tdnf install -y iproute
# tdnf update -y && tdnf install -y zeromq-devel
cd /src
rm -rf build
mkdir build
cd build
cmake -DENABLE_JBPF=on   -DCMAKE_C_FLAGS="-I/usr/include/x86_64-linux-gnu"   -DCMAKE_CXX_FLAGS="-I/usr/include/x86_64-linux-gnu" -DENABLE_EXPORT=ON -DENABLE_ZEROMQ=ON -DENABLE_DPDK=True -DINITIALIZE_SUBMODULES=OFF -DCMAKE_C_FLAGS="-Wno-error=unused-variable" ..
make -j
cd ..
ip netns add ue1 
ip netns add ue2
./run_gnb_multi_ue.sh ## gnb config file - configs/zmq-mode-multi-ue.yml
```

### Terminal 4 - Build and Run UE
```bash
## Build srsue and start the UEs
sudo docker exec -it janus_srsran_gnb bash
cd /src
cd srs-4G-UE
rm -rf build
mkdir build
cd build
#cmake -DCMAKE_C_FLAGS="-Wno-error=unused-variable" ..
#cmake -DENABLE_ZEROMQ=ON -DCMAKE_C_FLAGS="-Wno-error=unused-variable" -DCMAKE_CXX_FLAGS="-Wno-error=unused-variable" ..
cmake -DENABLE_ZEROMQ=ON \
      -DCMAKE_C_FLAGS="-Wno-error=unused-variable -Wno-error=array-bounds" \
      -DCMAKE_CXX_FLAGS="-Wno-error=unused-variable -Wno-error=array-bounds" \
      ..

make -j
tdnf install -y iputils
./srsue/src/srsue ../.config/ue1-4g-zmq.conf --params_filename="../params1.txt"
```
**todo - install gnuradio**

### Terminal 5 - Build Codelets
```bash
## Build the codelets
cd jrtc-apps
source set_vars.sh 
cd codelets
USE_JRTC=0
./make.sh -o clean
./make.sh -d /fapi_rach
```

### Terminal 6 - start the decoder in RAN container
```bash
sudo docker exec -it janus_srsran_gnb bash
/usr/local/bin/jbpf_protobuf_cli decoder run --log-level debug
```
***Output looks like - is this correct?**
```bash
root [ /out ]# /usr/local/bin/jbpf_protobuf_cli decoder run --log-level debug
DEBU[0000] starting data server                          addr="udp://[::]:20788"

OR

cd jrtc-apps
source set_vars.sh 
cd utils
USE_JRTC=0
./run_jbpf_decoder.sh
```
Q1. : Where is this running, should it run in container running RAN - janus_srsran_gnb or separate container jbpf_decoder  
Q2. WHat is this listening to, where is reverse proxy, how to see how the RAN is running?  

### Terminal 6 - loading codelets and schemas
```bash
## Create the tmp.yml for each codelet schema
\sudo -E ./load.sh -c $JBPF_CODELETS/mac/mac_stats.yaml
```

### Terminal 7
```bash
sudo docker exec -it janus_srsran_gnb bash
### Load the schema
# $JBPF_PROTOBUF_CLI_BIN decoder load -c $codeletSet_yaml # loads the schema
cd /out
source set_vars.sh 
USE_JRTC=0

/usr/local/bin/jbpf_protobuf_cli decoder load -c $JBPF_CODELETS/fapi_rach/tmp.yaml # loads the schema

### Load the codelet set
find / -name jbpf_lcm_cli 2>/dev/null # will give the jbpf_lcm_cli
/src/out/bin/jbpf_lcm_cli -a /tmp/jbpf/jbpf_lcm_ipc -l -c /out/codelets/fapi_rach/tmp.yaml
```
gnb-statefulset.yaml - reverse poxy command for srsran

### With jrtc

sudo docker-compose up --build 5gc
sudo docker-compose up gnb
sudo docker-compose up jrtc

**Start jrtc - jrtc container**
sudo docker exec -it jrtc_controller bash
cd $JRTC_PATH/
source setup_jrtc_env.sh
cd $JRTC_PATH/out/bin
./jrtc

**Start RAN and UEs - gnb container**
sudo docker exec -it janus_srsran_gnb bash
./make-ran.sh
./run_gnb_multi_ue.sh

sudo docker exec -it janus_srsran_gnb bash
./make-ue.sh
ip netns add ue1
tdnf install -y iputils
./run1ue-zmq-mode.sh

ip netns exec ue1 ping 10.45.1.1


**Start decoder on JRTC - jrtc container**
sudo docker exec -it jrtc_controller bash
cd $JRTC_PATH/sample_apps/advanced_example
./run_decoder.sh

**Start Reverse Proxy - gnb container**
sudo docker exec -it janus_srsran_gnb bash
cd /src/out/bin
./srsran_reverse_proxy --host-ip 10.53.1.3 --host-port 30450 --address "/tmp/jbpf/jbpf_lcm_ipc"

**Build codelets - bare metal**
cd jrtc-apps
source set_vars.sh 
cd codelets
USE_JRTC=1
./make.sh -o cleanall
./make.sh -d /fapi_rach
./make.sh -d /xran_packets

**Load and unload codelets**
sudo docker exec -it jrtc_controller bash
cd /out
source set_vars.sh
export JBPF_CODELETS=/out/codelets
USE_JRTC=1
/jrtc/out/bin/jrtc-ctl load -c $JRTC_APPS/xran_packets/deployment.yaml --log-level trace



### Kubenetes deployment
export USE_JRTC=1
export KUBECONFIG=~/.kube/config
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml
helm upgrade ran . -n ran -f jrtc.yaml -f k3d-values.yaml

### delete pod to upgrade
kubectl delete pod srs-gnb-du1-0 -n ran
helm upgrade ran . -n ran -f jrtc.yaml -f k3d-values.yaml
kubectl get pods -n ran

### creating kuberetes namespace
kubectl create namespace ran
kubectl get all -n ran
kubectl delete namespace ran


#### Delete the cluster
k3d cluster delete janus-cluster

#### Create the cluster
k3d cluster create janus-cluster --volume /home/wcsng-23/gitrepos/Janus-latest:/home/wcsng-23/gitrepos/Janus-latest --port "30400-30500:30400-30500@loadbalancer"

k3d kubeconfig merge janus-cluster --kubeconfig-switch-context

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl create namespace ran

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl wait --for=condition=ready pod -l app=multus -n kube-system --timeout=60s

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm install ran . -n ran -f jrtc.yaml -f k3d-values.yaml

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl get pods -n ran

#### Exec into containers
Check the container running in the pod:
kubectl get pod srs-gnb-du1-0 -n ran -o jsonpath="{.spec.containers[*].name}"

Exec into a container:
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash

#### Open5gs deployment
cd /home/wcsng-23/gitrepos/Janus-latest/open5gs
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm dependency list

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl create namespace open5gs

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm install open5gs . -n open5gs -f values-5g.yaml

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl get pods -n open5gs -o wide

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it open5gs-populate-7796b9d4db-g5hff -n open5gs -- open5gs-dbctl showall

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it open5gs-populate-7796b9d4db-g5hff -n open5gs -- open5gs-dbctl add 001010123456789 00112233445566778899aabbccddeeff 63bfa50ee6523365ff14c1f45f88737d

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it open5gs-upf-59bcf7bbb8-6pz4m -n open5gs -- ip addr show


######
##### Start the RAN - terminal 1
/home/wcsng-23/gitrepos/Janus-latest/jrtc-apps/containers/Helm
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && helm upgrade ran . -n ran -f jrtc.yaml -f k3d-values.yaml
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash
cd /src
./run_gnb_multi_ue.sh

##### jrtc controller logs - terminal 2
kubectl -n ran logs -f jrtc-0

##### jrtc decoder logs - terminal 3
kubectl -n ran logs -f jrtc-0 -c jrtc-decoder


##### loading and unloading codelets
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash
cd /apps
export JRTC_APPS=/apps
export JBPF_CODELETS=/codelets
/jrtc/out/bin/jrtc-ctl load -c /apps/xran_packets/deployment_fixed.yaml --log-level trace

