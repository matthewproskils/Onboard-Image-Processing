"""Made by BRONCO SPACE of CAL POLY POMONA
Edited by ARUSH KHARE, MATTHEW CHAN, and MASON of IRVINGTON CUBESAT"""

# Initialize Libraries
import board
import busio
import time
import adafruit_ov5640
import gc
import os

# Initialize Camera and Garbage Collector
gc.enable()
print("memory before allocation: {}".format(gc.mem_free()))
FACTOR = 1
height=480
width=640
quality=20
buf=bytearray(height*width//quality)
print("memory after allocation: {}".format(gc.mem_free()))

i2c1=busio.I2C(board.GP9,board.GP8)
cam = adafruit_ov5640.OV5640(
    i2c1,
    data_pins=(
        board.GP12,
        board.GP13,
        board.GP14,
        board.GP15,
        board.GP16,
        board.GP17,
        board.GP18,
        board.GP19,
    ),
    clock=board.GP11,
    vsync=board.GP7,
    href=board.GP21,
    mclk=board.GP20,
    shutdown=None,
    reset=None,
    size=adafruit_ov5640.OV5640_SIZE_VGA
)

camset_meta = {
    "effect": 0,
    "exposure_value": -3,
    "white_balance": 0,
}

# Camera Settings
cam.colorspace = adafruit_ov5640.OV5640_COLOR_JPEG
cam.flip_y = False
cam.flip_x = True
cam.test_pattern = False
for k in ["effect", "exposure_value", "white_balance"]:
    setattr(cam, k, camset_meta[k])
cam.night_mode=False
cam.quality=quality
print("memory before collection: {}".format(gc.mem_free()))
gc.collect()
print("memory after collection: {}".format(gc.mem_free()))
print("memory before picture: {}".format(gc.mem_free()))

import sys
import os
import binascii
import supervisor
import microcontroller as mc

serial_data_buffer = "" # from pc
serial_echo = False
serial_commands = {}

def serial_command(name):
    def wrapped(callback):
        serial_commands[name] = callback

        return callback
    
    return wrapped

def capture(name, folder="test-images"):
    # print("ok: zeroing buffer")
    for i in range(len(buf)):
        buf[i] = 0
    print("ok: capturing test photo")
    try:
        cam.capture(buf)
    except Exception as e:
        print("error:", e)
        return
    print(f"ok: saving test photo to images/{folder}/{name}.jpeg | byte count:", len(buf))
    
    eoi = buf.find(b"\xff\xd9") # this can false positive, parse the jpeg for better results
    # print("ok: eoi marker (possibly inaccurate):", eoi)

    if eoi == -1:
        print("warn: IMAGE IS PROBABLY TRUNCATED")

    try:
        os.mkdir("images")
    except:
        print("Image Folder Exists")

    try:
        os.mkdir(f"images/{folder}")
    except:
        print(f"Folder {folder} Exists")

    #print(buf)
    photo_file = open(f"images/{folder}/{name}.jpeg", 'wb')
    photo_file.write(buf)
    photo_file.close()
    print("ok: done saving")

def sortThroughDir(dir):
    # Maps through dir to return sorted list of touples of name and file size
    return sorted(
        list(
            map(
                lambda f: (
                    f,
                    os.stat(os.getcwd() +"/" + dir + "/" + f)[6],
                ),
                os.listdir(dir),
            )
        ),
        key=lambda x: x[1]
    )[::-1]

@serial_command("ping")
def _(_):
    print("pong")

@serial_command("echo")
def _(_):
    global serial_echo
    serial_echo = not serial_echo

@serial_command("esafemode")
def _(_):
    print("ok: entering safe mode and restarting")
    mc.on_next_reset(mc.RunMode.SAFE_MODE)
    mc.reset()

#Exit Safe Mode
"""
import microcontroller as mc
mc.on_next_reset(mc.RunMode.NORMAL)
mc.reset()
"""
@serial_command("exit")
def _(_):
    print("ok: exiting serial handler")
    sys.exit()

@serial_command("getfile")
def _(args):
    if len(args) < 1:
        print("error: getfile requires 1 arg")
        return
    
    try:
        with open(args[0], "rb") as f:
            print("ok:", binascii.b2a_base64(f.read()).decode('utf-8'))
    except Exception as e:
        print("error: file error:", e)

@serial_command("list")
def _(args):
    path = "."
    if len(args) > 0:
        path = args[0]
    
    try:
        for item in os.listdir(path):
            # item 0 is st_mode
            is_file = os.stat(path + os.sep + item)[0] >> 15

            if is_file:
                print("file:", item)
            else:
                print("dir:", item)
    except Exception as e:
        print("error: io error:", e)

#Captures Multiple Photos
@serial_command("captureSprint")
def _(args):
    if len(args) < 1:
        print("Capturing 10 images to dir 'sprint'")
        for i in range(1, 11):
            capture(f"image-{i}", "sprint")
    elif len(args) < 2:
        print(f"Capturing 10 images to dir {args[0]}")
        for i in range(1, 11):
            capture(f"image-{i}", args[0])
    else:
        print(f"Capturing {args[1]} images to dir {args[0]}")
        for i in range(1, args[1]+1):
            capture(f"image-{i}", args[0])

@serial_command("capture")
def _(args):
    if len(args) < 1:
        capture("photo_test")
    else:
        capture(args[0])

@serial_command("sort")
def _(args):
    if len(args) < 1:
        print(sortThroughDir("images/test-images"))
    else:
        print(sortThroughDir(f"images/{args[0]}"))

@serial_command("camset")
def _(args):
    if len(args) < 1:
        print("ok: Current camera settings:")
        for k in camset_meta:
            print("ok:", k, ":", camset_meta[k])
    elif len(args) < 2:
        print("error: usage: camset <attr> <int>")
    else:
        attr = args[0]
        value = args[1]

        try:
            value = int(value)
        except ValueError as e:
            print("error: invalid int:", e)
            return
        try:
            setattr(cam, attr, value)
            camset_meta[attr] = value
            print("ok:", attr, "=", value)
        except Exception as e:
            print("error:", e)
            
@serial_command("realloc")
def _(args):
    global buf

    if len(args) < 1:
        print("error: usage: realloc <bufsize>")
        return
    
    try:
        size = int(args[0])
    except ValueError as e:
        print("error: noninteger size provided")
        return
    
    if size < 1:
        print("error: size must be positive")
        return

    print("ok: freeing buffer (memory usage: %s bytes)" % gc.mem_free())
    del buf
    gc.collect()
    print("ok: freed buffer (memory usage: %s bytes)" % gc.mem_free())
    buf = bytearray(size)

    print("ok: reallocated buffer to %s bytes (memory usage: %s bytes)" % (len(buf), gc.mem_free()))

def process_pc_command(cmd):
    if len(cmd) < 1: return

    print("# Processing command:", cmd, "length", len(cmd))

    args = cmd.split(" ")
    command = args.pop(0)

    if command not in serial_commands:
        print("error: unrecognized command")
        return
    
    try:
        serial_commands[command](args)
    except Exception as e:
        print("error: unexpected exception while processing command:", e)

def check_for_pc_command():
    global serial_data_buffer

    while supervisor.runtime.serial_bytes_available:
        data = sys.stdin.read(1)

        if ord(data) == 27:
            # delete, esc, arrow keys, etc.
            # too difficult to handle, just drop the character

            continue
        elif ord(data) == 127:
            # backspace
            serial_data_buffer = serial_data_buffer[:-1]
            print(data, end="") # keep terminal state in sync

            return

        serial_data_buffer += data

        if serial_echo:
            print(data, end="")

        if data == "\n":
            # command terminator
            process_pc_command(serial_data_buffer.strip("\n").strip("\r"))
            serial_data_buffer = ""

while True:
    check_for_pc_command()