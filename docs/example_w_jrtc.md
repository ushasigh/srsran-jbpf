# Run the second example (with *jrt-controller*)

This example can be run either via container setup or on baremetal. 

### Run with Containers: 
It is assumed now that srsRAN is deployed with jrt-controller. 

To use this example, first build the xran codelets:

```
cd ~/jrtc_apps/codelets
./make.sh -d xran_packets/
```

Please note that the Errors shown in below example output can be ignored for now. 

```
Building xran_packets/
make: Entering directory '/codelet/xran_packets'
/usr/local/bin/jbpf_protobuf_cli serde -s xran_packet_info:packet_stats -w /codelet/xran_packets -o /codelet/xran_packets; \
rm -f /codelet/xran_packets/*_serializer.c /codelet/xran_packets/*.pb.c; \
if [ "1" = "1" ]; then \
        ctypesgen xran_packet_info.pb.h -I/nanopb -o xran_packet_info.py; \
fi
WARNING: No libraries specified
INFO: Status: Preprocessing /tmp/tmpgf92lcu5.h
INFO: Status: gcc -E -U __GNUC__ -dD -I"/nanopb" "-D__extension__=" "-D__const=const" "-D__asm__(x)=" "-D__asm(x)=" "-DCTYPESGEN=1" "/tmp/tmpgf92lcu5.h"
INFO: Status: Parsing /tmp/tmpgf92lcu5.h
ERROR: /nanopb/pb.h:216: Syntax error at '1'
ERROR: /nanopb/pb.h:384: Syntax error at 'sizeof'
ERROR: /usr/include/sys/cdefs.h:298: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:325: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:332: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:338: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:347: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:348: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:356: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:414: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:423: Syntax error at '\n'
ERROR: /usr/include/sys/cdefs.h:450: Syntax error at '\n'
INFO: Status: Processing description list.
WARNING: Could not parse macro "#define packet_inter_arrival_info_item_init_default { { 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 } }"
WARNING: Could not parse macro "#define data_packet_stats_item_init_default { 0 , 0 , packet_inter_arrival_info_item_init_default }"
WARNING: Could not parse macro "#define ctrl_packet_stats_item_init_default { 0 , packet_inter_arrival_info_item_init_default }"
WARNING: Could not parse macro "#define ul_packet_stats_item_init_default { data_packet_stats_item_init_default }"
WARNING: Could not parse macro "#define dl_packet_stats_item_init_default { data_packet_stats_item_init_default , ctrl_packet_stats_item_init_default }"
WARNING: Could not parse macro "#define packet_stats_init_default { 0 , ul_packet_stats_item_init_default , dl_packet_stats_item_init_default }"
WARNING: Could not parse macro "#define packet_inter_arrival_info_item_init_zero { { 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 } }"
WARNING: Could not parse macro "#define data_packet_stats_item_init_zero { 0 , 0 , packet_inter_arrival_info_item_init_zero }"
WARNING: Could not parse macro "#define ctrl_packet_stats_item_init_zero { 0 , packet_inter_arrival_info_item_init_zero }"
WARNING: Could not parse macro "#define ul_packet_stats_item_init_zero { data_packet_stats_item_init_zero }"
WARNING: Could not parse macro "#define dl_packet_stats_item_init_zero { data_packet_stats_item_init_zero , ctrl_packet_stats_item_init_zero }"
WARNING: Could not parse macro "#define packet_stats_init_zero { 0 , ul_packet_stats_item_init_zero , dl_packet_stats_item_init_zero }"
WARNING: Could not parse macro "#define data_packet_stats_item_FIELDLIST(X,a) X ( a , STATIC , REQUIRED , UINT32 , Packet_count , 1 ) X ( a , STATIC , REQUIRED , UINT64 , Prb_count , 2 ) X ( a , STATIC , REQUIRED , MESSAGE , packet_inter_arrival_info , 3 )"
WARNING: Could not parse macro "#define ctrl_packet_stats_item_FIELDLIST(X,a) X ( a , STATIC , REQUIRED , UINT32 , Packet_count , 1 ) X ( a , STATIC , REQUIRED , MESSAGE , packet_inter_arrival_info , 2 )"
WARNING: Could not parse macro "#define dl_packet_stats_item_FIELDLIST(X,a) X ( a , STATIC , REQUIRED , MESSAGE , data_packet_stats , 1 ) X ( a , STATIC , REQUIRED , MESSAGE , ctrl_packet_stats , 2 )"
WARNING: Could not parse macro "#define packet_stats_FIELDLIST(X,a) X ( a , STATIC , REQUIRED , UINT64 , timestamp , 1 ) X ( a , STATIC , REQUIRED , MESSAGE , ul_packet_stats , 2 ) X ( a , STATIC , REQUIRED , MESSAGE , dl_packet_stats , 3 )"
ERROR: Undef "NULL" depends on an unknown identifier "NULL". Undef "NULL" will not be output
ERROR: Undef "NULL" depends on an unknown identifier "NULL". Undef "NULL" will not be output
ERROR: Undef "NULL" depends on an unknown identifier "NULL". Undef "NULL" will not be output
ERROR: Macro "packet_inter_arrival_info_item_FIELDLIST" depends on an unknown identifier "STATIC". Macro "packet_inter_arrival_info_item_FIELDLIST" will not be output
ERROR: 3 more errors for Macro "packet_inter_arrival_info_item_FIELDLIST"
ERROR: Macro "ul_packet_stats_item_FIELDLIST" depends on an unknown identifier "STATIC". Macro "ul_packet_stats_item_FIELDLIST" will not be output
ERROR: 3 more errors for Macro "ul_packet_stats_item_FIELDLIST"
INFO: Status: Writing to xran_packet_info.py.
INFO: Status: Wrapping complete.
make: Leaving directory '/codelet/xran_packets'
```


