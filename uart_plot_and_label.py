"""
Windows Thonny Script:
- Reads mic0–mic15 + hand label from UART
- Plots all 16 mics in real time
- Displays hand label in plot title

UART format expected from Ultra96:
mic0,mic1,...,mic15,label
"""

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

COM_PORT = 'COM4'  # Change to match your actual COM port
BAUD_RATE = 115200
NUM_MICS = 16
WINDOW_SIZE = 100

ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
mic_buffers = [deque([0]*WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(NUM_MICS)]

fig, ax = plt.subplots()
lines = [ax.plot(range(WINDOW_SIZE), list(buf))[0] for buf in mic_buffers]
ax.set_ylim(0, 4096)
ax.set_title("Live Mic Data with Hand Position")
ax.set_xlabel("Time")
ax.set_ylabel("Amplitude")

def update(frame):
    try:
        line_in = ser.readline().decode().strip()
        parts = line_in.split(",")
        if len(parts) == NUM_MICS + 1:
            values = list(map(int, parts[:NUM_MICS]))
            label = parts[-1]
            for i in range(NUM_MICS):
                mic_buffers[i].append(values[i])
                lines[i].set_ydata(mic_buffers[i])
            ax.set_title(f"Hand Position: {label}")
    except Exception:
        pass
    return lines

ani = animation.FuncAnimation(fig, update, interval=10)
plt.tight_layout()
plt.show()
