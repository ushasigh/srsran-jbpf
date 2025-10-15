### loading
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c '
export JBPF_CODELETS=/codelets && export JRTC_APPS=/apps && 
/jrtc/out/bin/jrtc-ctl load -c /apps/xran_packets/deployment_fixed.yaml --log-level debug'

kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X POST \
-H "Content-Type: application/json" \
-v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450 \
--data @/tmp/codelet_payload.json
```

### Unloading
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c '
export JBPF_CODELETS=/codelets && export JRTC_APPS=/apps && 
/jrtc/out/bin/jrtc-ctl unload -c /apps/xran_packets/deployment_fixed.yaml --log-level debug'

kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE \
    -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/xran_packets
```


```bash
export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it jrtc-0 -n ran -c jrtc -- ls -la /out/utils/

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c 'export JRTC_APPS=/apps; export JBPF_CODELETS=/codelets; cat > /tmp/codelet_payload.json << "EOF"
{
  "codelet_descriptor": [
    {
      "codelet_path": "/codelets/xran_packets/xran_packets_collect.o",
      "hook_name": "capture_xran_packet",
      "codelet_name": "collector",
      "priority": 1
    },
    {
      "codelet_path": "/codelets/xran_packets/xran_packets_report.o",
      "hook_name": "report_stats",
      "linked_maps": [
        {
          "linked_codelet_name": "collector",
          "linked_map_name": "output_tmp_map",
          "map_name": "output_tmp_map"
        }
      ],
      "codelet_name": "reporter",
      "out_io_channel": [
        {
          "name": "output_map",
          "stream_id": "000813d82e92aa151cfa732f0a2f6ec2",
          "serde": {
            "file_path": "/codelets/xran_packets/xran_packet_info:packet_stats_serializer.so"
          }
        }
      ],
      "priority": 2
    }
  ],
  "codeletset_id": "xran_packets"
}
EOF'

export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X POST -H "Content-Type: application/json" -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450 --data @/tmp/codelet_payload.json


export KUBECONFIG=/home/wcsng-23/.config/k3d/kubeconfig-janus-cluster.yaml && kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/xran_packets








# Troubleshooting: Codelet Deployment in Kubernetes Environment

## Problem Summary

When deploying JRTC applications in Kubernetes using `jrtc-ctl load`, you may encounter a "400 Bad Request" error followed by connection failures to the JBPF agent. This document provides the root cause analysis and solution.

## Error Symptoms

```bash
INFO[0000] loaded app                                    id=6 startTime="2025-08-13 03:26:27.916256582 +0000 UTC"
TRAC[0000] sending http request                          method=POST url="http://127.0.0.1:30450"
Error: Post "http://127.0.0.1:30450": dial tcp 127.0.0.1:30450: connect: connection refused
```

## Root Cause

The `jrtc-ctl` tool is hardcoded to use `127.0.0.1` for JBPF device connections, but in Kubernetes environments, the reverse proxy is accessible via service names, not localhost.

## Architecture Overview

### Container Deployment
The `srs-gnb-du1-0` pod contains three containers:
- **`troubleshooter`**: Debugging container
- **`gnb`**: Main gNodeB application
- **`srs-gnb-proxy`**: Reverse proxy for JBPF communication

### Service Endpoints
- JRTC Service: `jrtc-service.ran.svc.cluster.local:3001`
- JBPF Reverse Proxy: `srs-gnb-du1-proxy.ran.svc.cluster.local:30450`
- JRTC Decoder: `jrtc-decoder.ran.svc.cluster.local:20789`

## Solution

### Method 1: Manual Codelet Deployment (Recommended)

When `jrtc-ctl load` fails at the codelet deployment step, you can manually deploy the codelets:

#### Step 1: Prepare the Codelet Payload
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c 'cat > /tmp/codelet_payload.json << "EOF"
{
  "codelet_descriptor": [
    {
      "codelet_path": "/codelets/xran_packets/xran_packets_collect.o",
      "hook_name": "capture_xran_packet",
      "codelet_name": "collector",
      "priority": 1
    },
    {
      "codelet_path": "/codelets/xran_packets/xran_packets_report.o",
      "hook_name": "report_stats",
      "linked_maps": [
        {
          "linked_codelet_name": "collector",
          "linked_map_name": "output_tmp_map",
          "map_name": "output_tmp_map"
        }
      ],
      "codelet_name": "reporter",
      "out_io_channel": [
        {
          "name": "output_map",
          "stream_id": "000813d82e92aa151cfa732f0a2f6ec2",
          "serde": {
            "file_path": "/codelets/xran_packets/xran_packet_info:packet_stats_serializer.so"
          }
        }
      ],
      "priority": 2
    }
  ],
  "codeletset_id": "xran_packets"
}
EOF'
```

