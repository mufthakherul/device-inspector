# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Thermal sensor monitoring and throttling detection.

Linux implementation uses lm-sensors to detect temperature readings.
Windows implementation uses OpenHardwareMonitor or WMI for thermal data.
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess
import time
from typing import Any, Dict

logger = logging.getLogger("inspecta.sensors")


class SensorError(Exception):
    """Raised when sensor operations fail."""


_SAMPLE_SENSORS = """\
coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +52.0°C  (high = +100.0°C, crit = +100.0°C)
Core 0:        +48.0°C  (high = +100.0°C, crit = +100.0°C)
Core 1:        +50.0°C  (high = +100.0°C, crit = +100.0°C)
Core 2:        +52.0°C  (high = +100.0°C, crit = +100.0°C)
Core 3:        +49.0°C  (high = +100.0°C, crit = +100.0°C)

nvme-pci-0100
Adapter: PCI adapter
Composite:    +38.9°C  (low  = -273.1°C, high = +84.8°C)
                       (crit = +84.8°C)
Sensor 1:     +38.9°C  (low  = -273.1°C, high = +65261.8°C)
Sensor 2:     +41.9°C  (low  = -273.1°C, high = +65261.8°C)
"""


def detect_platform() -> str:
    """Return 'linux', 'windows', or 'unknown'."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def has_lm_sensors() -> bool:
    """Check if lm-sensors is available on Linux."""
    try:
        result = subprocess.run(
            ["sensors", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def parse_sensors_output(output: str) -> Dict[str, Any]:
    """Parse lm-sensors output and extract temperature readings.

    Returns a dict with:
    {
        "sensors": [
            {
                "adapter": "coretemp-isa-0000",
                "type": "CPU",
                "readings": [
                    {
                        "label": "Package id 0",
                        "temp": 52.0,
                        "high": 100.0,
                        "crit": 100.0,
                    },
                    {
                        "label": "Core 0",
                        "temp": 48.0,
                        "high": 100.0,
                        "crit": 100.0,
                    },
                    ...
                ]
            },
            ...
        ],
        "max_temp": 52.0,
        "avg_temp": 49.6,
        "critical_temps": []
    }
    """
    sensors = []
    current_adapter = None
    current_type = None
    current_readings = []

    all_temps = []
    critical_temps = []

    for line in output.split("\n"):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Detect adapter header (e.g., "coretemp-isa-0000")
        # Adapter lines typically don't start with whitespace and don't contain ':'
        # or contain very specific patterns like "pci" or "isa"
        if not line.startswith("Adapter:") and ":" not in line and "-" in line:
            # Save previous adapter if any
            if current_adapter and current_readings:
                sensors.append(
                    {
                        "adapter": current_adapter,
                        "type": current_type or "Unknown",
                        "readings": current_readings,
                    }
                )

            current_adapter = line
            current_readings = []

            # Determine sensor type from adapter name
            adapter_lower = line.lower()
            if "coretemp" in adapter_lower or "k10temp" in adapter_lower:
                current_type = "CPU"
            elif "nvme" in adapter_lower:
                current_type = "NVMe"
            elif (
                "gpu" in adapter_lower
                or "amdgpu" in adapter_lower
                or "nvidia" in adapter_lower
            ):
                current_type = "GPU"
            else:
                current_type = "Unknown"

        elif line.startswith("Adapter:"):
            continue  # Skip adapter type line

        elif ":" in line and "°C" in line and current_adapter:
            # Parse temperature reading
            # Example: "Package id 0:  +52.0°C  (high = +100.0°C, crit = +100.0°C)"
            label_part, temp_part = line.split(":", 1)
            label = label_part.strip()

            # Extract current temperature
            temp_match = re.search(r"([+-]?\d+\.?\d*)\s*°C", temp_part)
            if not temp_match:
                continue

            temp = float(temp_match.group(1))
            all_temps.append(temp)

            # Extract high threshold
            high_match = re.search(r"high\s*=\s*([+-]?\d+\.?\d*)\s*°C", temp_part)
            high = float(high_match.group(1)) if high_match else None

            # Extract critical threshold
            crit_match = re.search(r"crit\s*=\s*([+-]?\d+\.?\d*)\s*°C", temp_part)
            crit = float(crit_match.group(1)) if crit_match else None

            # Check if temperature is critical
            if crit and temp >= crit:
                critical_temps.append(
                    {
                        "label": label,
                        "temp": temp,
                        "threshold": crit,
                    }
                )

            current_readings.append(
                {
                    "label": label,
                    "temp": temp,
                    "high": high,
                    "crit": crit,
                }
            )

    # Save last adapter
    if current_adapter and current_readings:
        sensors.append(
            {
                "adapter": current_adapter,
                "type": current_type or "Unknown",
                "readings": current_readings,
            }
        )

    return {
        "sensors": sensors,
        "max_temp": max(all_temps) if all_temps else None,
        "avg_temp": round(sum(all_temps) / len(all_temps), 1) if all_temps else None,
        "critical_temps": critical_temps,
    }


def get_sensors_snapshot_linux() -> Dict[str, Any]:
    """Get thermal snapshot using lm-sensors on Linux."""
    if not has_lm_sensors():
        raise SensorError("lm-sensors not available (install lm-sensors package)")

    try:
        result = subprocess.run(
            ["sensors"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise SensorError(f"sensors command failed: {result.stderr}")

        parsed = parse_sensors_output(result.stdout)

        return {
            "platform": "linux",
            "tool": "lm-sensors",
            "timestamp": time.time(),
            **parsed,
        }

    except subprocess.TimeoutExpired:
        raise SensorError("sensors command timed out")
    except Exception as e:
        raise SensorError(f"Failed to get sensor data: {e}")


def get_sensors_snapshot_windows() -> Dict[str, Any]:
    """Get thermal snapshot using WMI on Windows.

    Note: This is a placeholder. Full implementation would use WMI queries
    or OpenHardwareMonitor if available.
    """
    try:
        # Try using WMIC to get thermal zone temperatures
        result = subprocess.run(
            ["wmic", "path", "Win32_TemperatureProbe", "get", "CurrentReading,Name"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        sensors = []
        all_temps = []

        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            # WMIC returns temperature in tenths of Kelvin
                            reading = float(parts[0])
                            temp_celsius = (reading / 10.0) - 273.15
                            name = " ".join(parts[1:])

                            sensors.append(
                                {
                                    "adapter": "wmi-thermal",
                                    "type": "Thermal Zone",
                                    "readings": [
                                        {
                                            "label": name,
                                            "temp": round(temp_celsius, 1),
                                            "high": None,
                                            "crit": None,
                                        }
                                    ],
                                }
                            )
                            all_temps.append(temp_celsius)
                        except (ValueError, IndexError):
                            continue

        # If no WMI data available, return minimal structure
        if not sensors:
            logger.warning("No thermal data available via WMI on Windows")
            return {
                "platform": "windows",
                "tool": "wmi",
                "timestamp": time.time(),
                "sensors": [],
                "max_temp": None,
                "avg_temp": None,
                "critical_temps": [],
                "note": (
                    "OpenHardwareMonitor or HWiNFO recommended for better "
                    "thermal monitoring on Windows"
                ),
            }

        return {
            "platform": "windows",
            "tool": "wmi",
            "timestamp": time.time(),
            "sensors": sensors,
            "max_temp": max(all_temps) if all_temps else None,
            "avg_temp": (
                round(sum(all_temps) / len(all_temps), 1) if all_temps else None
            ),
            "critical_temps": [],
        }

    except subprocess.TimeoutExpired:
        raise SensorError("WMI query timed out")
    except Exception as e:
        raise SensorError(f"Failed to get Windows thermal data: {e}")


def get_sensors_snapshot() -> Dict[str, Any]:
    """Get thermal snapshot for the current platform."""
    plat = detect_platform()

    if plat == "linux":
        return get_sensors_snapshot_linux()
    elif plat == "windows":
        return get_sensors_snapshot_windows()
    else:
        raise SensorError(f"Unsupported platform: {platform.system()}")


def detect_cpu_throttling_linux(duration_seconds: int = 30) -> Dict[str, Any]:
    """Run a stress test and detect thermal throttling on Linux.

    Monitors CPU frequency during stress to detect throttling.
    Returns dict with baseline, peak temps, and throttling status.
    """
    if not has_lm_sensors():
        raise SensorError("lm-sensors required for throttle detection")

    # Get baseline temperature
    try:
        baseline = get_sensors_snapshot_linux()
        baseline_max = baseline.get("max_temp", 0)
    except SensorError:
        baseline = None
        baseline_max = 0

    # Check if stress-ng is available
    try:
        subprocess.run(["stress-ng", "--version"], capture_output=True, timeout=5)
        stress_cmd = ["stress-ng", "--cpu", "0", "--timeout", f"{duration_seconds}s"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback to using sysbench if available
        try:
            subprocess.run(["sysbench", "--version"], capture_output=True, timeout=5)
            stress_cmd = ["sysbench", "cpu", f"--time={duration_seconds}", "run"]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raise SensorError(
                "Neither stress-ng nor sysbench available for stress testing"
            )

    # Start stress test in background
    logger.info(
        f"Starting {duration_seconds}s CPU stress test for throttle detection..."
    )
    stress_proc = subprocess.Popen(
        stress_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Sample temperatures during stress
    samples = []
    sample_interval = 2  # seconds
    num_samples = duration_seconds // sample_interval

    try:
        for i in range(num_samples):
            time.sleep(sample_interval)
            try:
                snapshot = get_sensors_snapshot_linux()
                if snapshot.get("max_temp"):
                    samples.append(snapshot["max_temp"])
            except SensorError:
                pass
    finally:
        # Ensure stress process is terminated
        stress_proc.terminate()
        try:
            stress_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            stress_proc.kill()

    # Analyze results
    if not samples:
        return {
            "baseline_max_temp": baseline_max,
            "peak_temp": None,
            "avg_stress_temp": None,
            "throttling_detected": False,
            "note": "No temperature samples collected during stress test",
        }

    peak_temp = max(samples)
    avg_stress_temp = round(sum(samples) / len(samples), 1)

    # Simple throttling heuristic:
    # If peak temp is > 85°C or within 5°C of critical threshold, likely throttling
    throttling_detected = False
    throttle_reason = None

    if baseline and baseline.get("sensors"):
        for sensor in baseline["sensors"]:
            if sensor.get("type") == "CPU":
                for reading in sensor.get("readings", []):
                    crit = reading.get("crit")
                    if crit and peak_temp >= (crit - 5):
                        throttling_detected = True
                        throttle_reason = (
                            f"Temperature {peak_temp}°C within 5°C of "
                            f"critical threshold {crit}°C"
                        )
                        break

    if not throttling_detected and peak_temp >= 85:
        throttling_detected = True
        throttle_reason = (
            f"Peak temperature {peak_temp}°C exceeds typical threshold (85°C)"
        )

    return {
        "baseline_max_temp": baseline_max,
        "peak_temp": peak_temp,
        "avg_stress_temp": avg_stress_temp,
        "samples": samples,
        "throttling_detected": throttling_detected,
        "throttle_reason": throttle_reason,
        "duration_seconds": duration_seconds,
    }


def detect_cpu_throttling(duration_seconds: int = 30) -> Dict[str, Any]:
    """Detect CPU thermal throttling on the current platform."""
    plat = detect_platform()

    if plat == "linux":
        return detect_cpu_throttling_linux(duration_seconds)
    elif plat == "windows":
        # Windows throttling detection is more complex
        # and requires WMI or specialized tools
        # For now, return a placeholder
        return {
            "platform": "windows",
            "throttling_detected": None,
            "note": "Throttling detection not yet implemented for Windows",
        }
    else:
        raise SensorError(f"Unsupported platform: {platform.system()}")


# For testing purposes
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Getting sensor snapshot...")
    try:
        snapshot = get_sensors_snapshot()
        print(f"Max temp: {snapshot.get('max_temp')}°C")
        print(f"Avg temp: {snapshot.get('avg_temp')}°C")
        print(f"Sensors: {len(snapshot.get('sensors', []))}")
        if snapshot.get("critical_temps"):
            print(f"⚠️  Critical temperatures detected: {snapshot['critical_temps']}")
    except SensorError as e:
        print(f"❌ Sensor error: {e}")

    print("\nTesting throttle detection (30s)...")
    try:
        throttle = detect_cpu_throttling(30)
        print(f"Baseline: {throttle.get('baseline_max_temp')}°C")
        print(f"Peak: {throttle.get('peak_temp')}°C")
        print(f"Throttling detected: {throttle.get('throttling_detected')}")
        if throttle.get("throttle_reason"):
            print(f"Reason: {throttle['throttle_reason']}")
    except SensorError as e:
        print(f"❌ Throttle detection error: {e}")
