import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import asyncio
import websockets
import json
import pygame
import serial.tools.list_ports as ports
import serial
import time
import threading
import queue
import sys

# Function to find the Pico Serial port dynamically
def find_pico_port():
    pico_ports = [port for port in ports.comports() if 'ACM' in port.device or 'USB' in port.device]
    if pico_ports:
            return pico_ports[0].device # Return the first found port
    return None

# --- Configuration ---
#Set up serial communication with the Pico (adjust port and baud rate)
SERIAL_PORT = find_pico_port()
BAUD_RATE = 9600
try:
    # Use queue for thread-safe serial communication
    ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=0.1,
    write_timeout=0.1
    )
    print(f"Serial port {SERIAL_PORT} opened successfully.")
except serial.SerialException as e:
    print(f"Serial port error: {e}")
    sys.exit(1)
    
    
# Global variable to manage control priority
# 'remote' is the default mode
# 'local' takes over if the Bluetooth controller is connected and active
control_mode = 'remote'
last_local_input_time = time.time()
LOCAL_TIMEOUT_SECONDS = 5 # Timeout for local control inactivity

# A dictionary to hold the current desired robot state (e.g., motor speed, light status)
#This gets populated by either the websocket or the local controller
robot_state = {
    'left_motor_speed': 0,
    'right_motor_speed': 0,
    'light_on': False,
}

# Queue for sending commands from the threads to the main serial port handler
serial_queue = queue.Queue()


# --- Serial Sender Thread Function ---
def serial_sender():
    """Reads commands from the queue and sends them to the Pico."""
    while True:
        try:
            command = serial_queue.get(timeout=0.1) # Wait briefly for a command 
            
            if ser and ser.is_open:
                ser.write(command.encode('utf-8'))
                serial_queue.task_done()
                #print(f"[SERIAL TX] Sent Command: {command.strip()}")
        except queue.Empty:
            continue
        except serial.SerialException as e:
            print(f"Serial port exception during send: {e}")
            time.sleep(0.1)    
        except Exception as e:
            print(f"Error sending serial data: {e}")
            time.sleep(0.1)
        
# Start the serial sender thread
serial_thread = threading.Thread(target=serial_sender, daemon=True)
serial_thread.start()
#ser.write(b'\x04')

left_motor_val = 0
right_motor_val = 0
MAX_SPEED = 100

# --- Local Controller (Pygame) Thread Function ---
def check_local_controller():
    global control_mode, last_local_input_time, left_motor_val, right_motor_val
    
    pygame.init()
    pygame.joystick.init()
    joystick = None
    
    while True:
        if pygame.joystick.get_count() > 0:
            if joystick is None:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
                print("Local controller connected. Switching to LOCAL control.")
                control_mode = 'local'
            
           # Process events
            for event in pygame.event.get():
                if event.type in [pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION]:
                    last_local_input_time = time.time()
                    
                    if control_mode == 'local':
                        
                        # Get current joystick values (values are typically from -1.0 to 1.0)
                        forward_speed = -joystick.get_axis(1) # Left stick Y axis (Negate for forward=positive)
                        steer_speed = joystick.get_axis(3)   # Right stick X axis (Common axis, check your controller mapping if different)
                        
                        # --- Skid Steering Mixing Algorithm ---
                        # Scale values from -1.0 to 1.0 to -MAX_SPEED to MAX_SPEED
                        forward_val = int(forward_speed * MAX_SPEED)
                        steer_val = int(steer_speed * MAX_SPEED)

                        # Calculate individual motor speeds
                        left_val = forward_val + steer_val
                        right_val = forward_val - steer_val
                        
                        # Clamp values to the valid range [-MAX_SPEED, MAX_SPEED]
                        left_motor_val = max(-MAX_SPEED, min(MAX_SPEED, left_val))
                        right_motor_val = max(-MAX_SPEED, min(MAX_SPEED, right_val))
                        
                        # Format the command for the Pico and add to the serial queue
                        # Example command format: "L50R-20\n" (Assuming your Pico understands this)
                        #ser.write(f"L{left_motor_val}R{right_motor_val}".encode())
                        #command = f"L{left_motor_val}R{right_motor_val}\n"
                        #serial_queue.put(command)
                        serial_queue.put(f"L{left_motor_val}R{right_motor_val}\n")
                        #print(f"Command: {command.strip()} | Left: {forward_speed:.2f}, Right: {steer_speed:.2f}")
                        #print(f"[DEBUG JOY] Mode: {control_mode} | Axis 1: {forward_speed:.2f} | Axis 3: {steer_speed:.2f}")
                        
                        # Handle button presses for lights (optional)
                        if event.type == pygame.JOYBUTTONDOWN:
                            if event.button == 0: # Button A
                                serial_queue.put('LIGHT_ON\n')
                        if event.type == pygame.JOYBUTTONUP:
                            if event.button == 0:
                                serial_queue.put('LIGHT_OFF\n')
                        
                        #if abs(left_motor_val) > 5 or abs(right_motor_val) > 5:
                            #print(f"TX Command: {command.strip()} | Left Joy Y: {forward_speed:.2f}, Right Joy X: {steer_speed:.2f}")
            # Timeout mechanism: revert to remote if local controller is idle
            if time.time() - last_local_input_time > LOCAL_TIMEOUT_SECONDS:
                if control_mode == 'local':
                    print(f"Local controller inactive for {LOCAL_TIMEOUT_SECONDS}s. Reverting to REMOTE control and stopping motors.")
                    control_mode = 'remote'
                    # Send stop command when switching modes due to inactivity
                    serial_queue.put(f"L0R0\n")
        else:
            # If controller disconnects entirely
            if joystick is not None:
                print("Local controller disconnected. Reverting to REMOTE control and stopping motors.")
                joystick = None
                control_mode = 'remote'
                serial_queue.put(f"L0R0\n")
        
        time.sleep(0.01)
        
