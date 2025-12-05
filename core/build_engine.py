import os
import sys
import time
import argparse
import tensorrt as trt

def build(onnx_path, engine_path, img_size=960, workspace_gb=16, min_mem=None):
    logger = trt.Logger(trt.Logger.INFO) #type: ignore
    trt.init_libnvinfer_plugins(logger, namespace="") #type: ignore

    print(f"[Build] ONNX: {onnx_path}")
    print(f"[Build] Target engine: {engine_path}")
    print(f"[Build] IMG_SIZE: {img_size}")
    print(f"[Build] Workspace Limit: {workspace_gb} GB")

    if not os.path.exists(onnx_path):
        print("[Build] ERROR: ONNX file not found.")
        sys.exit(1)

    builder = trt.Builder(logger) #type: ignore
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) #type: ignore
    parser = trt.OnnxParser(network, logger) #type: ignore

    with open(onnx_path, 'rb') as f:
        onnx_bytes = f.read()

    print("[Build] Parsing ONNX...")
    if not parser.parse(onnx_bytes):
        print("[Build] ERROR: ONNX parse failed:")
        for i in range(parser.num_errors):
            print(f"  - {parser.get_error(i)}")
        sys.exit(1)

    config = builder.create_builder_config()
    # config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_gb << 30)  # GB
    # 修正：set_memory_pool_limit takes bytes. 1 << 30 is 1GB.
    # workspace_gb << 30 means workspace_gb * 1024^3
    try:
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, int(workspace_gb * (1 << 30))) #type: ignore
    except AttributeError:
         # For older TRT versions
        config.max_workspace_size = int(workspace_gb * (1 << 30))

    if builder.platform_has_fast_fp16:
        config.set_flag(trt.BuilderFlag.FP16) #type: ignore

    profile = builder.create_optimization_profile()
    input_name = network.get_input(0).name
    
    # Use img_size for opt and max, and something smaller for min?
    # User requested "Min Memory" (16) and "Max Memory" (30).
    # If these refer to shapes, I should use them.
    # But earlier I decided "Max Memory" is workspace.
    # Let's stick to workspace for Max Memory.
    # For Min Memory, maybe the user meant something else.
    # But given the code had `min_shape = (1, 3, 640, 640)`, maybe I should just use 640 or derived from img_size.
    # I will just use 640 for min if not specified.
    
    min_s = 640
    if img_size < 640:
        min_s = img_size

    min_shape = (1, 3, min_s, min_s)  
    opt_shape = (1, 3, img_size, img_size)   
    max_shape = (1, 3, img_size, img_size)  
    
    print(f"[Build] Input: {input_name}")
    print(f"[Build] Profile: min={min_shape}, opt={opt_shape}, max={max_shape}")

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

    runtime = trt.Runtime(logger) #type: ignore
    engine = runtime.deserialize_cuda_engine(serialized)
    if engine is None:
        print("[Build] ERROR: Engine deserialize failed")
        sys.exit(1)

    print(f"[Build] Serializing to {engine_path}...")
    with open(engine_path, 'wb') as f:
        f.write(serialized) 
    print("[Build] Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", required=True, help="Path to ONNX file")
    parser.add_argument("--engine", required=True, help="Path to output Engine file")
    parser.add_argument("--img_size", type=int, default=960, help="Image size")
    parser.add_argument("--max_mem", type=float, default=30, help="Max memory (Workspace) in GB") # User said default 30
    parser.add_argument("--min_mem", type=float, default=16, help="Min memory (unused/placeholder)") # User said default 16
    
    args = parser.parse_args()
    
    # Ensure output dir exists
    out_dir = os.path.dirname(args.engine)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    build(args.onnx, args.engine, args.img_size, args.max_mem, args.min_mem)
