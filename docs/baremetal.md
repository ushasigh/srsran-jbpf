# Baremetal Setup

This project provides a collection of sample applications for instrumenting **srsRAN** using the  
[jbpf](https://github.com/microsoft/jbpf) and [jrt-controller](https://github.com/microsoft/jrt-controller) frameworks.

# Getting started

The following instructions are for the `baremetal setup`.
For Kubernetes-based installation, please follow [these instructions](../README.md)

### Preparing the Environment

A version of srsRAN_platform with jBPF enabled must be built and used. Please follow the instructions from the [repo](https://github.com/xfoukas/srsRAN_Project_jbpf). 


#### Initialize submodules:

```bash
cd ~/jbpf_apps
./init_submodules.sh
```

Then go to the folder `jbpf-protobuf` and build the submodule using the instructions in the [repo](https://github.com/microsoft/jbpf-protobuf). 
You should do this only once after cloning the repo.


#### Set required environment variables:

```sh
export SRSRAN_DIR=<path_to_your_srsRAN_with_jbpf>
source set_vars.sh
```

You should do this in every terminal window where you run the commands. 

## Running the Examples

This project includes two examples:

- [Example 1](./example_no_jrtc.md):  
  Demonstrates data collection without using *jrt-controller*. Data is streamed to a local decoder and printed on-screen.

- [Example 2](./example_w_jrtc_baremetal.md):  
  Demonstrates data collection using *jrt-controller*.  Data is transferred from srsRAN to *jrt-controller* via shared memory.
   

# License

This project is licensed under the [MIT License](LICENSE.md).