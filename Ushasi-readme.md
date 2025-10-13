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
cd /home/wcsng-23/gitrepos/Janus-latest/Janus-v2/open5gs
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
