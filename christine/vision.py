"""
Handles the camera in wife's forehead. Her first eye.

This module owns /dev/video0 exclusively. Everything that wants to look through
her eye goes through here, because concurrent access to this camera does not
merely fail, it HANGS - two ffmpeg processes opening the device at once leaves
one wedged forever holding the device open, and then nothing can see anything
until it's killed. Hence the lock. Do not open the camera anywhere else.

Two capabilities today:

  measure_light()  - the camera as a light meter, replacing the photoresistors
                     the old body had in its eye sockets.
  snapshot()       - a JPEG frame, for object/face detection or for sending to
                     a vision LLM.

The light meter deserves an explanation, because the obvious approach does not
work. If you leave auto-exposure on and read mean luma, you measure nothing:
the camera's AE loop drives mean luma toward the same middle value in a dark
bedroom and a sunlit one. And this camera won't tell you what exposure the AE
loop chose - exposure_time_absolute reads back as 166 forever and is flagged
inactive whenever auto_exposure is 3.

So instead we take the light reading away from the camera: lock exposure to
manual and walk an exposure ladder until mean luma lands in a band we trust.
Scene luminance is then proportional to luma/exposure. That is a real light
meter with about 10 stops of range instead of one clipped fixed reading.

Measured on the actual hardware (Pi 3B+, 'Generic USB camera' 1e45:8022):

  - luma/exposure is flat within 3% for luma between roughly 12 and 45, and
    bends badly outside it. Hence LUMA_TRUST_LO/HI. Stay in the band.
  - Do NOT try to gamma-linearize luma first. It seems like the principled fix
    and it is dramatically worse: applying gamma 2.2 or 3.0 spread the ratio
    over a factor of 20 across the ladder versus 3% for raw luma. This camera
    has its own tone curve and correcting for a textbook one makes it worse.
  - Repeatability in a fixed scene is excellent, about 0.2% run to run.
  - Cost is dominated by ffmpeg startup and opening the device, not by frame
    count: ~2s of CPU whether you grab 1 frame or 3. But long exposures cost
    real wall time - a 10000us exposure takes ~6.5s to return 3 frames because
    the sensor's frame rate collapses. That's why the poll interval is slow and
    why exposure_dynamic_framerate gets turned off.
"""

import math
import os
import re
import subprocess
import threading
import time

from christine import log
from christine.config import CONFIG

# Exposure ladder in the camera's units (exposure_time_absolute, roughly 100us
# steps per the driver's own scale; treated here as an arbitrary linear unit
# since only ratios matter). Ordered dark-capable last.
EXPOSURE_LADDER = (8, 30, 100, 333, 1000, 3000, 10000)

# Where the ladder starts. Index 4 (1000) is a normally lit indoor room, so most
# measurements settle in one or two captures instead of walking the whole ladder.
LADDER_START_INDEX = 4

# The band where luma/exposure is actually proportional to scene luminance.
LUMA_TRUST_LO = 12.0
LUMA_TRUST_HI = 45.0

# Beyond the trust band we still accept a reading rather than failing, because
# at the ends of the ladder there is nowhere left to go. These are the hard
# clipping limits where the number is meaningless.
LUMA_USABLE_LO = 0.5
LUMA_USABLE_HI = 235.0

_YAVG_RE = re.compile(r"signalstats\.YAVG=([0-9.]+)")


