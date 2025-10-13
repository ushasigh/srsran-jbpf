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
k3d cluster delete janus-cluster

#### Create the cluster
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

### Open5gs deployment
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