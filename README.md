# Introduction

This project provides a collection of sample applications for instrumenting **srsRAN** using the  
[jbpf](https://github.com/microsoft/jbpf) and [jrt-controller](https://github.com/microsoft/jrt-controller) frameworks.

# Getting Started

There are two ways to start the setup - with Kubernetes or on Baremetal. 

By default, everything runs as containers and there is no need to install any external dependencies. 

## Running with Kubernetes Containers:

### Environment Setup

Before starting, ensure that **Kubernetes** is installed and configured.  
This guide assumes **srsRAN** will be deployed using **Helm**.

### Preparing the Environment

1. Initialize submodules:

    ```bash
    cd ~/jbpf_apps
    ./init_submodules.sh
    ```

2. Set required environment variables:

    ```bash
    source set_vars.sh
    ```

3. There are two ways to start the srsRAN deployment:
   - with JRTC
   - without JRTC - this will deploy srsRAN with jbpf

4. To start the srsRAN, move the the ***jrtc-apps/containers/Helm*** directory and make sure that parameters `related to local setup, such as Core IP, RRH, Local MAC Address, and VLAN ID are correctly configured either in the `values.yaml` or supplied via a separate YAML file. 

    The easiest way to configure parameters related to local setup is to supply them via seperate yaml file - lets say config.yaml. Here is an example `config.yaml`. Please note that `config.yaml` will overwrite parameters in the `values.yaml` file.

    ```
    duConfigs:
      du1:
        cells:
          cell1:
            cellID: 1
            ruNAME: "RRH"
            ruLocalMAC: "00:11:22:33:0a:a6" 
            ruRemoteMAC: "6c:ad:ad:00:0a:a6"
            ruVLAN: "1"
            physicalCellID: 1

    cell_cfg:
      plmn: "00101"

    ngcParams:
      coreIP: 192.168.101.50 
      tac: "000001" 
      plmn: "00101" 
    ```


  Once the parameters are configured correctly we can deploy srsRAN

  `Deploy RAN with jrtc:`

  ```
  cd ~/jrtc-apps/containers/Helm
  ./install.sh -h . -f config.yaml -f jrtc.yaml
  ```

  `Deploy RAN without jrtc:`

  ```
  ./install.sh -h . -f config.yaml
  ```

  
  Expected output:

  ```
  NAME            READY   STATUS    RESTARTS   AGE
  jrtc-0          2/2     Running   0          11s
  srs-gnb-du1-0   3/3     Running   0          11s
  ```

4. Run the following command to check the status of the deployment:

  ```bash
  kubectl get pods -n ran
  ```

  Expected output:

  ```
  NAME            READY   STATUS    RESTARTS   AGE
  srs-gnb-du1-0   3/3     Running   0          11s
  ```

---

## Running the Examples

This project includes two examples:

- [Example 1](./docs/example_no_jrtc.md):  
  Demonstrates data collection using *jbpf* only. Data is streamed to a local decoder and printed on-screen.

- [Example 2](./docs/example_w_jrtc.md):  
  Demonstrates integrated usage of both *jbpf* and *jrt-controller*.

---

# License

This project is licensed under the [MIT License](LICENSE.md).

---