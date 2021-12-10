import PCANBasic as pb
import time as tm
import threading
import tkinter
import psutil
# import numpy as np
import matplotlib.pyplot as plt


# Dynamic plot function
class DynamicUpdate():
    def on_launch(self):
        # Set up plot
        self.figure, self.ax = plt.subplots()
        self.packVolt, = self.ax.plot([], [], 'o', label="Pack Voltage [V]")
        self.SOC, = self.ax.plot([], [], '+', label="SOC [%]")
        self.minCellVolt, = self.ax.plot(
            [], [], '*', label="Min Cell Voltage [V]")
        # Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        # self.ax.set_xlim(self.min_x, self.max_x)
        self.ax.set_autoscalex_on(True)
        # Other stuff
        self.ax.grid()
        self.ax.legend()
        self.ax.set_xlabel('Time [s]')
        ...

    def on_running(self, timePackVolt, packVoltage, timeSOC, SOC,
                   timeMinCellVoltage, minCellVoltage):
        # Update data (with the new _and_ the old points)
        self.packVolt.set_xdata(timePackVolt)
        self.packVolt.set_ydata(packVoltage)

        self.SOC.set_xdata(timeSOC)
        self.SOC.set_ydata(SOC)

        self.minCellVolt.set_xdata(timeMinCellVoltage)
        self.minCellVolt.set_ydata(minCellVoltage)
        # Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        # We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()


# Button Functions
def plot_button_pressed(Button):
    global plot_state, plot_button

    if (plot_state):
        print("Ploting STOP. Click 'End Application' to close plot")
        plot_button_text.set("Start Plot")
        plot_state = False
    else:
        print("Ploting ...")
        plot_button_text.set("Pause Plot")
        plot_state = True


def stop_button_pressed(Button):
    global close_file, tk

    print("Ending Application")
    close_file = True
    tk.destroy()


# PCAN Logging Function
def LogFrame():
    global pcan, pcan_handle, plot_state, close_file

    start_time = 0

    # Message counter
    msg_count = 0
    # Start the error counter
    errors = 0
    # Store the current ram available
    ram_left = psutil.virtual_memory()[1]

    wait_counter = 0
    # Wait for the module to start (i.e.: The clock is running)
    while start_time == 0:
        if (wait_counter % 300000 == 0):
            wait_counter = 0
            print("Waiting for PCAN Signal...")

        dumdum = pcan.Read(pcan_handle)
        start_time = dumdum[2].micros + 1000 * dumdum[2].millis + \
            int('0x100000000', 16) * 1000 * dumdum[2].millis_overflow

        wait_counter = wait_counter + 1

        if (close_file):
            break

    # Initialize plot object
    plt.ion()
    dynFig = DynamicUpdate()
    dynFig.on_launch()
    timePackVolt = []
    packVoltage = []
    timeSOC = []
    SOC = []
    timeMinCellVoltage = []
    minCellVoltage = []

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # ------------------------------ Main Loop ------------------------------ #
    while(1):

        if ((curr_app_time - prev_app_time) > 5):
            ram_left = psutil.virtual_memory()[1]

            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                  + "mins \tMessage Count: " + str(msg_count)
                  + " \tRAM: " + str(ram_left/1000000) + "MB left")

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()

        if(close_file):
            break

        if (plot_state):

            # We create a TPCANMsg message structure
            #
            CANMsg = pcan.Read(pcan_handle)

            # Parse the message elements
            errors = errors + CANMsg[0]
            msg = CANMsg[1]
            time = CANMsg[2]

            current_time = time.micros + 1000 * time.millis + \
                int('0x100000000', 16) * 1000 * time.millis_overflow

            # Convert time to seconds
            current_time = current_time / 1000

            # Count all received messages
            if ((msg.ID != 0)):
                msg_count = msg_count + 1

            # Process only the pack voltage, SOC, and low cell voltage data
            if (msg.ID == 0x320):
                voltage = ((msg.DATA[7] << 24) | (msg.DATA[6] << 16) | (
                    msg.DATA[5] << 8) | (msg.DATA[4])) / 1000
                timePackVolt.append(curr_app_time)
                packVoltage.append(voltage)
            elif (msg.ID == 0x321):
                charge = ((msg.DATA[7] << 8) | (msg.DATA[6])) / 10
                timeSOC.append(curr_app_time)
                SOC.append(charge)
            elif (msg.ID == 0x322):
                voltage = ((msg.DATA[7] << 8) | (msg.DATA[6])) / 1000
                timeMinCellVoltage.append(curr_app_time)
                minCellVoltage.append(voltage)

            dynFig.on_running(timePackVolt, packVoltage, timeSOC, SOC,
                              timeMinCellVoltage, minCellVoltage)

        else:
            tm.sleep(0.5)
    # ------------------------------ --------- ------------------------------ #

###############################################################################
#                                  INIT                                       #
###############################################################################


# ----------------------------- Button Objects ------------------------------ #
tk = tkinter.Tk()

plot_state = False
close_file = False
safe_close = False
override = False

plot_button_text = tkinter.StringVar()
plot_button_text.set("Start Plot")

plot_button = tkinter.Button(
    tk,
    textvariable=plot_button_text,
    width=25,
    height=5,
    bg="blue",
    fg="yellow"
)
stop_button = tkinter.Button(
    tk,
    text="End Application",
    width=25,
    height=5,
    bg="blue",
    fg="yellow"
)

plot_button.bind("<ButtonPress>", plot_button_pressed)
stop_button.bind("<ButtonPress>", stop_button_pressed)

plot_button.pack(side=tkinter.LEFT)
stop_button.pack(side=tkinter.RIGHT)

# ------------------------------ PCAN Objects ------------------------------ #

# Initialize pcan object
pcan = pb.PCANBasic()
# Get PCAN Channel
pcan_handle = pb.PCAN_USBBUS1

# Setup Connection's Baud Rate
baudrate = pb.PCAN_BAUD_500K

result = pcan.Initialize(pcan_handle, baudrate)

if result != pb.PCAN_ERROR_OK:
    if result != pb.PCAN_ERROR_CAUTION:
        print("PCAN Error!")
    else:
        print('******************************************************')
        print('The bitrate being used is different than the given one')
        print('******************************************************')
        result = pb.PCAN_ERROR_OK
else:
    x = threading.Thread(target=LogFrame)
    x.start()

    print("Running PCAN Basic...")

    tk.mainloop()


print(".\n.\n.\nProgram Exit")
exit(0)