#### Step 2: Deploy to Reverse Proxy
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X POST \
  -H "Content-Type: application/json" \
  -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450 \
  --data @/tmp/codelet_payload.json
```

#### Expected Success Response
```
< HTTP/1.1 201 Created
< Server: 0.1.0-
< Content-Length: 0
```

### Method 2: Fix Deployment Configuration

Update your `deployment_fixed.yaml` to include the correct host for JBPF devices:

```yaml
jbpf:
  device:
    - id: 1
      host: srs-gnb-du1-proxy.ran.svc.cluster.local
      port: 30450
```

**Note**: This may not work due to `jrtc-ctl` hardcoded defaults, but it's worth trying.

## Complete Deployment Process

### 1. Load the Application
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c '
export JRTC_APPS=/apps
export JBPF_CODELETS=/codelets
/jrtc/out/bin/jrtc-ctl load -c /apps/xran_packets/deployment_fixed.yaml --log-level trace
'
```

### 2. If Codelet Deployment Fails
Follow the manual deployment steps above.

### 3. Verify Deployment
```bash
# Check app is loaded
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -s http://127.0.0.1:3001/app | grep -o '"app_name":"[^"]*"'

# Check JRTC logs
kubectl logs jrtc-0 -n ran -c jrtc --tail=10
```

## Troubleshooting Commands

### Check Pod Status
```bash
kubectl get pods -n ran
kubectl get services -n ran
```

### Check Container Logs
```bash
# JRTC Controller logs
kubectl logs jrtc-0 -n ran -c jrtc --tail=20

# JRTC Decoder logs  
kubectl logs jrtc-0 -n ran -c jrtc-decoder --tail=20

# gnb logs
kubectl logs srs-gnb-du1-0 -n ran -c gnb --tail=20

# Reverse proxy logs
kubectl logs srs-gnb-du1-0 -n ran -c srs-gnb-proxy --tail=20
```

### Test Connectivity
```bash
# Test JRTC service
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -v http://127.0.0.1:3001/app

# Test reverse proxy
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/
```

### Unload Application
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c '
export JRTC_APPS=/apps
export JBPF_CODELETS=/codelets
/jrtc/out/bin/jrtc-ctl unload -c /apps/xran_packets/deployment_fixed.yaml --log-level trace
'
```

## Unloading Codelets

### Method 1: Using jrtc-ctl (May Fail)
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- bash -c '
export JRTC_APPS=/apps
export JBPF_CODELETS=/codelets
/jrtc/out/bin/jrtc-ctl unload -c /apps/xran_packets/deployment_fixed.yaml --log-level trace
'
```

**Note**: This may fail with the same "connection refused" error when trying to clean up codelets from the JBPF agent.

### Method 2: Manual Codelet Unloading (Recommended)

If `jrtc-ctl unload` fails at the codelet cleanup step, you can manually unload them:

#### Step 1: Get the Codelet Set ID
The codelet set ID is typically the name from your deployment (e.g., "xran_packets").

#### Step 2: Unload from Reverse Proxy
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE \
  -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/xran_packets
