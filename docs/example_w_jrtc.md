# Run the second example (with *jrt-controller*)

This example can be run either via container setup or on baremetal. 

## Run with Containers: 
It is assumed now that srsRAN is deployed with jrt-controller. 

To use this example, first build the xran codelets:

```
cd ~/jrtc_apps/codelets
./make.sh -d xran_packets/
```
*Note: when this is run you'll see output similar to the following* ...

```sh
ERROR: /nanopb/pb.h:216: Syntax error at '1'
ERROR: /nanopb/pb.h:384: Syntax error at 'sizeof'
ERROR: /usr/include/sys/cdefs.h:298: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:325: Syntax error at '\n'
...
...
WARNING: Could not parse macro "#define t_ta_hist_init_default { 0 , 0 }"
WARNING: Could not parse macro "#define t_pwr_hist_init_default { 0 , 0 }"
...
...
ERROR: Undef "NULL" depends on an unknown identifier "NULL". Undef "NULL" will not be output
ERROR: Undef "NULL" depends on an unknown identifier "NULL". Undef "NULL" will not be output
INFO: Status: Writing to fapi_gnb_rach_stats.py.
INFO: Status: Wrapping complete.
--------- fapi_gnb_rach_stats_collect.cpp ----------------------------------------------
clang++ -O2 -target bpf -Wall -std=gnu++17 -DJBPF_EXPERIMENTAL_FEATURES -DJBPF_DEBUG_ENABLED -D__x86_64__ -fpermissive -Wno-incompatible-pointer-types -Wno-pedantic  -I/src/out/inc -I/src/include -I/nanopb -I/src/external -I/src/external/fmt/include -I/usr/include/c++/13.2.0 -I/usr/include/c++/13.2.0/x86_64-pc-linux-gnu  -c fapi_gnb_rach_stats_collect.cpp -o fapi_gnb_rach_stats_collect.o
/src/out/bin/srsran_verifier_cli fapi_gnb_rach_stats_collect.o || echo "fapi_gnb_rach_stats_collect.cpp: Failed verification"

48:53: Code is unreachable after 48:53
56:61: Code is unreachable after 56:61
60:177: Code is unreachable after 60:177
94:61: Code is unreachable after 94:61
151:61: Code is unreachable after 151:61

1,0.077681
Program terminates within 2067 instructions
```
These errors toward the top bcan actually be ignored.  They are output by the "ctypesgen" command, but are not issues that have any impact.  The codelet's compilation/verification result is shown in the lines ...
```sh
1,0.016758
Program terminates within 333 instructions
``` 
When this starts with "1," it means it is successful.  In failures cases, it will start with "0,".


