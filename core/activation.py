import uuid
import hashlib
import json
import base64
import time
import os
import random
import string
from datetime import datetime, timedelta

# --- Configuration ---
# In a real scenario, obfuscate this or load from a secure place.
# For this task, we define it here.
INTERNAL_SALT = "OST_2025_SECURE_SALT_!@#" 
ACTIVATION_FILE_NAME = "license"
HISTORY_FILE_NAME = "activation.history"

def _get_xor_key():
    """Derive a key from the internal salt for XOR obfuscation."""
    return hashlib.sha256(INTERNAL_SALT.encode('utf-8')).digest()

def _obfuscate(data_str):
    """Simple XOR obfuscation + Base64 encoding to hide plaintext."""
    key = _get_xor_key()
    data_bytes = data_str.encode('utf-8')
    obfuscated = bytearray()
    for i, b in enumerate(data_bytes):
        obfuscated.append(b ^ key[i % len(key)])
    return base64.b64encode(obfuscated).decode('utf-8')

def _deobfuscate(data_b64):
    """Reverse the obfuscation."""
    try:
        data_bytes = base64.b64decode(data_b64)
        key = _get_xor_key()
        original = bytearray()
        for i, b in enumerate(data_bytes):
            original.append(b ^ key[i % len(key)])
        return original.decode('utf-8')
    except Exception:
        return None

def _load_history():
    """Loads the list of used activation signatures."""
    if not os.path.exists(HISTORY_FILE_NAME):
        return []
    try:
        with open(HISTORY_FILE_NAME, 'r') as f:
            content = f.read().strip()
        if not content:
            return []
            
        json_str = _deobfuscate(content)
        if not json_str:
            return []
            
        return json.loads(json_str)
    except Exception:
        return []

def _save_history(used_signatures):
    """Saves the list of used activation signatures."""
    try:
        json_str = json.dumps(used_signatures)
        encrypted = _obfuscate(json_str)
        with open(HISTORY_FILE_NAME, 'w') as f:
            f.write(encrypted)
    except Exception as e:
        print(f"Failed to save history: {e}")

def get_machine_code():
    """
    Generates a unique machine code based on MAC address.
    Returns a 16-character uppercase string.
    """
    try:
        mac = uuid.getnode()
        # Mix with salt to prevent direct guessing of MAC
        raw_str = f"{mac}-{INTERNAL_SALT}"
        hasher = hashlib.sha256()
        hasher.update(raw_str.encode('utf-8'))
        # Take first 16 chars
        return hasher.hexdigest()[:16].upper()
    except Exception:
        return "UNKNOWN-DEVICE"

def generate_activation_payload(machine_code, duration_seconds, custom_salt=INTERNAL_SALT):
    """
    Generates the activation code string to be given to the user.
    Format: Base64(duration_seconds|random_str|signature)
    Signature = SHA256(duration_seconds + random_str + machine_code + custom_salt)
    """
    # Generate random string
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Create signature
    # 拼接「有效期秒数 + 随机串 + 客户机器码 + 盐值」
    raw_data = f"{duration_seconds}{random_str}{machine_code}{custom_salt}"
    signature = hashlib.sha256(raw_data.encode('utf-8')).hexdigest().upper()
    
    # Create payload
    payload = f"{duration_seconds}|{random_str}|{signature}"
    encoded_payload = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
    
    return encoded_payload

def verify_activation_code(input_code, current_machine_code):
    """
    Verifies the activation code entered by the user.
    Returns (is_valid, duration_seconds, message)
    """
    try:
        # Decode
        decoded = base64.b64decode(input_code).decode('utf-8')
        parts = decoded.split('|')
        if len(parts) != 3:
            return False, 0, "激活码格式错误"
        
        duration_seconds = parts[0]
        random_str = parts[1]
        signature = parts[2]
        
        # Re-calculate signature
        raw_data = f"{duration_seconds}{random_str}{current_machine_code}{INTERNAL_SALT}"
        expected_signature = hashlib.sha256(raw_data.encode('utf-8')).hexdigest().upper()
        
        if signature == expected_signature:
            # Check if already used
            used_signatures = _load_history()
            if signature in used_signatures:
                return False, 0, "激活码已过期或已使用！"
                
            return True, int(duration_seconds), "激活成功"
        else:
            return False, 0, "签名验证失败"
            
    except Exception as e:
        print(f"Activation parsing error: {e}")
        return False, 0, "解析激活码错误"