# Start the local controller thread
controller_thread = threading.Thread(target=check_local_controller, daemon=True)
controller_thread.start()


# --- WebSocket Server Functions (Your existing code + arbitration) ---

async def message_process(websocket):
    global control_mode
    
    print("Client connected! Waiting for data stream...")
    
    try:
        async for message in websocket:

            # Parse the structured JSON message

            data = json.loads(message)

            

            # Now access every field by name as defined in your table:

            if data.get('connection_status', False):

                print("-" * 30) # Separator for each update

                print(f"Connection Status: {data['connection_status']}")

                print(f"Left Stick X: {data.get('left_stick_x')} | Left Stick Y: {data.get('left_stick_y')}")

                print(f"Right Stick X: {data.get('right_stick_x')} | Right Stick Y: {data.get('right_stick_y')}")

                print(f"Trigger Left: {data.get('trigger_left')} | Trigger Right: {data.get('trigger_right')}")

                print(f"Button A: {data.get('button_a')} | Button B: {data.get('button_b')} | Button X: {data.get('button_x')} | Button Y: {data.get('button_y')}")

                print(f"Bumper Left: {data.get('button_left_bumper')} | Bumper Right: {data.get('button_right_bumper')}")

                print(f"Button Left (View): {data.get('button_left')} | Button Right (Menu): {data.get('button_right')} | Button Center: {data.get('button_center')}")

                print(f"Left Stick Button: {data.get('left_stick_button')} | Right Stick Button: {data.get('right_stick_button')}")
                
                print(f"D-Pad: Top:{data.get('dpad_top')} | Bottom:{data.get('dpad_bottom')} | Left:{data.get('dpad_left')} | Right:{data.get('dpad_right')}")

                print("-" * 30)

                

                # --- Control Logic Integration Point ---

                # Example: Turn on LED when button A is pressed

                # if data.get('button_a'):

                #     led.on()

                # else:

                #     led.off()

                # -------------------------------------


            else:

                print("Controller disconnected (status false)")


    except websockets.exceptions.ConnectionClosed:

        print("Client disconnected.")

    except Exception as e:

        # Catch JSON decoding errors or key errors gracefully

        print(f"An error occurred while processing data: {e}")
        
        
async def main():
    # Use the single-argument handler required by your installed library version
    async with websockets.serve(message_process, "0.0.0.0", 5000):
        print("WebSocket server started at ws://0.0.0.0:5000")
        print(f"Current Control Mode: {control_mode}") 
        await asyncio.Future() # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program shutting down.")
    finally:
        ser.close()
        pygame.quit()
