# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Unit tests for sensors.py"""

from unittest.mock import MagicMock, patch

import pytest

from agent.plugins import sensors

SAMPLE_SENSORS_OUTPUT = """\
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

SAMPLE_SENSORS_CRITICAL = """\
coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +102.0°C  (high = +100.0°C, crit = +100.0°C)
Core 0:        +98.0°C  (high = +100.0°C, crit = +100.0°C)
"""


class TestParseSensorsOutput:
    """Test parse_sensors_output function."""

    def test_parse_normal_output(self):
        """Test parsing normal sensor output."""
        result = sensors.parse_sensors_output(SAMPLE_SENSORS_OUTPUT)

        assert "sensors" in result
        assert len(result["sensors"]) == 2

        # Check CPU sensor
        cpu_sensor = result["sensors"][0]
        assert cpu_sensor["adapter"] == "coretemp-isa-0000"
        assert cpu_sensor["type"] == "CPU"
        assert len(cpu_sensor["readings"]) == 5

        # Check first reading
        pkg_reading = cpu_sensor["readings"][0]
        assert pkg_reading["label"] == "Package id 0"
        assert pkg_reading["temp"] == 52.0
        assert pkg_reading["high"] == 100.0
        assert pkg_reading["crit"] == 100.0

        # Check NVMe sensor
        nvme_sensor = result["sensors"][1]
        assert nvme_sensor["adapter"] == "nvme-pci-0100"
        assert nvme_sensor["type"] == "NVMe"
        assert len(nvme_sensor["readings"]) == 3

        # Check aggregates
        assert result["max_temp"] == 52.0
        assert result["avg_temp"] > 40  # Should be around 46-47
        assert result["critical_temps"] == []

    def test_parse_critical_temps(self):
        """Test parsing output with critical temperatures."""
        result = sensors.parse_sensors_output(SAMPLE_SENSORS_CRITICAL)

        assert result["max_temp"] == 102.0
        assert len(result["critical_temps"]) > 0

        crit = result["critical_temps"][0]
        assert crit["label"] == "Package id 0"
        assert crit["temp"] == 102.0
        assert crit["threshold"] == 100.0

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = sensors.parse_sensors_output("")

        assert result["sensors"] == []
        assert result["max_temp"] is None
        assert result["avg_temp"] is None
        assert result["critical_temps"] == []


class TestHasLmSensors:
    """Test has_lm_sensors function."""

    @patch("subprocess.run")
    def test_sensors_available(self, mock_run):
        """Test when lm-sensors is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert sensors.has_lm_sensors() is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_sensors_not_found(self, mock_run):
        """Test when lm-sensors is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert sensors.has_lm_sensors() is False

    @patch("subprocess.run")
    def test_sensors_timeout(self, mock_run):
        """Test when sensors command times out."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("sensors", 5)
        assert sensors.has_lm_sensors() is False


class TestGetSensorsSnapshotLinux:
    """Test get_sensors_snapshot_linux function."""

    @patch("agent.plugins.sensors.has_lm_sensors")
    def test_sensors_not_available(self, mock_has):
        """Test error when sensors not available."""
        mock_has.return_value = False

        with pytest.raises(sensors.SensorError, match="not available"):
            sensors.get_sensors_snapshot_linux()

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("subprocess.run")
    def test_successful_snapshot(self, mock_run, mock_has):
        """Test successful sensor snapshot."""
        mock_has.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=SAMPLE_SENSORS_OUTPUT,
        )

        result = sensors.get_sensors_snapshot_linux()

        assert result["platform"] == "linux"
        assert result["tool"] == "lm-sensors"
        assert "timestamp" in result
        assert result["max_temp"] == 52.0
        assert len(result["sensors"]) == 2

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("subprocess.run")
    def test_sensors_command_fails(self, mock_run, mock_has):
        """Test error when sensors command fails."""
        mock_has.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Command failed",
        )

        with pytest.raises(sensors.SensorError, match="failed"):
            sensors.get_sensors_snapshot_linux()

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("subprocess.run")
    def test_sensors_timeout(self, mock_run, mock_has):
        """Test timeout during sensor read."""
        from subprocess import TimeoutExpired

        mock_has.return_value = True
        mock_run.side_effect = TimeoutExpired("sensors", 10)

        with pytest.raises(sensors.SensorError, match="timed out"):
            sensors.get_sensors_snapshot_linux()


class TestGetSensorsSnapshotWindows:
    """Test get_sensors_snapshot_windows function."""

    @patch("subprocess.run")
    def test_wmi_no_data(self, mock_run):
        """Test Windows when no thermal data available."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
        )

        result = sensors.get_sensors_snapshot_windows()

        assert result["platform"] == "windows"
        assert result["tool"] == "wmi"
        assert result["sensors"] == []
        assert "OpenHardwareMonitor" in result.get("note", "")

    @patch("subprocess.run")
    def test_wmi_timeout(self, mock_run):
        """Test WMI timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("wmic", 10)

        with pytest.raises(sensors.SensorError, match="timed out"):
            sensors.get_sensors_snapshot_windows()


