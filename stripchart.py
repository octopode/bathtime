#!/usr/bin/python3
## This script looks for the newest "thermolog" file in the working directory
## and provides a real-time stripchart.

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import time
import os

# looks for the newest thermolog in working dir
tsv_file = [file for file in sorted(os.listdir()) if "thermolog" in file][-1]

fig, ax = plt.subplots()
line1, = ax.plot([], [], color = "blue")  # Create an empty line object
line2, = ax.plot([], [], color = "purple")  # Create an empty line object
ax.set_xlim(0, 100)      # Set initial x-axis limits
ax.set_ylim(-1, 1)      # Set initial y-axis limits
ax.set_xlabel("Expt time (s)")
ax.set_ylabel("Temperature (°C)")

def animate(i):
    # Get new data (replace with your data source)
    data = pd.read_csv(tsv_file, sep='\t')
    x_data = data.loc[:, "watch"]
    y1_data = data.loc[:, "temp_ext"]
    y2_data = data.loc[:, "temp_int"]

    # Update the line object's data
    line1.set_data(x_data, y1_data)
    line2.set_data(x_data, y2_data)

    # Adjust x-axis limits to follow the data
    ax.set_xlim(0, max(x_data, default=100))
    alldata = pd.concat([y1_data, y2_data])
    ax.set_ylim(min(alldata, default=100), max(alldata, default=100))
    return line1, line2

ani = animation.FuncAnimation(fig, animate, interval=1000, blit=True)
plt.show()