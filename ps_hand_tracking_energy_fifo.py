"""
FIFO-Compatible Hand Tracking (No ML)
- Reads 16 mic samples from FIFO (outSample at 0x08) when pdmDataReady is high
- Classifies hand position based on regional mic energy
"""

import os, mmap, struct, time

# AXI Settings (FIFO-based)
AXI_BASE_ADDR = 0x43C00000
AXI_SIZE = 0x1000
REG_READY_OFFSET = 0x00
REG_SAMPLE_OFFSET = 0x08
NUM_MICS = 16

def read_reg(mem, offset):
    mem.seek(offset)
    return struct.unpack("<I", mem.read(4))[0]

def classify_hand_position(mic_values):
    left_energy = sum(mic_values[0:5])
    center_energy = sum(mic_values[5:11])
    right_energy = sum(mic_values[11:16])

    max_energy = max(left_energy, center_energy, right_energy)

    if max_energy == left_energy:
        return "Left"
    elif max_energy == center_energy:
        return "Center"
    else:
        return "Right"

def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(fd, AXI_SIZE, mmap.MAP_SHARED,
                    mmap.PROT_READ | mmap.PROT_WRITE, offset=AXI_BASE_ADDR)

    try:
        print("Running FIFO-based hand tracking... (Ctrl+C to stop)")
        while True:
            # Wait for pdmDataReady (bit 4 of register 0x00)
            while read_reg(mem, REG_READY_OFFSET) & 0x10 == 0:
                time.sleep(0.0001)

            # Read 16 mic samples from FIFO
            mic_data = [read_reg(mem, REG_SAMPLE_OFFSET) for _ in range(NUM_MICS)]
            position = classify_hand_position(mic_data)

            # Print result
            print(f"Hand: {position} | Mic0: {mic_data[0]} | Mic7: {mic_data[7]} | Mic15: {mic_data[15]}")
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        mem.close()
        os.close(fd)

if __name__ == "__main__":
    main()
