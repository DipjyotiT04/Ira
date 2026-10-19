#!/usr/bin/env python3
import json
import struct
import hashlib
import sys

GGUF_PATH = "/home/dinu/.ollama/models/blobs/sha256-59bb50d8116b6a1f9bfbb940d6bb946a05554e591e30c8c2429ed6c854867ecb"

def read_gguf_metadata(path):
    with open(path, "rb") as f:
        # Read magic
        magic = f.read(4)
        if magic != b"GGUF":
            raise ValueError("Not a GGUF file")
        
        # Read version
        version = struct.unpack("<I", f.read(4))[0]
        
        # Read tensor count and metadata count
        tensor_count = struct.unpack("<Q", f.read(8))[0]
        metadata_kv_count = struct.unpack("<Q", f.read(8))[0]
        
        metadata = {}
        for _ in range(metadata_kv_count):
            # Read key
            key_len = struct.unpack("<Q", f.read(8))[0]
            key = f.read(key_len).decode("utf-8")
            
            # Read value type
            value_type = struct.unpack("<I", f.read(4))[0]
            
            # Read value based on type
            if value_type == 0:  # uint8
                value = struct.unpack("<B", f.read(1))[0]
            elif value_type == 1:  # int8
                value = struct.unpack("<b", f.read(1))[0]
            elif value_type == 2:  # uint16
                value = struct.unpack("<H", f.read(2))[0]
            elif value_type == 3:  # int16
                value = struct.unpack("<h", f.read(2))[0]
            elif value_type == 4:  # uint32
                value = struct.unpack("<I", f.read(4))[0]
            elif value_type == 5:  # int32
                value = struct.unpack("<i", f.read(4))[0]
            elif value_type == 6:  # float32
                value = struct.unpack("<f", f.read(4))[0]
            elif value_type == 7:  # bool
                value = struct.unpack("<?", f.read(1))[0]
            elif value_type == 8:  # string
                str_len = struct.unpack("<Q", f.read(8))[0]
                value = f.read(str_len).decode("utf-8")
            elif value_type == 9:  # array
                array_type = struct.unpack("<I", f.read(4))[0]
                array_len = struct.unpack("<Q", f.read(8))[0]
                if array_type == 8:  # string array
                    value = []
                    for _ in range(array_len):
                        str_len = struct.unpack("<Q", f.read(8))[0]
                        value.append(f.read(str_len).decode("utf-8"))
                elif array_type == 4:  # uint32 array
                    value = struct.unpack(f"<{array_len}I", f.read(4 * array_len))
                elif array_type == 5:  # int32 array
                    value = struct.unpack(f"<{array_len}i", f.read(4 * array_len))
                elif array_type == 6:  # float32 array
                    value = struct.unpack(f"<{array_len}f", f.read(4 * array_len))
                else:
                    value = f"[array type {array_type}, len {array_len}]"
                    f.seek(f.tell())  # skip
            elif value_type == 10:  # uint64
                value = struct.unpack("<Q", f.read(8))[0]
            elif value_type == 11:  # int64
                value = struct.unpack("<q", f.read(8))[0]
            elif value_type == 12:  # float64
                value = struct.unpack("<d", f.read(8))[0]
            else:
                value = f"[unknown type {value_type}]"
            
            metadata[key] = value
        
        return metadata

def get_checksum(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_size(path):
    import os
    return os.path.getsize(path)

if __name__ == "__main__":
    metadata = read_gguf_metadata(GGUF_PATH)
    checksum = get_checksum(GGUF_PATH)
    size = get_size(GGUF_PATH)
    
    with open("/home/dinu/Desktop/Tech/ira/eval/audit/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    with open("/home/dinu/Desktop/Tech/ira/eval/audit/checksums.txt", "w") as f:
        f.write(f"SHA256: {checksum}\n")
        f.write(f"Size: {size} bytes ({size / (1024**3):.2f} GB)\n")
    
    print("Metadata keys:", list(metadata.keys()))
    print("Checksum:", checksum)
    print("Size:", size)