def save_activation_status(duration_seconds, input_code=None):
    """
    Saves the activation status to a local file.
    If input_code is provided, extracts signature and marks it as used.
    """
    try:
        timestamp = int(time.time())
        machine_code = get_machine_code()
        
        # Create integrity signature for the file itself
        check_str = f"{timestamp}{duration_seconds}{machine_code}{INTERNAL_SALT}"
        file_signature = hashlib.sha256(check_str.encode('utf-8')).hexdigest()
        
        data = {
            "activated_at": timestamp,
            "duration": duration_seconds,
            "file_signature": file_signature
        }
        
        # Convert to JSON string
        json_str = json.dumps(data)
        
        # Obfuscate
        encrypted_content = _obfuscate(json_str)
        
        with open(ACTIVATION_FILE_NAME, 'w') as f:
            f.write(encrypted_content)
        
        # Mark as used in history
        if input_code:
            try:
                decoded = base64.b64decode(input_code).decode('utf-8')
                parts = decoded.split('|')
                if len(parts) == 3:
                    signature = parts[2]
                    used_signatures = _load_history()
                    if signature not in used_signatures:
                        used_signatures.append(signature)
                        _save_history(used_signatures)
            except Exception as e:
                print(f"Failed to update history: {e}")
        
        return True
    except Exception as e:
        print(f"Failed to save activation: {e}")
        return False

def check_activation_status():
    """
    Checks if the app is currently activated and valid.
    Returns:
    - valid (bool): True if valid, False otherwise
    - message (str): Status message (e.g., "Expired", "Not Activated", "Valid")
    - details (dict): Extra info like remaining time
    """
    if not os.path.exists(ACTIVATION_FILE_NAME):
        return False, "Not Activated", {}
    
    try:
        with open(ACTIVATION_FILE_NAME, 'r') as f:
            content = f.read().strip()
            
        # Try to deobfuscate
        json_str = _deobfuscate(content)
        
        if not json_str:
            # Fallback: Maybe it's the old plaintext JSON format?
            # We can try to parse content directly to be nice, or just reject it.
            # Given the requirement for security, let's try to parse as JSON first just in case
            # we want backward compatibility, BUT the user specifically wants to prevent tampering.
            # If we allow plaintext, they can still tamper.
            # So we should REJECT plaintext.
            return False, "Invalid License Format", {}
            
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return False, "Corrupted License Data", {}
            
        timestamp = data.get("activated_at")
        duration = data.get("duration")
        stored_signature = data.get("file_signature")
        
        if not timestamp or not duration or not stored_signature:
            return False, "Corrupted Activation File", {}
        
        # Verify integrity
        machine_code = get_machine_code()
        check_str = f"{timestamp}{duration}{machine_code}{INTERNAL_SALT}"
        expected_signature = hashlib.sha256(check_str.encode('utf-8')).hexdigest()
        
        if stored_signature != expected_signature:
            return False, "Activation File Tampered", {}
        
        # Check expiration
        current_time = int(time.time())
        elapsed = current_time - timestamp
        
        # duration -1 could mean forever if we wanted, but requirement says specific months.
        # Assuming duration is always > 0.
        
        if elapsed > duration:
            return False, "Expired", {"expired_at": datetime.fromtimestamp(timestamp + duration)}
        
        remaining = duration - elapsed
        return True, "Valid", {"remaining_seconds": remaining}
        
    except Exception as e:
        return False, f"Error checking activation: {e}", {}
