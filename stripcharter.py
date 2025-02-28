    import matplotlib.pyplot as plt
    import pandas as pd
    import time
    import os
    from IPython import display

    refresh = 1 # refresh period in s

    # looks for the newest thermolog in working fir
    #dir_tomonitor = os.getcwd()
    tsv_file = [file for file in sorted(os.listdir) if "thermolog" in file][-1]

    def plot_data(tsv_file):
        try:
            data = pd.read_tsv(tsv_file)
            plt.clf() # Clear previous plot
            plt.plot(data.iloc[:, "watch"], data.iloc[:, "temp_int"], label="int")
            plt.plot(data.iloc[:, "watch"], data.iloc[:, "temp_ext"], label="ext")
            plt.xlabel("Expt time (s)")
            plt.ylabel("Temperature (°C)")
            plt.title(f'Plot from {tsv_file}')
            display.display(plt.gcf())
            display.clear_output(wait=True)
        except Exception as e:
             print(f"An error occurred: {e}")

    while True:
        plot_data(tsv_file)
        time.sleep(refresh) # Adjust the interval as needed