class Vision:
    """Owns the forehead camera. Thread-safe; serializes all device access."""

    def __init__(self):
        # One lock for the whole device. Light metering and snapshots must never
        # overlap. See module docstring for what happens if they do.
        self.lock = threading.Lock()

        self.device = CONFIG.camera_device

        # Remember where the ladder settled last time, so a stable room costs
        # one capture instead of a walk.
        self.last_exposure_index = LADDER_START_INDEX

        # Whether we've already pushed the manual-exposure setup to the camera.
        self.configured = False

    # ---------------------------------------------------------------- plumbing

    def _v4l2_set(self, **controls):
        """Set v4l2 controls. Returns True if the call succeeded."""
        args = []
        for key, value in controls.items():
            args += ["-c", f"{key}={value}"]
        try:
            result = subprocess.run(
                ["v4l2-ctl", "-d", self.device] + args,
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.light.warning("v4l2-ctl failed: %s", exc)
            return False
        if result.returncode != 0:
            log.light.warning("v4l2-ctl returned %s: %s",
                              result.returncode, result.stderr.strip())
            return False
        return True

    def _configure_for_metering(self):
        """Lock the camera down so luma means something.

        Every one of these matters:
          auto_exposure=1              manual, so exposure is ours to set
          white_balance_automatic=0    stop AWB from shifting luma under us
          exposure_dynamic_framerate=0 stop the sensor from silently dropping
                                       framerate in low light, which is what
                                       turns a capture into a 6 second stall
          gain fixed                   another AE knob that would drift
        """
        ok = self._v4l2_set(
            auto_exposure=1,
            white_balance_automatic=0,
            exposure_dynamic_framerate=0,
            gain=CONFIG.camera_gain,
        )
        self.configured = ok
        return ok

    def _grab_luma(self, frames=2, size="320x240"):
        """Capture and return mean luma (0-255), or None."""
        cmd = [
            "ffmpeg", "-hide_banner",
            "-f", "v4l2", "-input_format", "mjpeg",
            "-video_size", size, "-i", self.device,
            "-frames:v", str(frames),
            "-vf", "signalstats,metadata=print",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=CONFIG.camera_capture_timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired:
            # A timeout here usually means something else has the device open.
            log.light.warning("Camera capture timed out after %ss",
                              CONFIG.camera_capture_timeout_seconds)
            return None
        except FileNotFoundError:
            log.light.error("ffmpeg not found; camera light metering disabled")
            return None

        values = _YAVG_RE.findall(result.stderr)
        if not values:
            log.light.warning("No luma in ffmpeg output: %s",
                              result.stderr.strip()[-300:])
            return None

        # Last frame, since the first frame out of the device can be stale.
        return float(values[-1])

    # ------------------------------------------------------------ light meter

    def measure_light(self):
        """Auto-ranging light measurement.

        Returns a dict with the raw findings, or None on failure:
          luminance  - proportional to scene luminance, arbitrary units
          log10      - log10(luminance), the useful perceptual quantity
          exposure   - exposure the ladder settled on
          luma       - mean luma at that exposure
          captures   - how many captures it took
          saturated  - 'dark' or 'bright' if we ran out of ladder, else None
        """
        with self.lock:
            return self._measure_light_locked()

    def _measure_light_locked(self):
        started = time.time()

        if not self.configured and not self._configure_for_metering():
            return None

        index = self.last_exposure_index
        captures = 0
        luma = None
        exposure = EXPOSURE_LADDER[index]
        saturated = None

        # Walk the ladder. Bounded by its own length so this cannot spin.
        for _ in range(len(EXPOSURE_LADDER)):
            exposure = EXPOSURE_LADDER[index]

            if not self._v4l2_set(exposure_time_absolute=exposure):
                return None

            luma = self._grab_luma()
            captures += 1

            if luma is None:
                return None

            if luma < LUMA_TRUST_LO:
                if index < len(EXPOSURE_LADDER) - 1:
                    index += 1      # too dark, open up
                    continue
                saturated = "dark"  # already wide open; it really is that dark
                break

            if luma > LUMA_TRUST_HI:
                if index > 0:
                    index -= 1        # too bright, close down
                    continue
                saturated = "bright"  # already stopped all the way down
                break

            break  # landed in the trust band

        self.last_exposure_index = index

        if luma is None:
            return None

        # Below the usable floor the sensor is reading its own noise. Report
        # true darkness rather than a ratio computed from nothing, because the
        # ratio between tiny values is exactly what used to wake her up at night.
        if luma < LUMA_USABLE_LO:
            luminance = 0.0
            # Nothing measurable. Hand back a sentinel far below any real
            # reading; light.py clips it to full darkness.
            log10 = -9.0
        else:
            # Above the usable ceiling the sensor is clipping, so the ratio
            # understates the scene. Note it; the ladder has nothing left.
            if luma > LUMA_USABLE_HI and saturated is None:
                saturated = "bright"
            luminance = luma / exposure
            log10 = math.log10(max(luminance, 1e-9))

        result = {
            "luminance": luminance,
            "log10": log10,
            "exposure": exposure,
            "luma": luma,
            "captures": captures,
            "saturated": saturated,
            "seconds": time.time() - started,
        }

        log.light.debug(
            "Meter: luma=%.2f exp=%d lum=%.6g log10=%.2f caps=%d sat=%s %.2fs",
            luma, exposure, luminance, log10, captures, saturated,
            result["seconds"],
        )
        return result

    # --------------------------------------------------------------- snapshot

    def snapshot(self, path=None, size=None, auto_exposure=True, warmup=None):
        """Grab a JPEG frame for object detection or a vision LLM.

        Unlike metering, this wants a picture a human or a model can read, so it
        hands exposure back to the camera's own AE loop and burns some warmup
        frames to let it settle. Measured: frame 1 was badly overexposed and it
        had settled by roughly frame 8-20.

        Returns the path written, or None on failure. Leaves the camera needing
        reconfiguration before the next light measurement, which is handled by
        clearing self.configured.
        """
        size = size or CONFIG.camera_snapshot_size
        warmup = CONFIG.camera_snapshot_warmup_frames if warmup is None else warmup
        if path is None:
            os.makedirs(CONFIG.camera_snapshot_dir, exist_ok=True)
            path = os.path.join(
                CONFIG.camera_snapshot_dir,
                time.strftime("%Y%m%d_%H%M%S") + ".jpg",
            )

        with self.lock:
            if auto_exposure:
                # Aperture Priority Mode (3) is this camera's auto exposure.
                self._v4l2_set(auto_exposure=3, white_balance_automatic=1)
                # Any AE change invalidates the metering setup.
                self.configured = False

            tmp_pattern = path + ".%03d.tmp.jpg"
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "v4l2", "-input_format", "mjpeg",
                "-video_size", size, "-i", self.device,
                "-frames:v", str(max(1, warmup)), "-y", tmp_pattern,
            ]
            try:
                subprocess.run(
                    cmd, capture_output=True, text=True, check=False,
                    timeout=CONFIG.camera_capture_timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                log.light.warning("Snapshot timed out")
                _cleanup_tmp(path, warmup)
                return None
            except FileNotFoundError:
                log.light.error("ffmpeg not found; snapshot unavailable")
                return None

            # Keep the last frame written, discard the unsettled ones.
            kept = None
            for n in range(max(1, warmup), 0, -1):
                candidate = tmp_pattern % n
                if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                    kept = candidate
                    break
            if kept is None:
                log.light.warning("Snapshot produced no frames")
                _cleanup_tmp(path, warmup)
                return None

            try:
                os.replace(kept, path)
            except OSError as exc:
                log.light.warning("Could not write snapshot: %s", exc)
                _cleanup_tmp(path, warmup)
                return None

            _cleanup_tmp(path, warmup)
            log.light.info("Snapshot: %s (%d bytes)", path,
                           os.path.getsize(path))
            return path


def _cleanup_tmp(path, warmup):
    for n in range(0, max(1, warmup) + 1):
        try:
            os.remove(path + ".%03d.tmp.jpg" % n)
        except OSError:
            pass


# Instantiate
vision = Vision()
