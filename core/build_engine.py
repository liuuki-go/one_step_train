import os
import sys
import time
import tensorrt as trt

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model')
ONNX_PATH = os.path.join(MODEL_DIR, 'best.onnx')
ENGINE_PATH = os.path.join(MODEL_DIR, 'best.engine')
IMG_SIZE = int(os.environ.get('IMG_SIZE', '960'))

logger = trt.Logger(trt.Logger.INFO)  #type: ignore
trt.init_libnvinfer_plugins(logger, namespace="") #type: ignore

print(f"[Build] ONNX: {ONNX_PATH}")
print(f"[Build] Target engine: {ENGINE_PATH}")
print(f"[Build] IMG_SIZE: {IMG_SIZE}")

if not os.path.exists(ONNX_PATH):
    print("[Build] ERROR: ONNX file not found.")
    sys.exit(1)

builder = trt.Builder(logger) #type: ignore
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) #type: ignore
parser = trt.OnnxParser(network, logger) #type: ignore

with open(ONNX_PATH, 'rb') as f:
    onnx_bytes = f.read()

print("[Build] Parsing ONNX...")
if not parser.parse(onnx_bytes):
    print("[Build] ERROR: ONNX parse failed:")
    for i in range(parser.num_errors):
        print(f"  - {parser.get_error(i)}")
    sys.exit(1)

config = builder.create_builder_config()
config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 16 << 30)  # 1GB #type: ignore
if builder.platform_has_fast_fp16:
    config.set_flag(trt.BuilderFlag.FP16) #type: ignore

profile = builder.create_optimization_profile()
input_name = network.get_input(0).name
min_shape = (1, 3, 640, 640)  
opt_shape = (1, 3, 960, 960)   
max_shape = (1, 3, 960, 960)  
profile.set_shape(input_name, min_shape, opt_shape, max_shape)
config.add_optimization_profile(profile)

print("[Build] Building serialized network...")
start = time.time()
serialized = builder.build_serialized_network(network, config)
elapsed = time.time() - start
if serialized is None:
    print("[Build] ERROR: build_serialized_network failed")
    sys.exit(1)
print(f"[Build] Serialized network built in {elapsed:.2f}s")

runtime = trt.Runtime(logger)  #type: ignore
engine = runtime.deserialize_cuda_engine(serialized)
if engine is None:
    print("[Build] ERROR: Engine deserialize failed")
    sys.exit(1)

print(f"[Build] Serializing to {ENGINE_PATH}...")
with open(ENGINE_PATH, 'wb') as f:
    f.write(serialized)  # 跳过中间反序列化步骤
print("[Build] Done.")