class TestGetSensorsSnapshot:
    """Test get_sensors_snapshot cross-platform function."""

    @patch("agent.plugins.sensors.detect_platform")
    @patch("agent.plugins.sensors.get_sensors_snapshot_linux")
    def test_linux_platform(self, mock_linux, mock_platform):
        """Test snapshot on Linux."""
        mock_platform.return_value = "linux"
        mock_linux.return_value = {"platform": "linux"}

        result = sensors.get_sensors_snapshot()
        assert result["platform"] == "linux"
        mock_linux.assert_called_once()

    @patch("agent.plugins.sensors.detect_platform")
    @patch("agent.plugins.sensors.get_sensors_snapshot_windows")
    def test_windows_platform(self, mock_windows, mock_platform):
        """Test snapshot on Windows."""
        mock_platform.return_value = "windows"
        mock_windows.return_value = {"platform": "windows"}

        result = sensors.get_sensors_snapshot()
        assert result["platform"] == "windows"
        mock_windows.assert_called_once()

    @patch("agent.plugins.sensors.detect_platform")
    def test_unsupported_platform(self, mock_platform):
        """Test error on unsupported platform."""
        mock_platform.return_value = "unknown"

        with pytest.raises(sensors.SensorError, match="Unsupported platform"):
            sensors.get_sensors_snapshot()


class TestDetectCpuThrottling:
    """Test detect_cpu_throttling_linux function."""

    @patch("agent.plugins.sensors.has_lm_sensors")
    def test_no_sensors(self, mock_has):
        """Test error when sensors not available."""
        mock_has.return_value = False

        with pytest.raises(sensors.SensorError, match="lm-sensors required"):
            sensors.detect_cpu_throttling_linux(duration_seconds=5)

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("subprocess.run")
    def test_no_stress_tool(self, mock_run, mock_has):
        """Test error when neither stress-ng nor sysbench available."""
        mock_has.return_value = True
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(sensors.SensorError, match="Neither stress-ng nor sysbench"):
            sensors.detect_cpu_throttling_linux(duration_seconds=5)

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("agent.plugins.sensors.get_sensors_snapshot_linux")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_throttling_detected(
        self, mock_sleep, mock_popen, mock_run, mock_snapshot, mock_has
    ):
        """Test throttling detection."""
        mock_has.return_value = True

        # Mock baseline snapshot
        mock_snapshot.side_effect = [
            {
                "max_temp": 45.0,
                "sensors": [
                    {
                        "type": "CPU",
                        "readings": [
                            {
                                "label": "Package id 0",
                                "temp": 45.0,
                                "crit": 100.0,
                            }
                        ],
                    }
                ],
            },
            {"max_temp": 96.0},  # Sample 1 - high temp
            {"max_temp": 98.0},  # Sample 2 - higher temp
        ]

        # Mock stress-ng availability
        mock_run.return_value = MagicMock(returncode=0)

        # Mock stress process
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        result = sensors.detect_cpu_throttling_linux(duration_seconds=4)

        assert result["baseline_max_temp"] == 45.0
        assert result["peak_temp"] == 98.0
        assert result["throttling_detected"] is True
        assert "critical threshold" in result.get("throttle_reason", "")

        # Verify stress process was terminated
        mock_proc.terminate.assert_called_once()

    @patch("agent.plugins.sensors.has_lm_sensors")
    @patch("agent.plugins.sensors.get_sensors_snapshot_linux")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_no_throttling(
        self, mock_sleep, mock_popen, mock_run, mock_snapshot, mock_has
    ):
        """Test when no throttling detected."""
        mock_has.return_value = True

        # Mock baseline snapshot and samples with normal temps
        mock_snapshot.side_effect = [
            {"max_temp": 45.0, "sensors": []},
            {"max_temp": 55.0},  # Sample 1
            {"max_temp": 58.0},  # Sample 2
        ]

        mock_run.return_value = MagicMock(returncode=0)
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        result = sensors.detect_cpu_throttling_linux(duration_seconds=4)

        assert result["peak_temp"] == 58.0
        assert result["throttling_detected"] is False


class TestDetectPlatform:
    """Test detect_platform function."""

    @patch("platform.system")
    def test_linux(self, mock_system):
        """Test Linux platform detection."""
        mock_system.return_value = "Linux"
        assert sensors.detect_platform() == "linux"

    @patch("platform.system")
    def test_windows(self, mock_system):
        """Test Windows platform detection."""
        mock_system.return_value = "Windows"
        assert sensors.detect_platform() == "windows"

    @patch("platform.system")
    def test_unknown(self, mock_system):
        """Test unknown platform detection."""
        mock_system.return_value = "Darwin"
        assert sensors.detect_platform() == "unknown"


class TestThermalSeverityClassification:
    """Test Sprint 2 thermal severity tier classification."""

    def test_low_severity(self):
        result = sensors.classify_thermal_severity(
            peak_temp=72.0, throttling_detected=False
        )
        assert result["severity"] == "low"
        assert result["score_penalty"] == 0

    def test_moderate_severity(self):
        result = sensors.classify_thermal_severity(
            peak_temp=84.0, throttling_detected=False
        )
        assert result["severity"] == "moderate"
        assert result["score_penalty"] == 10

    def test_high_severity(self):
        result = sensors.classify_thermal_severity(
            peak_temp=91.0, throttling_detected=False
        )
        assert result["severity"] == "high"
        assert result["score_penalty"] == 22

    def test_critical_severity(self):
        result = sensors.classify_thermal_severity(
            peak_temp=97.0, throttling_detected=True
        )
        assert result["severity"] == "critical"
        assert result["score_penalty"] == 35