Open four seperate terminals and make sure to set environment in each terminal:

```
cd ~/jrtc-apps
source set_vars.sh
```

Now, in Terminal-1, start the srsRAN logs:

```
kubectl -n ran logs -f srs-gnb-du1-0 -c gnb
```

In Terminal-2, start the jrtc logs:

```
kubectl -n ran logs -f jrtc-0
```


In Terminal-3, start the jrtc-decoder logs:

```
kubectl -n ran logs -f jrtc-0 -c jrtc-decoder
```

In Terminal-4, load the codelet:

```
cd ~/jrtc_apps/jrtc_apps
./load.sh -y xran_packets/deployment.yaml
```

Once the codelet is loaded successfully, we should see the following logs in each terminal:

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

### Run without Container: 

In this example we will use the xRAN codelets from the [example](./example_no_jrtc.md) without *jrt-controller*, and we will feed their input into a sample *jrt-controller* app. 

**Important:** There are several artifacts of the build that have to be rebuilt for different environments.   
If you switch from the example that doesn't use *jrt-controller* to the example that does, you need to make sure all of them are rebuilt. 
We advise you to do a clean clone of the repo in that case. 


## Configuring the components

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



## Running the example

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

Terminal running *jrt-controller*:
```sh
cd $JRTC_PATH/out/bin
./jrtc
```

Terminal running *srsRAN*: 
```sh
cd  $SRSRAN_DIR/build/apps/gnb
sudo ./gnb -c modified_conf_to_include_jbpf.yml
```

Terminal running the *jrt-controller* decoder (see [here](https://github.com/microsoft/jrt-controller/blob/main/docs/understand_advanced_app.md) for more info): 
```sh
cd $JRTC_PATH/sample_apps/advanced_example
./run_decoder.sh
```

Terminal running the *jbpf* reverse proxy (see [here](https://github.com/microsoft/jbpf/tree/main/examples/reverse_proxy) for more info):
```sh
sudo -E $SRSRAN_DIR/out/bin/srsran_reverse_proxy --host-port 30450 --address "/tmp/jbpf/jbpf_lcm_ipc"
```

Terminal that loads *jbpf* codelets and *jrt-controller* apps for *srsRAN*:
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

