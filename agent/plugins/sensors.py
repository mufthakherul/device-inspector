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
from typing import Any, Dict, Optional

logger = logging.getLogger("inspecta.sensors")


class SensorError(Exception):
    """Raised when sensor operations fail."""


def _get_windows_openhardwaremonitor_snapshot() -> Optional[Dict[str, Any]]:
    """Try reading temperatures from OpenHardwareMonitor WMI namespace."""
    ps_script = (
        "$sensors=Get-WmiObject -Namespace root\\OpenHardwareMonitor "
        "-Class Sensor -ErrorAction SilentlyContinue | "
        "Where-Object {$_.SensorType -eq 'Temperature'} | "
        "Select-Object Name,Value,Identifier,SensorType;"
        "$sensors | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    import json

    try:
        payload = json.loads(result.stdout.strip())
    except Exception:
        return None

    rows = payload if isinstance(payload, list) else [payload]
    readings = []
    temps = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            temp = float(row.get("Value"))
        except (TypeError, ValueError):
            continue

        readings.append(
            {
                "label": str(row.get("Name") or "Temperature"),
                "temp": round(temp, 1),
                "high": None,
                "crit": None,
            }
        )
        temps.append(temp)

    if not readings:
        return None

    return {
        "platform": "windows",
        "tool": "openhardwaremonitor",
        "timestamp": time.time(),
        "sensors": [
            {
                "adapter": "openhardwaremonitor-wmi",
                "type": "CPU",
                "readings": readings,
            }
        ],
        "max_temp": max(temps),
        "avg_temp": round(sum(temps) / len(temps), 1),
        "critical_temps": [],
    }


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
    ohm_snapshot = _get_windows_openhardwaremonitor_snapshot()
    if ohm_snapshot is not None:
        return ohm_snapshot

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


def get_cpu_frequency_linux() -> Optional[float]:
    """Get current CPU frequency in MHz from /proc/cpuinfo or cpufreq."""
    try:
        # Try reading from cpufreq first (more accurate)
        freq_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        with open(freq_path, "r") as f:
            # cpufreq returns kHz, convert to MHz
            return float(f.read().strip()) / 1000.0
    except (FileNotFoundError, PermissionError, ValueError):
        pass

    try:
        # Fallback to parsing /proc/cpuinfo
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("cpu MHz"):
                    # Format: "cpu MHz		: 2400.000"
                    freq_str = line.split(":")[1].strip()
                    return float(freq_str)
    except (FileNotFoundError, PermissionError, ValueError, IndexError):
        pass

    return None


def detect_cpu_throttling_linux(
    duration_seconds: int = 30,
) -> Dict[str, Any]:
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

    # Sample temperatures and frequencies during stress
    samples = []
    temp_samples = []
    freq_samples = []
    sample_interval = 2  # seconds
    num_samples = duration_seconds // sample_interval

    # Get baseline frequency
    baseline_freq = get_cpu_frequency_linux()

    try:
        for i in range(num_samples):
            time.sleep(sample_interval)
            try:
                snapshot = get_sensors_snapshot_linux()
                freq = get_cpu_frequency_linux()
                temp = snapshot.get("max_temp")

                if temp:
                    temp_samples.append(temp)

                if freq:
                    freq_samples.append(freq)

                # Create detailed sample with timestamp
                from datetime import datetime, timezone

                sample = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "temp_c": temp,
                    "freq_mhz": freq,
                    "throttled": False,  # Will be determined later
                }

                # Check for frequency drop (simple throttling indicator)
                if baseline_freq and freq and freq < (baseline_freq * 0.85):
                    sample["throttled"] = True

                samples.append(sample)
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
    if not temp_samples:
        return {
            "baseline_max_temp": baseline_max,
            "baseline_freq_mhz": baseline_freq,
            "peak_temp": None,
            "avg_stress_temp": None,
            "min_freq_mhz": None,
            "avg_freq_mhz": None,
            "throttling_detected": False,
            "samples": [],
            "note": "No temperature samples collected during stress test",
        }

    peak_temp = max(temp_samples)
    avg_stress_temp = round(sum(temp_samples) / len(temp_samples), 1)
    min_freq = min(freq_samples) if freq_samples else None
    avg_freq = round(sum(freq_samples) / len(freq_samples), 1) if freq_samples else None

    # Determine throttling based on multiple indicators:
    # 1. High temperature (> 85°C or within 5°C of critical)
    # 2. Significant frequency drop (> 15% from baseline)
    # 3. Any sample marked as throttled
    throttling_detected = False
    throttle_reason = []

    # Check temperature-based throttling
    if baseline and baseline.get("sensors"):
        for sensor in baseline["sensors"]:
            if sensor.get("type") == "CPU":
                for reading in sensor.get("readings", []):
                    crit = reading.get("crit")
                    if crit and peak_temp >= (crit - 5):
                        throttling_detected = True
                        throttle_reason.append(
                            f"Temperature {peak_temp}°C within 5°C of "
                            f"critical threshold {crit}°C"
                        )
                        break

    if not throttling_detected and peak_temp >= 85:
        throttling_detected = True
        throttle_reason.append(
            f"Peak temperature {peak_temp}°C exceeds typical threshold (85°C)"
        )

    # Check frequency-based throttling
    if baseline_freq and min_freq:
        freq_drop_pct = ((baseline_freq - min_freq) / baseline_freq) * 100
        if freq_drop_pct > 15:
            throttling_detected = True
            throttle_reason.append(
                f"CPU frequency dropped {freq_drop_pct:.1f}% "
                f"({baseline_freq:.0f} → {min_freq:.0f} MHz)"
            )

    # Check if any samples detected throttling
    throttled_samples = [s for s in samples if s.get("throttled")]
    if throttled_samples:
        throttling_detected = True
        if not any("frequency" in r for r in throttle_reason):
            throttle_reason.append(
                f"Throttling detected in "
                f"{len(throttled_samples)}/{len(samples)} samples"
            )

    return {
        "baseline_max_temp": baseline_max,
        "baseline_freq_mhz": baseline_freq,
        "peak_temp": peak_temp,
        "avg_stress_temp": avg_stress_temp,
        "min_freq_mhz": min_freq,
        "avg_freq_mhz": avg_freq,
        "samples": samples,
        "throttling_detected": throttling_detected,
        "throttle_reason": "; ".join(throttle_reason) if throttle_reason else None,
        "duration_seconds": duration_seconds,
        "num_samples": len(samples),
    }


