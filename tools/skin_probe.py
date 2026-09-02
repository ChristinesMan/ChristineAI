#!/usr/bin/env python3
"""
Body touch sensor probe for the MCP23017 skin sensors.

Answers the three questions that can't be guessed from code:

  1. Which MCP23017 channels have sensors on them?
  2. Which electrical level means "touched"?  (-> CHRISTINE_SKIN_ACTIVE_LOW)
  3. Which Pi GPIO is the expander's INT line wired to?  (-> CHRISTINE_SKIN_IRQ_PIN)

Run it while Christine's service is stopped, so the two aren't fighting over I2C:

    systemctl stop christine
    /root/ChristineAI/venv/bin/python tools/skin_probe.py
    systemctl start christine

Then touch each sensor when prompted. It prints the exact config lines to use.
"""

import sys
import time
from collections import Counter

try:
    import board
    import busio
    from digitalio import Direction, Pull
    from adafruit_mcp230xx.mcp23017 import MCP23017
except ImportError as ex:
    print("Missing a hardware library: %s" % ex)
    print("Run this with Christine's venv python:")
    print("  /root/ChristineAI/venv/bin/python tools/skin_probe.py")
    sys.exit(1)

I2C_ADDRESS = 0x20
IRQ_CANDIDATES = (22, 27, 17)
SETTLE_SECONDS = 3
REST_SAMPLES = 20
WATCH_SECONDS = 45
POLL = 0.01