```

#### Expected Success Response
```
< HTTP/1.1 200 OK
< Server: 0.1.0-
< Content-Length: 0
```

### Method 3: Complete Manual Unload Process

If you need to completely unload everything manually:

#### Step 1: Unload App from JRTC
```bash
# Get the app ID first
APP_ID=$(kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -s http://127.0.0.1:3001/app | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

# Unload the app
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE \
  -v http://127.0.0.1:3001/app/$APP_ID
```

#### Step 2: Unload Codelets from JBPF Agent
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE \
  -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/xran_packets
```

#### Step 3: Disassociate Stream (Optional)
This is usually handled automatically, but if needed, you can manually disassociate streams using the decoder API.

## Verification After Unload

### Check App is Unloaded
```bash
# Should return empty array or not include your app
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -s http://127.0.0.1:3001/app
```

### Check JRTC Logs
```bash
kubectl logs jrtc-0 -n ran -c jrtc --tail=10
```

Look for messages like:
- `INFO[0000] unloading app`
- `INFO[0000] unloaded app`
- `INFO[0000] successfully disassociated stream ID`

## Common Unload Issues

### "Connection Refused" During Unload
- **Cause**: Same as load - hardcoded localhost in `jrtc-ctl`
- **Solution**: Use manual unload methods above

### App Unloaded but Codelets Still Running
- **Cause**: Codelet cleanup failed but app removal succeeded
- **Solution**: Use Method 2 to manually unload codelets

### Partial Unload Success
If `jrtc-ctl unload` succeeds partially, you'll see:
```bash
INFO[0000] unloaded app
INFO[0000] successfully disassociated stream ID with proto package
Error: Delete "http://127.0.0.1:30450/xran_packets": dial tcp 127.0.0.1:30450: connect: connection refused
```

In this case, just run the manual codelet unload:
```bash
kubectl exec -it jrtc-0 -n ran -c jrtc -- curl -X DELETE \
  -v http://srs-gnb-du1-proxy.ran.svc.cluster.local:30450/xran_packets
```

## Success Indicators

1. **App Loaded**: `INFO[0000] loaded app id=X startTime="..."`
2. **Schema Loaded**: `INFO[0000] successfully upserted proto package`
3. **Stream Associated**: `INFO[0000] successfully associated stream ID`
4. **Codelets Deployed**: `HTTP/1.1 201 Created` from reverse proxy
5. **App Running**: App appears in `curl http://127.0.0.1:3001/app`

## Common Issues

### "400 Bad Request" on Load
- **Cause**: App already loaded
- **Solution**: Unload first, then reload

### "Connection Refused" to 127.0.0.1:30450
- **Cause**: Hardcoded localhost in `jrtc-ctl`
- **Solution**: Use manual codelet deployment method

### "Empty Reply from Server" 
- **Cause**: Wrong endpoint or payload format
- **Solution**: Verify service name and JSON payload

## Environment Variables

Required environment variables for `jrtc-ctl`:
```bash
export JRTC_APPS=/apps
export JBPF_CODELETS=/codelets
```

## Files Involved

- `/apps/xran_packets/deployment_fixed.yaml` - Deployment configuration
- `/codelets/xran_packets/` - Codelet binaries and configurations
- `/apps/xran_packets/xran_packets.py` - Python application

## Related Documentation

- [Ushasi-readme.md](./Ushasi-readme.md) - Main deployment guide
- [jrtc-apps/README.md](./jrtc-apps/README.md) - JRTC applications documentation 

## JBPF Agent Issues

If you see association removal messages like:
```
INFO[2735] association removed                           protoMsg=packet_stats protoPackage=xran_packet_info streamUUID=000ff3d82e92aa151cfa732f0a2f6ec2
DEBU[3285] no association found for stream UUID          streamUUID=000ff3d82e92aa151cfa732f0a2f6ec2
```

This indicates the JBPF agent has stopped or IPC is disabled.

### Check JBPF Configuration

```bash
# Check if JBPF IPC is enabled in the gnb configuration
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash -c 'grep -A5 "jbpf:" /usr/local/share/srsran/jbpf_gnb_config.yml'
```

If you see `jbpf_enable_ipc: 0`, then JBPF IPC is disabled and needs to be enabled.

### Check JBPF Agent Status

```bash
# Check if JBPF agent process is running
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash -c 'ps aux | grep jbpf'

# Check if IPC socket exists
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash -c 'ls -la /tmp/jbpf/'
```

### Solution: Enable JBPF IPC

To fix the issue, you need to:

1. **Enable JBPF IPC** by changing `jbpf_enable_ipc: 0` to `jbpf_enable_ipc: 1` in the gnb configuration
2. **Restart the gnb process** to apply the changes
3. **Reload the codelets** once JBPF agent is running again

```bash
# The configuration file is typically at:
# /usr/local/share/srsran/jbpf_gnb_config.yml
# 
# Change:
#   jbpf_enable_ipc: 0
# To:
#   jbpf_enable_ipc: 1
#
# Then restart the gnb process
```

### Restart Process

After enabling JBPF IPC, restart the gnb to start the JBPF agent:

```bash
# Find and kill the current gnb process
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash -c 'pkill gnb'

# The container should restart automatically, or manually start gnb again
kubectl exec -it srs-gnb-du1-0 -n ran -c gnb -- bash -c 'cd /opt/srsRAN_Project/build/apps/gnb && ./gnb -c ../../../configs/zmq-mode-multi-operator/gnb_zmq_with_cucp_du_1.yml'
```

After restart, verify JBPF agent is running and reload your codelets. 
