import PCANBasic as pb
import time as tm
import threading
import tkinter
# import psutil


# Button Functions
def log_button_pressed(Button):
    global log_state, log_button

    if (log_state):
        print("Scanning STOP. Click 'End Application' to exit")
        log_button_text.set("Start Scan")
        log_state = False
    else:
        print("Scanning ...")
        log_button_text.set("Pause Scan")
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
    # initialize pack voltage
    packVoltage = 0
    # 
    precharge = 0

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

    # timing for status print
    app_start_time = tm.perf_counter()
    curr_app_time = tm.perf_counter()
    prev_app_time = tm.perf_counter()

    # Send a message to inform that the main code is running
    print("PCAN Signal Received. Main Loop Running...")

    # ------------------------------ Main Loop ------------------------------ #
    while(1):
        if ((curr_app_time - prev_app_time) > 60):
            print("Run Time: " + f'{(curr_app_time-app_start_time)/60:.2f}'
                  + "mins \tMessage Count: " + str(msg_count))

            curr_app_time = tm.perf_counter()
            prev_app_time = tm.perf_counter()
        else:
            curr_app_time = tm.perf_counter()

        if(close_file):
            break

        # We create a TPCANMsg message structure
        # this is always read in order to clear the buffer
        CANMsg = pcan.Read(pcan_handle)

        # Only process the message if scanning is active
        if (log_state):

            # Parse the message elements
            errors = errors + CANMsg[0]
            msg = CANMsg[1]
            time = CANMsg[2]

            current_time = time.micros + 1000 * time.millis + \
                int('0x100000000', 16) * 1000 * time.millis_overflow

            # Use this for file printing
            if ((msg.ID != 0)):
                msg_count = msg_count + 1

                # if (msg.ID == 0x320):
                #     packVoltage = ((msg.DATA[7] << 24) | (msg.DATA[6] << 16) | (
                #         msg.DATA[5] << 8) | (msg.DATA[4]))/1000.0

                # if (msg.ID == 0x324):
                #     voltSum = ((msg.DATA[7] << 24) | (msg.DATA[6] << 16) | (
                #         msg.DATA[5] << 8) | (msg.DATA[4]))/1000.0
                #     print("Sum of Cell Voltage: "
                #           + f'{voltSum:.2f}' + " V" + "\tPack Voltage: "
                #           + f'{packVoltage:.2f}' + " V")

                if (msg.ID == 0x324):
                    volt = ((msg.DATA[3] << 24) | (msg.DATA[2] << 16) | (
                        msg.DATA[1] << 8) | (msg.DATA[0]))/1000.0

                    if (volt > precharge):
                        precharge = volt
                        print("Precharge Voltage: "
                            + f'{volt:.2f}' + " V")

                # if (msg.ID >= 0x030 and msg.ID <= 0x036):
                #     print('Message ' + hex(msg.ID) + ':', end='')
                #
                #     for i in range(0, msg.LEN):
                #         print(hex(msg.DATA[i])[2:] + ' ', end='', flush=True)
                #
                #     print('')

        else:
            tm.sleep(0.5)
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
