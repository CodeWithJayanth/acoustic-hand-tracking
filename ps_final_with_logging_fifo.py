"""
Updated final demo script (FIFO-compatible):
- Waits for GPIO sync
- Reads 16 samples from FIFO (outSample) after pdmDataReady is set
- Tracks sampling rate
- Logs mic data to CSV
"""

import os, mmap, struct, time, csv

# GPIO Setup
GPIO_PIN = 68
GPIO_PATH = f"/sys/class/gpio/gpio{GPIO_PIN}/value"

# AXI Settings (FIFO-based)
AXI_BASE_ADDR = 0x43C00000
AXI_SIZE = 0x1000
REG_READY_OFFSET = 0x00
REG_SAMPLE_OFFSET = 0x08
NUM_MICS = 16

def wait_for_sync_gpio():
    print(f"Waiting for sync pulse on GPIO{GPIO_PIN}...")
    while True:
        with open(GPIO_PATH, 'r') as f:
            val = f.read().strip()
        if val == "1":
            print("Sync pulse received!")
            break
        time.sleep(0.001)

def read_reg(mem, offset):
    mem.seek(offset)
    return struct.unpack("<I", mem.read(4))[0]

def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(fd, AXI_SIZE, mmap.MAP_SHARED,
                    mmap.PROT_READ | mmap.PROT_WRITE, offset=AXI_BASE_ADDR)

    try:
        wait_for_sync_gpio()
        print("Starting mic read loop...")

        count = 0
        t_start = time.time()

        with open("mic_data_log.csv", "w", newline="") as logfile:
            writer = csv.writer(logfile)
            writer.writerow(["frame_index"] + [f"mic{i}" for i in range(NUM_MICS)])

            while True:
                # Wait for pdmDataReady
                while read_reg(mem, REG_READY_OFFSET) & 0x10 == 0:
                    time.sleep(0.0001)

                # Read 16 mic samples from outSample
                mic_data = [read_reg(mem, REG_SAMPLE_OFFSET) for _ in range(NUM_MICS)]
                writer.writerow([count] + mic_data)

                # Optional print
                mic_str = " | ".join([f"Mic{i}: {mic_data[i]}" for i in range(NUM_MICS)])
                print(f"Frame {count} | {mic_str}")

                count += 1
                if count % 96 == 0:
                    elapsed = time.time() - t_start
                    if elapsed > 0:
                        rate = int(96 / elapsed)
                        print(f"Sampling Rate: {rate} samples/sec (expected ~96000)")
                        t_start = time.time()

                time.sleep(0.0005)

    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        mem.close()
        os.close(fd)

if __name__ == "__main__":
    main()
