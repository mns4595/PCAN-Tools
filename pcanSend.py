import PCANBasic as pb
import time as tm
import threading
import tkinter
import numpy as np
# import psutil


# Button Functions
def log_button_pressed(Button):
    global log_state, log_button

    if (log_state):
        print("Scanning STOP. Click 'End Application' to exit")
        log_button_text.set("Start Send")
        log_state = False
    else:
        print("Sending ...")
        log_button_text.set("Pause Send")
        log_state = True


def stop_button_pressed(Button):
    global close_file, tk

    print("Ending Application")
    close_file = True
    tk.destroy()


# PCAN Logging Function
def LogFrame():
    global pcan, pcan_handle, log_state, close_file

    start_time = 0

    # Message counter
    msg_count = 0
    # Start the error counter
    errors = 0
    # initialize temperatures
    temperatures = 25
    tflag = True

    wait_counter = 0

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # Send a message to inform that the main code is running
    print("PCAN Signal Received. Main Loop Running...")

    # ------------------------------ Main Loop ------------------------------ #
    while(~close_file):
        if log_state:
            if ((curr_app_time - prev_app_time) > 0.5):

                msg = pb.TPCANMsg()

                offset = 0x1D000000

                # SOC (80%)
                msg.ID = offset + 0x0C2
                msg.MSGTYPE = pb.PCAN_MESSAGE_EXTENDED
                msg.LEN = 4
                msg.DATA[3] = 0x00
                msg.DATA[2] = 0x00
                msg.DATA[1] = 0x1F
                msg.DATA[0] = 0x40

                pcan.Write(pcan_handle, msg)

                # SOH (100%)
                msg.ID = msg.ID + 1
                msg.LEN = 4
                msg.DATA[3] = 0x00
                msg.DATA[2] = 0x00
                msg.DATA[1] = 0x27
                msg.DATA[0] = 0x10

                pcan.Write(pcan_handle, msg)

                # Voltage (704.54V - 4.12V - 4.22V)
                msg.ID = msg.ID + 1
                msg.LEN = 8
                msg.DATA[7] = 0x01
                msg.DATA[6] = 0xA6
                msg.DATA[5] = 0x01
                msg.DATA[4] = 0x9C
                msg.DATA[3] = 0x00
                msg.DATA[2] = 0x01
                msg.DATA[1] = 0x12
                msg.DATA[0] = 0x6E

                pcan.Write(pcan_handle, msg)

                curr_app_time = tm.perf_counter()
                prev_app_time = tm.perf_counter()
            else:
                curr_app_time = tm.perf_counter()

        elif ((curr_app_time - prev_app_time) > 2):
            print("App Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                  + "mins")

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()
    # ------------------------------ --------- ------------------------------ #

###############################################################################
#                                  INIT                                       #
###############################################################################


# ----------------------------- Button Objects ------------------------------ #
tk = tkinter.Tk()

log_state = False
close_file = False
safe_close = False
override = False

log_button_text = tkinter.StringVar()
log_button_text.set("Start Scan")

log_button = tkinter.Button(
    tk,
    textvariable=log_button_text,
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

log_button.bind("<ButtonPress>", log_button_pressed)
stop_button.bind("<ButtonPress>", stop_button_pressed)

log_button.pack(side=tkinter.LEFT)
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

    print("Running PCAN Basic...")
    x.start()

    tk.mainloop()


print(".\n.\n.\nProgram Exit")
exit(0)
