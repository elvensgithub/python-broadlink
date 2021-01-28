"""Support for universal remotes."""
import enum
import struct

from .device import device
from .exceptions import check_error


@enum.unique
class Features(enum.IntFlag):
    """Flag supported features."""
    LEARN_IR_CODE = 1
    SEND_IR_CODE = 2
    LEARN_RF_CODE = 4
    SEND_RF_CODE = 8
    CHECK_TEMPERATURE = 16
    CHECK_HUMIDITY = 32


class rmmini(device):
    """Controls a Broadlink RM mini 3."""

    TYPE = "RMMINI"

    def _send(self, command: int, data: bytes = b'') -> bytes:
        """Send a packet to the device."""
        packet = struct.pack("<I", command) + data
        resp = self.send_packet(0x6A, packet)
        check_error(resp[0x22:0x24])
        payload = self.decrypt(resp[0x38:])
        return payload[0x4:]

    def fetch_data(self) -> dict:
        """Fetch data."""
        resp = self._send(0x1)
        return {
            "name": resp[0x48:].split(b"\x00")[0].decode(),
            "is_locked": bool(resp[0x87]),
        }

    def send_data(self, data: bytes) -> None:
        """Send a code to the device."""
        self._send(0x2, data)

    def enter_learning(self) -> None:
        """Enter infrared learning mode."""
        self._send(0x3)

    def check_data(self) -> bytes:
        """Return the last captured code."""
        return self._send(0x4)

    @property
    def supported_features(self) -> Features:
        """Flag supported features."""
        ft = Features
        return ft.LEARN_IR_CODE | ft.SEND_IR_CODE


class rmpro(rmmini):
    """Controls a Broadlink RM pro."""

    TYPE = "RMPRO"

    def fetch_data(self) -> dict:
        """Fetch data."""
        resp = self._send(0x1)
        temperature = struct.unpack("<bb", resp[:0x2])
        return {
            "temperature": temperature[0x0] + temperature[0x1] / 10.0,
            "name": resp[0x48:].split(b"\x00")[0].decode(),
            "is_locked": bool(resp[0x87]),
        }

    def sweep_frequency(self) -> None:
        """Sweep frequency."""
        self._send(0x19)

    def check_frequency(self) -> bool:
        """Return True if the frequency was identified successfully."""
        resp = self._send(0x1A)
        return resp[0] == 1

    def find_rf_packet(self) -> None:
        """Enter radiofrequency learning mode."""
        self._send(0x1B)

    def cancel_sweep_frequency(self) -> None:
        """Cancel sweep frequency."""
        self._send(0x1E)

    def check_sensors(self) -> dict:
        """Return the state of the sensors."""
        resp = self._send(0x1)
        temperature = struct.unpack("<bb", resp[:0x2])
        return {"temperature": temperature[0x0] + temperature[0x1] / 10.0}

    def check_temperature(self) -> float:
        """Return the temperature."""
        return self.check_sensors()["temperature"]

    @property
    def supported_features(self) -> Features:
        """Flag supported features."""
        ft = Features
        return (
            ft.LEARN_IR_CODE | ft.SEND_IR_CODE |
            ft.LEARN_RF_CODE | ft.SEND_RF_CODE |
            ft.CHECK_TEMPERATURE
        )


class rmminib(rmmini):
    """Controls a Broadlink RM mini 3 (new firmware)."""

    TYPE = "RMMINIB"

    def _send(self, command: int, data: bytes = b'') -> bytes:
        """Send a packet to the device."""
        packet = struct.pack("<HI", len(data) + 4, command) + data
        resp = self.send_packet(0x6A, packet)
        check_error(resp[0x22:0x24])
        payload = self.decrypt(resp[0x38:])
        p_len = struct.unpack("<H", payload[:0x2])[0]
        return payload[0x6:p_len+2]


class rm4mini(rmminib):
    """Controls a Broadlink RM4 mini."""
    
    TYPE = "RM4MINI"

    def check_sensors(self) -> dict:
        """Return the state of the sensors."""
        resp = self._send(0x24)
        temperature = struct.unpack("<bb", resp[:0x2])
        return {
            "temperature": temperature[0x0] + temperature[0x1] / 100.0,
            "humidity": resp[0x2] + resp[0x3] / 100.0
        }

    def check_temperature(self) -> float:
        """Return the temperature."""
        return self.check_sensors()["temperature"]

    def check_humidity(self) -> float:
        """Return the humidity."""
        return self.check_sensors()["humidity"]

    @property
    def supported_features(self) -> Features:
        """Flag supported features."""
        ft = Features
        return (
            ft.LEARN_IR_CODE | ft.SEND_IR_CODE |
            ft.CHECK_TEMPERATURE | ft.CHECK_HUMIDITY
        )


class rm4pro(rm4mini, rmpro):
    """Controls a Broadlink RM4 pro."""

    TYPE = "RM4PRO"

    @property
    def supported_features(self) -> Features:
        """Flag supported features."""
        ft = Features
        return (
            ft.LEARN_IR_CODE | ft.SEND_IR_CODE |
            ft.LEARN_RF_CODE | ft.SEND_RF_CODE |
            ft.CHECK_TEMPERATURE | ft.CHECK_HUMIDITY
        )


class rm(rmpro):
    """For backwards compatibility."""

    TYPE = "RM2"


class rm4(rm4pro):
    """For backwards compatibility."""

    TYPE = "RM4"