def generate_thermal_stress_csv(samples: list) -> str:
    """Generate CSV content from thermal stress samples.

    Args:
        samples: List of sample dicts with timestamp, temp_c, freq_mhz, throttled

    Returns:
        CSV content as string
    """
    lines = ["timestamp,temp_c,freq_mhz,throttled"]

    for sample in samples:
        timestamp = sample.get("timestamp", "")
        temp = sample.get("temp_c", "")
        freq = sample.get("freq_mhz", "")
        throttled = str(sample.get("throttled", False)).lower()

        lines.append(f"{timestamp},{temp},{freq},{throttled}")

    return "\n".join(lines) + "\n"


def classify_thermal_severity(
    peak_temp: Optional[float],
    throttling_detected: Optional[bool],
    throttle_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Classify thermal risk severity from stress-test outcomes.

    Severity tiers:
    - low: no throttling and peak < 80°C
    - moderate: no throttling but elevated peak temperature (80-89.9°C)
    - high: throttling detected or peak temperature 90-94.9°C
    - critical: throttling detected with peak >= 95°C
    """
    peak = float(peak_temp) if peak_temp is not None else None
    throttled = bool(throttling_detected) if throttling_detected is not None else False

    severity = "unknown"
    score_penalty = 0

    if peak is None and throttling_detected is None:
        severity = "unknown"
    elif throttled and peak is not None and peak >= 95:
        severity = "critical"
        score_penalty = 35
    elif throttled or (peak is not None and peak >= 90):
        severity = "high"
        score_penalty = 22
    elif peak is not None and peak >= 80:
        severity = "moderate"
        score_penalty = 10
    else:
        severity = "low"
        score_penalty = 0

    return {
        "severity": severity,
        "score_penalty": score_penalty,
        "peak_temp": peak_temp,
        "throttling_detected": throttling_detected,
        "throttle_reason": throttle_reason,
    }


def _collect_windows_perf_sample() -> Dict[str, Any]:
    """Collect a single Windows CPU/thermal sample via PowerShell."""
    ps_script = (
        "$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1;"
        "$tz=Get-CimInstance MSAcpi_ThermalZoneTemperature "
        "-ErrorAction SilentlyContinue "
        "| Select-Object -First 1;"
        "$temp=$null;"
        "if($tz -and $tz.CurrentTemperature){"
        "$temp=[math]::Round(($tz.CurrentTemperature/10)-273.15,1)"
        "};"
        "$ohm=Get-WmiObject -Namespace root\\OpenHardwareMonitor "
        "-Class Sensor -ErrorAction SilentlyContinue | "
        "Where-Object {$_.SensorType -eq 'Temperature'} | "
        "Select-Object -First 1;"
        "if($ohm -and $ohm.Value){$temp=[double]$ohm.Value};"
        "$obj=[ordered]@{"
        "freq_mhz=$cpu.CurrentClockSpeed;"
        "max_mhz=$cpu.MaxClockSpeed;"
        "temp_c=$temp"
        "};"
        "$obj | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SensorError("PowerShell not found for Windows thermal probe") from exc
    except subprocess.TimeoutExpired as exc:
        raise SensorError("Windows thermal probe timed out") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise SensorError(f"Windows thermal probe failed: {stderr}")

    import json

    try:
        payload = json.loads(result.stdout.strip() or "{}")
    except Exception as exc:
        raise SensorError(
            f"Could not parse Windows thermal probe output: {exc}"
        ) from exc

    return payload


def detect_cpu_throttling_windows(duration_seconds: int = 30) -> Dict[str, Any]:
    """Detect Windows CPU throttling using sampled current clock speed."""
    sample_interval = 2
    sample_count = max(1, duration_seconds // sample_interval)

    baseline = _collect_windows_perf_sample()
    baseline_freq = baseline.get("freq_mhz")
    samples = []
    temps = []
    freqs = []

    for _ in range(sample_count):
        time.sleep(sample_interval)
        sample = _collect_windows_perf_sample()
        freq = sample.get("freq_mhz")
        temp = sample.get("temp_c")

        throttled = False
        if baseline_freq and freq and float(freq) < (float(baseline_freq) * 0.85):
            throttled = True

        samples.append(
            {
                "timestamp": time.time(),
                "temp_c": temp,
                "freq_mhz": freq,
                "throttled": throttled,
            }
        )

        if temp is not None:
            temps.append(float(temp))
        if freq is not None:
            freqs.append(float(freq))

    min_freq = min(freqs) if freqs else None
    avg_freq = round(sum(freqs) / len(freqs), 1) if freqs else None
    peak_temp = max(temps) if temps else None
    avg_temp = round(sum(temps) / len(temps), 1) if temps else None

    throttled_samples = [s for s in samples if s.get("throttled")]
    throttling_detected = len(throttled_samples) > 0

    reason = None
    if throttling_detected and baseline_freq and min_freq:
        drop_pct = (
            (float(baseline_freq) - float(min_freq)) / float(baseline_freq)
        ) * 100
        reason = (
            f"CPU frequency dropped {drop_pct:.1f}% ({baseline_freq} -> {min_freq} MHz)"
        )

    return {
        "platform": "windows",
        "baseline_max_temp": baseline.get("temp_c"),
        "baseline_freq_mhz": baseline_freq,
        "peak_temp": peak_temp,
        "avg_stress_temp": avg_temp,
        "min_freq_mhz": min_freq,
        "avg_freq_mhz": avg_freq,
        "samples": samples,
        "throttling_detected": throttling_detected,
        "throttle_reason": reason,
        "duration_seconds": duration_seconds,
        "num_samples": len(samples),
    }


def detect_cpu_throttling(duration_seconds: int = 30) -> Dict[str, Any]:
    """Detect CPU thermal throttling on the current platform."""
    plat = detect_platform()

    if plat == "linux":
        return detect_cpu_throttling_linux(duration_seconds)
    elif plat == "windows":
        return detect_cpu_throttling_windows(duration_seconds)
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
