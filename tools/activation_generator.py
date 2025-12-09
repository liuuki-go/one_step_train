import sys
import os
import datetime
import csv

# Ensure we can import core
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from core.activation import generate_activation_payload
except ImportError:
    print("Error: Could not import core.activation. Please run this script from the project root or ensure core is in python path.")
    sys.exit(1)

def main():
    print("=== Activation Code Generator ===")
    
    while True:
        print("\n--- New Activation Code ---")
        machine_code = input("Enter Customer Machine Code: ").strip()
        if not machine_code:
            print("Machine code is required.")
            continue
            
        print("Select Validity Period:")
        print("1. 1 Month")
        print("2. 6 Months")
        print("3. 12 Months")
        print("4. 24 Months")
        print("5. Custom (Seconds)")
        
        choice = input("Enter choice (1-5): ").strip()
        
        duration = 0
        duration_label = ""
        
        # Approximation: 1 month = 30 days
        month_seconds = 30 * 24 * 3600
        
        if choice == '1':
            duration = month_seconds
            duration_label = "1 Month"
        elif choice == '2':
            duration = 6 * month_seconds
            duration_label = "6 Months"
        elif choice == '3':
            duration = 12 * month_seconds
            duration_label = "12 Months"
        elif choice == '4':
            duration = 24 * month_seconds
            duration_label = "24 Months"
        elif choice == '5':
            try:
                duration = int(input("Enter duration in seconds: "))
                duration_label = f"{duration} Seconds"
            except ValueError:
                print("Invalid number.")
                continue
        else:
            print("Invalid choice.")
            continue
            
        code = generate_activation_payload(machine_code, duration)
        
        print("\n" + "="*40)
        print(f"Machine Code: {machine_code}")
        print(f"Duration:     {duration_label} ({duration}s)")
        print(f"Activation Code:\n{code}")
        print("="*40 + "\n")
        
        # Log to CSV (台账)
        log_file = os.path.join(current_dir, "activation_log.csv")
        file_exists = os.path.exists(log_file)
        
        try:
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Machine Code", "Duration Label", "Duration Seconds", "Expiration Date (Approx)", "Activation Code"])
                
                now = datetime.datetime.now()
                expire_approx = now + datetime.timedelta(seconds=duration)
                
                writer.writerow([
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    machine_code,
                    duration_label,
                    duration,
                    expire_approx.strftime("%Y-%m-%d %H:%M:%S"),
                    code
                ])
            print(f"Record saved to {log_file}")
        except Exception as e:
            print(f"Failed to save log: {e}")
            
        cont = input("Generate another? (y/n): ").lower()
        if cont != 'y':
            break

if __name__ == "__main__":
    main()