Open four seperate terminals.
In each window, set up the environment variables as described [here](../README.md#Preparing-the-Environment).

The srsRAN and JRTC are started as shown [here](../README.md#Start-the-srsRAN).

### Terminal 1

Monitor the srsRAN logs:
```
kubectl -n ran logs -f srs-gnb-du1-0 -c gnb
```

### Terminal 2

Monitor the jrt-controllerc logs:
```
kubectl -n ran logs -f jrtc-0
```

### Terminal 3

Montor the jrt-decoder logs:
```
kubectl -n ran logs -f jrtc-0 -c jrtc-decoder
```

### Terminal 4

Load the codelet:
```
cd ~/jrtc_apps/jrtc_apps
./load.sh -y xran_packets/deployment.yaml
```

Expected output:

Once the codeletSet is loaded successfully, one should see the following logs in each terminal:

Terminal 1 (srsRAN logs)- 

```
[2025-04-17T11:25:24.025208Z] [JBPF_INFO]: Registered codelet collector to hook capture_xran_packet
[2025-04-17T11:25:24.025211Z] [JBPF_INFO]: ----------------- capture_xran_packet: collector ----------------------
[2025-04-17T11:25:24.025214Z] [JBPF_INFO]: hook_name = capture_xran_packet, priority = 1, runtime_threshold = 0
[2025-04-17T11:25:24.025216Z] [JBPF_INFO]: Codelet created and loaded successfully: collector
[2025-04-17T11:25:24.025221Z] [JBPF_INFO]: Registered codelet reporter to hook report_stats
[2025-04-17T11:25:24.025224Z] [JBPF_INFO]: ----------------- report_stats: reporter ----------------------
[2025-04-17T11:25:24.025226Z] [JBPF_INFO]: hook_name = report_stats, priority = 2, runtime_threshold = 0
[2025-04-17T11:25:24.025229Z] [JBPF_INFO]: Codelet created and loaded successfully: reporter
[2025-04-17T11:25:24.025239Z] [JBPF_DEBUG]: Codeletset is loaded OK 0
```

Terminal 2 (jrtc logs)-

```
Hi App 1: timestamp: 1744887825600324096
DL Ctl: 12884 [9663, 961, 205, 94, 116, 31, 1, 0, 0, 0, 1567, 196, 50, 0, 0, 0]
DL Data: 83672 8869232 [62672, 81, 0, 1, 0, 1, 2706, 18009, 0, 0, 0, 0, 202, 0, 0, 0]
```

Terminal 3 (jrtc-decoder logs)- 

```
INFO[1520] REC: {"timestamp":"1744889030083753984","ulPacketStats":{"dataPacketStats":{"PacketCount":10616,"PrbCount":"669584","packetInterArrivalInfo":{"hist":[0,0,619,2814,1611,3898,1519,3,0,0,0,0,0,51,51,50]}}},"dlPacketStats":{"dataPacketStats":{"PacketCount":83728,"PrbCount":"8875168","packetInterArrivalInfo":{"hist":[62701,93,0,2,0,3,3195,17533,0,0,0,0,201,0,0,0]}},"ctrlPacketStats":{"PacketCount":12896,"packetInterArrivalInfo":{"hist":[9682,927,201,110,131,31,0,0,0,0,1614,151,49,0,0,0]}}}}  streamUUID=001013d8-2e92-aa15-1cfa-732f0a2f6ec2
recv "001013d82e92aa151cfa732f0a2f6ec20880f6ceb4c3eac59b1812220a2008a85510b0822b1a170a1500009d05c217a40dd31db60c0300000000003434311a440a2308a08d0510c0fc9c041a180a16c0e9033105020001a415ba8c0100000000c901000000121d08e46412180a16d54bb207ad01718c011c00000000d00c960131000000"(132)
```

To unload the codelet, run the following command:

```
cd ~/jrtc-apps/jrtc_apps
./unload.sh -y xran_packets/deployment.yaml
```

## Run without Container: 

In this example we will use the xRAN codelets from the [example](./example_no_jrtc.md) without *jrt-controller*, and we will feed their input into a sample *jrt-controller* app. 

**Important:** There are several artifacts of the build that have to be rebuilt for different environments.   
If you switch from the example that doesn't use *jrt-controller* to the example that does, you need to make sure all of them are rebuilt. 
We advise you to do a clean clone of the repo in that case. 


### Configuring the components

To use *jrt-controller* with the examples in this repo, we need to set the env variable `USE_JRTC=1`. 
The default environment options are in file __".env"__. 
If you wish to override any of these variables, create a separate file called __".env.local"__, with variable which should be overwritten, for example:-
```sh
USE_JRTC=1
```
These overrides will occur when __set_vars.sh__ is executed.
You also need to define a path to your instance of jrt-controller, e.g.:
```sh
export JRTC_PATH=~/jrt-controller/
```
and then set the environment variables as described in the [README](../README.md). 


Next, you need to modify the srsRAN config file with the following section:
```yaml
jbpf:
  jbpf_run_path: "/tmp"
  jbpf_namespace: "jbpf"
  jbpf_enable_ipc: 1
  jbpf_standalone_io_out_ip: "127.0.0.1"
  jbpf_standalone_io_out_port: 20788
  jbpf_standalone_io_in_port: 30400
  jbpf_standalone_io_policy: 0
  jbpf_standalone_io_priority: 0
  jbpf_io_mem_size_mb: 1024
  jbpf_ipc_mem_name: "jrt_controller"
  jbpf_enable_lcm_ipc: 1
  jbpf_lcm_ipc_name: "jbpf_lcm_ipc"
  jbpf_agent_cpu: 0
  jbpf_agent_policy: 1
  jbpf_agent_priority: 30
  jbpf_maint_cpu: 0
  jbpf_maint_policy: 0
  jbpf_maint_priority: 0
```



#### Running the example

To run the example, we need 5 terminals. 
In each of these, you need to set the following environment variables:
```sh
export JRTC_PATH=~/jrt-controller/
export SRSRAN_DIR=~/srsRAN_Project/
export SRSRANAPP_DIR=~/jrtc-apps/
source $SRSRANAPP_DIR/set_vars.sh
```
The example uses sample path values. 
Please edit for your system.
Next, run the following in the terminals. 

##### Terminal 1

Run *jrt-controller*:
```sh
cd $JRTC_PATH/out/bin
./jrtc
```

##### Terminal 2

Run *srsRAN*: 
```sh
cd  $SRSRAN_DIR/build/apps/gnb
sudo ./gnb -c modified_conf_to_include_jbpf.yml
```

##### Terminal 3

Run the *jrt-controller* decoder (see [here](https://github.com/microsoft/jrt-controller/blob/main/docs/understand_advanced_app.md) for more info): 
```sh
cd $JRTC_PATH/sample_apps/advanced_example
./run_decoder.sh
```

##### Terminal 4

Run the *jbpf* reverse proxy (see [here](https://github.com/microsoft/jbpf/tree/main/examples/reverse_proxy) for more info):
```sh
sudo -E $SRSRAN_DIR/out/bin/srsran_reverse_proxy --host-port 30450 --address "/tmp/jbpf/jbpf_lcm_ipc"
```

##### Terminal 5

Load the *jbpf* codelets and *jrt-controller* apps for *srsRAN*:

First build the codelets:
```sh
cd $SRSRANAPP_DIR/codelets
./make.sh -o cleanall
./make.sh
```

Load and unload the [xran_packets](../jrtc_apps/xran_packets/) examples:
```sh
# load the xran_packets deployment
cd $JRTC_APPS
./load.sh -y $JRTC_APPS/xran_packets/deployment.yaml
# you should now see the decoder
./unload.sh -y $JRTC_APPS/xran_packets/deployment.yaml
```

Load and unload the [fapi](../jrtc_apps/fapi/) examples: 
```sh
# load the fapi deployment
cd $JRTC_APPS
./load.sh -y $JRTC_APPS/fapi/deployment.yaml
# you should now see the decoder
./unload.sh -y $JRTC_APPS/fapi/deployment.yaml
```

