"""
Ultra96 UART Sender (FIFO-Compatible, Hand Tracking)
- Waits for pdmDataReady
- Reads 16 mic samples from FIFO (outSample @ 0x08)
- Classifies hand as Left, Center, Right based on energy
- Sends all 16 mic values + label via UART
"""

import os, mmap, struct, time, serial

AXI_BASE_ADDR = 0x43C00000
AXI_SIZE = 0x1000
REG_READY_OFFSET = 0x00
REG_SAMPLE_OFFSET = 0x08
NUM_MICS = 16

fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
mem = mmap.mmap(fd, AXI_SIZE, mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE, offset=AXI_BASE_ADDR)

ser = serial.Serial('/dev/ttyPS0', 115200)

def read_reg(offset):
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

try:
    print("FIFO-based UART Hand Tracking Sender running...")
    while True:
        # Wait for data ready (bit 4 of 0x00)
        while read_reg(REG_READY_OFFSET) & 0x10 == 0:
            time.sleep(0.0001)

        mic_data = [read_reg(REG_SAMPLE_OFFSET) for _ in range(NUM_MICS)]
        label = classify_hand_position(mic_data)
        line = ",".join(map(str, mic_data)) + "," + label + "\n"
        ser.write(line.encode())
        time.sleep(0.001)

except KeyboardInterrupt:
    print("Exiting.")
finally:
    mem.close()
    os.close(fd)
