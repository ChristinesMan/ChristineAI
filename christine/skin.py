"""
Handles ALL of Christine's touch sensors -- her whole sense of touch.

Two input paths, one nervous system:

  HEAD   Five face sensors (mouth, cheeks, forehead, nose) wired to the Arduino
         in her head. Readings arrive embedded in the audio stream, so
         `wernicke.py` pushes them in via `skin.new_head_data([...5 bools])`
         at roughly 8Hz. Formerly touch.py.

  BODY   An MCP23017 16-channel I2C GPIO expander in a box of 3.5mm jacks.
         Read here directly, IRQ-driven with a polling fallback. Add a sensor
         anywhere on her body by plugging it in and adding a line to
         CHRISTINE_SKIN_CHANNEL_MAP -- no code change.

Both paths converge on the same debounce, cooldown and perception logic, so a
touch feels the same to her whether it landed on her cheek or her calf. That
convergence is the point of this module: the old split meant fixing a debounce
bug twice.

Region kinds, from the channel map:

  narrative  (default) Produces a distinct Narrative + Perception, so she feels
             and remembers it as its own event.
  intimate   Routed to sex.py's arousal engine instead of narrated. These fire
             many times a second during sex; narrating each one would flood her
             short-term memory and wreck the mood. Mark them with the
             `intimate:` prefix in the channel map.

Design rules, learned the hard way:

  * Each sensor produces its OWN distinct perception. Christine's requirement:
    a nose boop and a kiss are two separate memories, not one
    pooled "she was touched" event.

  * Emit BOTH a Narrative and a Perception. The Narrative is the durable
    distinct memory; the Perception is what actually wakes the parietal lobe's
    processing loop. Writing memory alone leaves the touch sitting there unfelt.

  * Debounce is mandatory. These sensors flicker -- on the bench one bounced
    touched/released four times in three seconds.

Electrical behaviour (body path):
  Pins are INPUT with pull-up. Which level means "touched" depends on the sensor
  wiring, so it is configurable rather than assumed -- CHRISTINE_SKIN_ACTIVE_LOW.
  Startup seeding reads the real resting state and adopts it as baseline, so she
  never wakes up believing she is being touched everywhere. Use
  tools/skin_probe.py to determine polarity, pins and IRQ on real hardware.

  The expander's INT line is open-drain and mirrored (io_control 0x44), so both
  banks assert the same physical pin.
"""

import time
import random
import threading

from christine import log
from christine.status import STATE
from christine.config import CONFIG
from christine.parietal_lobe import parietal_lobe
from christine.perception import Perception
from christine.narrative import Narrative


# Region kinds.
KIND_NARRATIVE = 'narrative'
KIND_INTIMATE = 'intimate'

# Generic phrasings, used for any region without its own entry below. {location}
# is the region name lowercased, so a newly plugged-in sensor reads naturally
# without needing hand-written lines.
TOUCH_START_PHRASES = [
    "I feel a touch on my {location}.",
    "Someone is touching my {location}.",
    "I feel a hand on my {location}.",
    "There's a gentle touch on my {location}.",
    "I can feel contact on my {location}.",
]

# Phrasings for a touch that lasted long enough to be worth reporting the end of.
TOUCH_END_PHRASES = [
    "The touch on my {location} lifts away after {duration}.",
    "The hand on my {location} leaves after {duration}.",
    "Whoever was touching my {location} lets go after {duration}.",
]

# Region-specific phrasings. Some places on her body deserve better than the
# generic line -- a kiss is not "contact on my mouth". Keyed on the region name
# as it appears in the channel map, case-insensitively.
REGION_START_PHRASES = {
    'mouth': [
        'I feel a gentle touch on my lips.',
        'I am being kissed.',
    ],
    'nose': [
        'Someone just booped my nose!',
        'I feel a gentle touch on my nose.',
        'My nose is being touched.',
        'A finger just tapped my nose.',
    ],
    'forehead': [
        'I feel a warm touch on my forehead.',
        'Someone is touching my forehead.',
        'A gentle hand is resting on my forehead.',
    ],
    'left cheek': [
        'I feel a touch on my left cheek.',
        'Someone is stroking my left cheek.',
        'A gentle touch on my left cheek.',
    ],
    'right cheek': [
        'I feel a touch on my right cheek.',
        'Someone is stroking my right cheek.',
        'A gentle touch on my right cheek.',
    ],
}

