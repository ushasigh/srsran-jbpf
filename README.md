# Introduction

This project provides a number of sample applications for instrumenting srsRAN through 
[jbpf](https://github.com/microsoft/jbpf) and [jrt-controller](https://github.com/microsoft/jrt-controller) frameworks.



# Getting started

## Set up the environment

You need to use and build a version of srsRAN_platform with jbpf enabled. 
Please follow the instructions from the [repo](https://github.com/xfoukas/srsRAN_Project_jbpf). 

Start by initializing the submodules:
```sh
./init_submodules.sh
```
Then go to the folder `jbpf-protobuf` and build the submodule using the instructions in the [repo](https://github.com/microsoft/jbpf-protobuf). 
You should do this only once after cloning the repo.


Then set up the environment variables:
```sh
export SRSRAN_DIR=<path_to_your_srsRAN_with_jbpf>
source set_vars.sh
```
You should do this in every terminal window where you run the commands. 



## Run the examples

We provide two example. 
* The [first example](./docs/example_no_jrtc.md) does not use *jrt-controller* and only streams data collected by *jbpf* to a local decoder that prints it on a screen. 
* The [second example](./docs/example_w_jrtc.md) shows how to use both *jbpf* and *jrt-controller*. 



# License

This framework is licensed under the [MIT license](LICENSE.md).