def main():
    print("=" * 70)
    print("MCP23017 skin sensor probe")
    print("=" * 70)

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        mcp = MCP23017(i2c, address=I2C_ADDRESS)
    except (OSError, ValueError) as ex:
        print("\nCould not reach an MCP23017 at %s: %s" % (hex(I2C_ADDRESS), ex))
        print("Check the I2C cable, and confirm with:  i2cdetect -y -r 1")
        return 1

    print("\nFound MCP23017 at %s" % hex(I2C_ADDRESS))

    pins = []
    for n in range(16):
        p = mcp.get_pin(n)
        p.direction = Direction.INPUT
        p.pull = Pull.UP
        pins.append(p)

    mcp.interrupt_enable = 0xFFFF
    mcp.interrupt_configuration = 0x0000
    mcp.io_control = 0x44          # INT open-drain, mirrored
    mcp.clear_ints()

    # ---------------- resting state ----------------
    print("\nStep 1: resting state.")
    print("  DO NOT TOUCH the sensors. Settling for %ds..." % SETTLE_SECONDS)
    time.sleep(SETTLE_SECONDS)

    tally = [Counter() for _ in range(16)]
    for _ in range(REST_SAMPLES):
        for n, p in enumerate(pins):
            tally[n]["high" if p.value else "low"] += 1
        time.sleep(0.05)

    stable_low, stable_high, unstable = [], [], []
    for n, c in enumerate(tally):
        if c["low"] == REST_SAMPLES:
            stable_low.append(n)
        elif c["high"] == REST_SAMPLES:
            stable_high.append(n)
        else:
            unstable.append(n)

    print("\n  Stable HIGH at rest (pull-up holding, likely UNWIRED): %s"
          % (stable_high if stable_high else "none"))
    print("  Stable LOW  at rest (something pulling down, likely WIRED): %s"
          % (stable_low if stable_low else "none"))
    if unstable:
        print("  UNSTABLE / floating (suspicious): %s" % unstable)

    rest = {n: (1 if tally[n]["high"] > tally[n]["low"] else 0) for n in range(16)}

    # ---------------- live touch ----------------
    print("\nStep 2: live touch test.")
    print("  Touch each sensor in turn, firmly, for about a second each.")
    print("  Watching for %ds. Ctrl-C when you've done them all.\n" % WATCH_SECONDS)

    prev = {n: (1 if pins[n].value else 0) for n in range(16)}
    irq_low_counts = Counter()
    changes = []

    # Read candidate IRQ lines too, if RPi.GPIO will let us.
    gpio = None
    try:
        from RPi import GPIO
        GPIO.setmode(GPIO.BCM)
        for c in IRQ_CANDIDATES:
            GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        gpio = GPIO
    except Exception as ex:  # pylint: disable=broad-exception-caught
        print("  (Could not read IRQ candidate pins: %s)" % ex)
        print("  (Channel mapping will still work.)\n")

    start = time.time()
    try:
        while time.time() - start < WATCH_SECONDS:
            if gpio is not None:
                for c in IRQ_CANDIDATES:
                    if gpio.input(c) == 0:
                        irq_low_counts[c] += 1

            for n, p in enumerate(pins):
                v = 1 if p.value else 0
                if v != prev[n]:
                    direction = "LOW->HIGH" if v else "HIGH->LOW"
                    away = "AWAY FROM REST" if v != rest[n] else "back to rest"
                    port = "A%d" % n if n < 8 else "B%d" % (n - 8)
                    print("  [%s] pin %2d (%s)  %s  (%s)"
                          % (time.strftime("%H:%M:%S"), n, port, direction, away))
                    changes.append((n, v))
                    prev[n] = v
            mcp.clear_ints()
            time.sleep(POLL)
    except KeyboardInterrupt:
        print("\n  (stopped early)")

    # ---------------- conclusions ----------------
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    touched_pins = sorted({n for n, _ in changes})
    if not touched_pins:
        print("\nNo pin activity detected at all.")
        print("Either nothing was touched, or the sensors aren't reaching the expander.")
        print("Wired channels are most likely: %s" % (stable_low or stable_high))
        if gpio is not None:
            gpio.cleanup()
        return 1

    print("\nChannels that responded to touch: %s" % touched_pins)

    # Polarity: did touching move pins away from rest toward HIGH or toward LOW?
    away_high = sum(1 for n, v in changes if v == 1 and rest[n] == 0)
    away_low = sum(1 for n, v in changes if v == 0 and rest[n] == 1)

    print("\nPolarity evidence:")
    print("  transitions to HIGH away from a LOW rest: %d" % away_high)
    print("  transitions to LOW away from a HIGH rest: %d" % away_low)

    if away_high > away_low:
        active_low = "false"
        print("\n  => Touch drives the line HIGH. These sensors are ACTIVE HIGH.")
    elif away_low > away_high:
        active_low = "true"
        print("\n  => Touch pulls the line LOW. These sensors are ACTIVE LOW.")
    else:
        active_low = "true"
        print("\n  => Ambiguous. Defaulting to active low; re-run with cleaner touches.")

    print("\nIRQ pin evidence:")
    if irq_low_counts:
        for c in IRQ_CANDIDATES:
            print("  BCM %2d: %d low samples" % (c, irq_low_counts[c]))
        best = irq_low_counts.most_common(1)[0][0]
        print("\n  => INT line is on BCM %d" % best)
    else:
        best = IRQ_CANDIDATES[0]
        print("  No IRQ pulses captured. Polling will still work.")
        print("  => Leaving CHRISTINE_SKIN_IRQ_PIN at %d" % best)

    print("\n" + "-" * 70)
    print("Suggested .env lines:")
    print("-" * 70)
    print("CHRISTINE_SKIN_ENABLED=true")
    print("CHRISTINE_SKIN_I2C_ADDRESS=%s" % hex(I2C_ADDRESS))
    print("CHRISTINE_SKIN_IRQ_PIN=%d" % best)
    print("CHRISTINE_SKIN_ACTIVE_LOW=%s" % active_low)
    print("CHRISTINE_SKIN_CHANNEL_MAP=%s"
          % ','.join("%d:CHANGE_ME_%d" % (n, n) for n in touched_pins))
    print("-" * 70)
    print("\nReplace CHANGE_ME_n with real body locations, e.g. 'Left Thigh'.")
    print("The order you touched them in is the order listed above.")

    if gpio is not None:
        gpio.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