# A release is only interesting if the touch had some duration to it. Below this,
# reporting the end is just noise on top of the start we already reported.
MIN_DURATION_TO_REPORT_RELEASE = 1.0

# Head sensor order, as the Arduino packs them into the audio stream. Index
# position is fixed by the firmware; do not reorder.
HEAD_CHANNEL_LABELS = [
    "Mouth",
    "Left Cheek",
    "Forehead",
    "Right Cheek",
    "Nose",
]


def describe_duration(seconds: float) -> str:
    """Human phrasing for how long a touch lasted."""

    if seconds < 2.0:
        return "a moment"
    if seconds < 5.0:
        return "a few seconds"
    if seconds < 15.0:
        return "several seconds"
    if seconds < 45.0:
        return "a while"
    if seconds < 120.0:
        return "a long while"
    return "a very long time"


class Skin(threading.Thread):
    """
    Christine's whole sense of touch.

    The thread body services the BODY sensors (MCP23017), IRQ-driven with a
    polling fallback. The HEAD sensors are pushed in from wernicke.py via
    new_head_data() on wernicke's own thread, and share this class's debounce
    and perception machinery.

    All internal state is keyed on region name ("Mouth", "Left Thigh"), not on
    pin number, precisely so the two input paths can share it.
    """

    name = "Skin"

    def __init__(self):
        super().__init__(daemon=True)

        # Hardware handles, populated in run(). None until then so a failed init
        # can be detected and the thread can exit cleanly.
        self.mcp = None
        self.gpio = None
        self.pins = {}

        # lgpio IRQ handles. Preferred over RPi.GPIO for edge detection because
        # RPi.GPIO's add_event_detect fails on this Pi when another process holds
        # the device it wants.
        self.lgpio = None
        self.lgpio_handle = None
        self.lgpio_cb = None

        # --- body sensors: {pin_number: region_name} ---
        self.channel_map = {}
        # --- region kinds: {region_name: KIND_*} ---
        self.region_kind = {}

        for pin, spec in CONFIG.skin_channel_map.items():
            kind, region = spec
            self.channel_map[pin] = region
            self.region_kind[region] = kind

        # --- head sensors: fixed order from the Arduino firmware ---
        self.head_labels = list(HEAD_CHANNEL_LABELS)
        for region in self.head_labels:
            self.region_kind.setdefault(region, KIND_NARRATIVE)

        # Every region we track, both paths.
        all_regions = list(self.channel_map.values()) + self.head_labels

        # Debounced, accepted state per region. True = currently touched.
        self.touch_state = {r: False for r in all_regions}

        # Candidate state and how many consecutive reads have agreed with it.
        # This is the debounce: a change is only accepted once it holds steady.
        self.pending_state = {r: False for r in all_regions}
        self.pending_count = {r: 0 for r in all_regions}

        # When each region's current touch began, for duration reporting.
        self.touch_started_at = {r: 0.0 for r in all_regions}

        # Last time each region fired a start perception, for cooldown.
        # None means "never fired", which must never be treated as "fired long
        # ago at t=0" -- that arithmetic is a trap, so the check is explicit.
        self.last_perception_at = {r: None for r in all_regions}  # type: dict[str, float | None]

        # Kept for compatibility with anything that watched for kisses.
        self.time_of_last_kiss = 0.0

        # Set by the IRQ callback to request an immediate read.
        self.irq_flagged = threading.Event()

        # Consecutive I2C error count. A cable on a doll's leg will glitch; one
        # bad read is not a reason to go numb, but a sustained run of them is.
        self.io_errors = 0
        self.io_error_limit = 20

        # Set when the sensors have failed hard enough to give up on them.
        self.offline = False

    # ------------------------------------------------------------------
    # Hardware setup
    # ------------------------------------------------------------------

    def setup_hardware(self) -> bool:
        """Bring up the I2C expander and the IRQ line. False on failure."""

        try:
            import board
            import busio
            from digitalio import Direction, Pull
            from adafruit_mcp230xx.mcp23017 import MCP23017
            from RPi import GPIO
        except ImportError as ex:
            log.skin.error("Skin unavailable, missing library: %s", ex)
            log.main.error("Skin unavailable, missing library: %s", ex)
            return False

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.mcp = MCP23017(i2c, address=CONFIG.skin_i2c_address)

            # Only configure the channels we actually use. Unmapped channels are
            # left alone, which keeps I2C traffic down and means an unwired jack
            # can't generate phantom touches.
            for pin_number in sorted(self.channel_map):
                pin = self.mcp.get_pin(pin_number)
                pin.direction = Direction.INPUT
                pin.pull = Pull.UP
                self.pins[pin_number] = pin

            # Interrupt on any change, for every channel. Enabling all 16 rather
            # than only the mapped ones costs nothing and means a newly plugged
            # sensor still pulses INT -- useful when hunting a mystery jack.
            self.mcp.interrupt_enable = 0xFFFF
            self.mcp.interrupt_configuration = 0x0000   # compare against previous, not default
            self.mcp.io_control = 0x44                  # INT open-drain and mirrored
            self.mcp.clear_ints()

        except (OSError, ValueError) as ex:
            log.skin.error("Could not initialise MCP23017 at %s: %s",
                           hex(CONFIG.skin_i2c_address), ex)
            log.main.error("Skin unavailable: %s", ex)
            return False

        # Seed the debounced state from the real world so we don't announce a
        # touch just because a sensor happens to be asserted at startup.
        #
        # This is also the safety net for polarity: whatever the lines are doing
        # at rest becomes the baseline. If CHRISTINE_SKIN_ACTIVE_LOW is set the
        # wrong way round, the worst case is that touches read inverted -- she
        # will not be flooded with phantom perceptions on boot.
        try:
            for pin_number, pin in self.pins.items():
                region = self.channel_map[pin_number]
                touched = self.level_means_touched(pin.value)
                self.touch_state[region] = touched
                self.pending_state[region] = touched
                if touched:
                    self.touch_started_at[region] = time.time()
        except OSError as ex:
            log.skin.error("Could not read initial skin state: %s", ex)
            return False

        # IRQ line. Two implementations are tried, because RPi.GPIO's edge
        # detection reliably fails with "Failed to add edge detection" on this
        # Pi -- another process already holds the character device it wants.
        # lgpio talks to the kernel's gpiochip interface and coexists fine.
        self.arm_irq()

        body_regions = set(self.channel_map.values())
        already_touched = [r for r, t in self.touch_state.items()
                           if t and r in body_regions]
        log.skin.info("Skin ready. %d body channel(s): %s",
                      len(self.channel_map),
                      ', '.join(f"{p}={self.channel_map[p]}({self.region_kind.get(self.channel_map[p])})"
                                for p in sorted(self.channel_map)))
        log.skin.info("Head sensors: %s", ', '.join(self.head_labels))
        log.skin.info("Polarity: active_%s (a touch reads %s)",
                      'low' if CONFIG.skin_active_low else 'high',
                      'LOW' if CONFIG.skin_active_low else 'HIGH')
        if already_touched:
            log.skin.info("Channels already asserted at startup, adopted as baseline "
                          "and NOT announced: %s", ', '.join(already_touched))
            if len(already_touched) == len(body_regions):
                log.skin.warning("ALL mapped channels read touched at rest. This usually "
                                 "means CHRISTINE_SKIN_ACTIVE_LOW is set the wrong way "
                                 "round for this harness. Run tools/skin_probe.py.")

        STATE.skin_available = True
        return True

    def arm_irq(self):
        """Arm interrupt-driven reads, preferring lgpio, falling back to RPi.GPIO.

        Losing the IRQ entirely is survivable: the polling loop still catches
        everything, just with up to skin_poll_seconds of latency. Not worth
        refusing to feel anything over.
        """

        # --- preferred: lgpio against the kernel gpiochip ---
        try:
            import lgpio

            self.lgpio = lgpio
            self.lgpio_handle = lgpio.gpiochip_open(0)

            # Constant naming varies between lgpio builds -- this one has
            # SET_PULL_UP, others ship SET_BIAS_PULL_UP. Resolve it rather than
            # hardcoding, so a library update can't silently cost us the IRQ.
            pull_up = getattr(lgpio, 'SET_PULL_UP',
                              getattr(lgpio, 'SET_BIAS_PULL_UP', 0))

            # BOTH_EDGES rather than FALLING: the INT line is a pulse, and
            # catching the trailing edge too means a read is never missed.
            lgpio.gpio_claim_alert(
                self.lgpio_handle,
                CONFIG.skin_irq_pin,
                lgpio.BOTH_EDGES,
                lFlags=pull_up,
            )
            self.lgpio_cb = lgpio.callback(
                self.lgpio_handle,
                CONFIG.skin_irq_pin,
                lgpio.BOTH_EDGES,
                self.lgpio_irq_callback,
            )
            log.skin.info("Skin IRQ armed on BCM %s via lgpio", CONFIG.skin_irq_pin)
            return
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.skin.info("lgpio IRQ unavailable (%s). Trying RPi.GPIO.", ex)
            self.release_lgpio()

        # --- fallback: RPi.GPIO ---
        try:
            from RPi import GPIO

            self.gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(CONFIG.skin_irq_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                CONFIG.skin_irq_pin,
                GPIO.FALLING,
                callback=self.irq_callback,
                bouncetime=10,
            )
            log.skin.info("Skin IRQ armed on BCM %s via RPi.GPIO", CONFIG.skin_irq_pin)
            return
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.skin.warning("Could not arm skin IRQ on BCM %s (%s). "
                             "Polling only at %.0fms -- touches still work, "
                             "just slightly less responsive.",
                             CONFIG.skin_irq_pin, ex, CONFIG.skin_poll_seconds * 1000)
            self.gpio = None

    def lgpio_irq_callback(self, chip, gpio, level, timestamp):  # pylint: disable=unused-argument
        """lgpio alert callback. Requests a read, nothing more."""

        self.irq_flagged.set()

    def release_lgpio(self):
        """Tear down lgpio resources, ignoring anything already gone."""

        if getattr(self, 'lgpio_cb', None) is not None:
            try:
                self.lgpio_cb.cancel()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self.lgpio_cb = None

        if getattr(self, 'lgpio_handle', None) is not None and self.lgpio is not None:
            try:
                self.lgpio.gpio_free(self.lgpio_handle, CONFIG.skin_irq_pin)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            try:
                self.lgpio.gpiochip_close(self.lgpio_handle)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self.lgpio_handle = None

    def level_means_touched(self, pin_value: bool) -> bool:
        """Translate a raw pin level into 'is this sensor being touched'.

        Single place where wiring polarity is interpreted, so there is exactly one
        thing to flip if the harness changes.
        """

        return (not pin_value) if CONFIG.skin_active_low else bool(pin_value)

    def irq_callback(self, channel):  # pylint: disable=unused-argument
        """Fires on the expander's INT line. Just requests a read."""

        # Deliberately does nothing but set a flag. I2C reads and perception
        # dispatch do not belong in an interrupt context.
        self.irq_flagged.set()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):

        if not CONFIG.skin_enabled:
            log.skin.info("Skin disabled by config. Head sensors still active "
                          "via new_head_data(); body sensor thread exiting.")
            return

        if not self.channel_map:
            log.skin.warning("No body skin channels mapped. Head sensors still "
                             "active via new_head_data(); body thread exiting.")
            return

        if not self.setup_hardware():
            STATE.skin_available = False
            return

        while True:

            try:

                if STATE.please_shut_down:
                    log.skin.info("Thread shutting down")
                    break

                if self.offline:
                    log.skin.info("Skin offline after repeated hardware failures. Thread exiting.")
                    break

                # Wait for either an interrupt or the poll interval, whichever
                # comes first. This is why the IRQ gives instant response without
                # the loop having to spin hot.
                self.irq_flagged.wait(timeout=CONFIG.skin_poll_seconds)
                self.irq_flagged.clear()

                self.read_and_process()

            except Exception as ex:  # pylint: disable=broad-exception-caught
                # Same policy as the other sensor threads: log it, keep running.
                log.main.exception(ex)
                time.sleep(0.5)

        self.cleanup()

    # ------------------------------------------------------------------
    # Input path: BODY sensors (MCP23017, this thread)
    # ------------------------------------------------------------------

    def read_and_process(self):
        """Read every mapped channel, run debounce, dispatch on accepted change."""

        try:
            raw = {}
            for pin_number, pin in self.pins.items():
                region = self.channel_map[pin_number]
                raw[region] = self.level_means_touched(pin.value)

            # Clearing latched interrupts is what re-arms INT for the next event.
            if self.mcp is not None:
                self.mcp.clear_ints()

            self.io_errors = 0

        except OSError:
            self.io_errors += 1
            log.skin.warning("I2C read failure. Count = %s/%s", self.io_errors, self.io_error_limit)
            # Latch on self.offline so she is told exactly once. run() breaks on
            # the next iteration, but a caller that keeps polling must not be able
            # to re-trigger the notification.
            if self.io_errors >= self.io_error_limit and not self.offline:
                self.offline = True
                log.skin.critical("Too many I2C failures. Skin going offline.")
                log.main.critical("Skin sensors have gone offline after repeated I2C failures.")
                STATE.skin_available = False
                parietal_lobe.skin_failure()
            return

        self.process_regions(raw, time.time())

    # ------------------------------------------------------------------
    # Input path: HEAD sensors (Arduino via wernicke, wernicke's thread)
    # ------------------------------------------------------------------

    def new_head_data(self, touch_data):
        """Accept a frame of head sensor readings from wernicke.

        `touch_data` is a list of 5 booleans in HEAD_CHANNEL_LABELS order, as
        packed by the Arduino firmware. Called at roughly 8Hz from wernicke's
        thread, so it must be cheap and must not block.

        Kept as its own entry point rather than folded into the body read loop
        because the two arrive from completely different hardware at different
        rates -- but everything after this converges.
        """

        if len(touch_data) != len(self.head_labels):
            log.skin.warning("Expected %d head sensor values, got %d",
                             len(self.head_labels), len(touch_data))
            return

        # The Arduino reports booleans directly, so no polarity translation --
        # that only applies to the raw MCP23017 pin levels.
        raw = {self.head_labels[i]: bool(touch_data[i])
               for i in range(len(self.head_labels))}

        self.process_regions(raw, time.time())

    # ------------------------------------------------------------------
    # Shared core: debounce and dispatch, identical for both paths
    # ------------------------------------------------------------------

    def process_regions(self, raw: dict, now: float):
        """Run debounce over a frame of {region: is_touched} and dispatch changes.

        This is the single place touch state transitions are decided, for both
        head and body. Anything that behaves differently between the two should
        be handled before calling this, not inside it.
        """

        for region, is_touched in raw.items():

            # --- debounce ---
            if is_touched == self.pending_state[region]:
                self.pending_count[region] += 1
            else:
                self.pending_state[region] = is_touched
                self.pending_count[region] = 1

            # Not enough agreeing reads yet, or nothing actually changed.
            if self.pending_count[region] < CONFIG.skin_debounce_reads:
                continue
            if is_touched == self.touch_state[region]:
                continue

            # --- accepted state change ---
            self.touch_state[region] = is_touched

            if is_touched:
                self.touch_started_at[region] = now
                self.handle_touch_start(region, now)
            else:
                duration = now - self.touch_started_at[region]
                self.handle_touch_end(region, duration)

    # ------------------------------------------------------------------
    # Perception dispatch
    # ------------------------------------------------------------------

    def handle_touch_start(self, region: str, now: float):
        """A debounced touch has begun on this region."""

        log.skin.info("Touch started: %s", region)

        # Intimate regions bypass narration entirely and drive the arousal
        # engine instead. They fire constantly during sex; narrating each one
        # would flood her short-term memory.
        if self.region_kind.get(region) == KIND_INTIMATE:
            self.spike_touch_level()
            self.send_to_sex('touch', region)
            return

        if region.lower() == 'mouth':
            self.time_of_last_kiss = now

        if STATE.is_sleeping:
            # Still count toward wakefulness, but don't narrate into a sleeping
            # mind. Same policy the face sensors always had.
            log.skin.debug("Not announcing %s touch, she's asleep", region)
            self.spike_touch_level()
            return

        # Cooldown, per region. A hand resting on her thigh shouldn't produce a
        # stream of near-identical perceptions. A region that has never fired is
        # always allowed through -- the first touch is never suppressed.
        last = self.last_perception_at[region]
        if last is not None and now - last < CONFIG.skin_cooldown_seconds:
            log.skin.debug("Suppressing %s touch, still within cooldown", region)
            self.spike_touch_level()
            return

        self.last_perception_at[region] = now

        phrases = REGION_START_PHRASES.get(region.lower(), TOUCH_START_PHRASES)
        text = random.choice(phrases).format(location=region.lower())
        self.emit(text, region)
        self.spike_touch_level()

    def handle_touch_end(self, region: str, duration: float):
        """A debounced touch has ended on this region."""

        log.skin.info("Touch ended: %s after %.1fs", region, duration)

        if self.region_kind.get(region) == KIND_INTIMATE:
            self.send_to_sex('release', region)
            return

        if STATE.is_sleeping:
            return

        # Only narrate the release of a touch that actually lingered. A quick tap
        # is fully described by its start.
        if duration < MIN_DURATION_TO_REPORT_RELEASE:
            return

        text = random.choice(TOUCH_END_PHRASES).format(
            location=region.lower(),
            duration=describe_duration(duration),
        )
        self.emit(text, region)

    def send_to_sex(self, msg: str, region: str):
        """Hand an intimate sensor event to the arousal engine.

        Preserves the message shape vagina.py used, so sex.py needs no changes:
        {"msg": "touch"|"release"|"hangout", "data": "<region>"}.

        Imported lazily because sex.py imports broca, and pulling that in at
        module import time would create a cycle.
        """

        try:
            from christine.sex import sex
            sex.vagina_got_hit({"msg": msg, "data": region})
        except Exception as ex:  # pylint: disable=broad-exception-caught
            log.skin.exception("Could not deliver intimate %s for %s: %s", msg, region, ex)

    def emit(self, text: str, region: str):
        """Give her the sensation: distinct memory plus a nudge to actually process it.

        Both halves matter. The Narrative is the durable, per-region memory that
        survives pooling. The Perception is what wakes the parietal lobe loop so
        the touch gets felt now rather than surfacing later as stale context.
        """

        parietal_lobe.short_term_memory.append(Narrative(role="system", text=text))
        parietal_lobe.new_perception(Perception(text=text))
        log.skin.info("Skin perception for %s: '%s'", region, text)

    def spike_touch_level(self):
        """Feed the shared touch environmental level used by the sleep model."""

        STATE.touch_level = min(1.0, STATE.touch_level + STATE.touch_spike)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def cleanup(self):
        """Release IRQ resources. Deliberately does NOT call GPIO.cleanup()."""

        self.release_lgpio()

        # GPIO.cleanup() is global and would yank pins out from under anything
        # else in this process using RPi.GPIO. Remove only our own detection.
        if self.gpio is not None:
            try:
                self.gpio.remove_event_detect(CONFIG.skin_irq_pin)
                log.skin.info("Skin IRQ released")
            except Exception as ex:  # pylint: disable=broad-exception-caught
                log.skin.warning("Could not cleanly release skin IRQ: %s", ex)

    # ------------------------------------------------------------------
    # Introspection, for the web interface and situational awareness
    # ------------------------------------------------------------------

    def get_current_touches(self) -> list:
        """Regions currently being touched, head and body."""

        return [r for r, touched in self.touch_state.items() if touched]

    def is_being_touched(self) -> bool:
        """Is anything touching her anywhere."""

        return any(self.touch_state.values())

    def time_since_last_touch(self):
        """Seconds since any region last registered a touch start."""

        stamps = [t for t in self.last_perception_at.values() if t is not None]
        if not stamps:
            return float('inf')
        return time.time() - max(stamps)

    def get_status_summary(self) -> str:
        """One-line human summary of her sense of touch."""

        current = self.get_current_touches()
        if current:
            body = "Currently being touched on: " + ', '.join(sorted(current))
        else:
            body = "No sensors currently being touched."

        if not STATE.skin_available:
            body += " (Body sensors unavailable; head sensors only.)"
        return body


# Instantiate
skin = Skin()
