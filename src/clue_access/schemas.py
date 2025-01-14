"""
This module contains all database schema definitions for the Clue server.

Development Notes:
- This module only contains the schema definitions.
- Do not include any database operations in this module.
"""

import base64
import struct
from collections.abc import Iterable
from datetime import datetime
from enum import IntEnum, StrEnum, auto
from typing import Any, Self, override
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from pydantic import model_serializer
from shapely import Point
from sqlalchemy import JSON, Column, Enum, LargeBinary
from sqlmodel import Field, SQLModel


class BLEDeviceBase(SQLModel):
    """Schema for creating BLE devices"""

    mac: str = Field(min_length=17, max_length=17)
    rssi: int = Field(...)
    time: datetime = Field(...)
    lat: float = Field(...)
    long: float = Field(...)
    accuracy: float = Field(...)
    blob_name: str = Field(...)
    speed: float | None = Field(default=None)
    name: str | None = Field(default=None)
    local_name: str | None = Field(default=None)
    manufacturer_id: int | None = Field(default=None)


class BLEDeviceCreate(BLEDeviceBase):
    """Schema for creating BLE devices"""

    uuids: str | None = Field(default=None)
    raw_data: str | None = Field(default=None)

    def create(self) -> tuple[set["BLEUUID"], "BLEDevice"]:
        """Create a BLEDevice instance from raw data"""
        uuid_list = self.uuids.split(",") if self.uuids else []
        ble_uuids = set(BLEUUID(full_uuid=UUID(uuid)) for uuid in uuid_list)
        ble_device = BLEDevice.from_create(self)
        return ble_uuids, ble_device


class BLEDevice(BLEDeviceBase, table=True):
    """Schema for BLE devices"""

    __tablename__: str = "ble_device"  # type: ignore

    # Data not included in the raw advertisement data
    id: int | None = Field(default=None, primary_key=True)
    coordinates: Any = Field(
        default=None,
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326),
        ),
    )
    raw_data: bytes | None = Field(default=None, sa_column=Column(LargeBinary))

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add the missing coordinates field"""
        if self.lat and self.long:
            self.coordinates = self.coordinates or from_shape(Point(self.long, self.lat), srid=4326)

    @classmethod
    def from_create(cls: type[Self], raw_device: BLEDeviceCreate) -> Self:
        """Create a BLEDevice instance from raw data"""
        raw_data_bytes = base64.b64decode(raw_device.raw_data) if raw_device.raw_data else None
        return cls(
            mac=raw_device.mac,
            rssi=raw_device.rssi,
            time=raw_device.time,
            lat=raw_device.lat,
            long=raw_device.long,
            accuracy=raw_device.accuracy,
            blob_name=raw_device.blob_name,
            speed=raw_device.speed,
            name=raw_device.name,
            local_name=raw_device.local_name,
            manufacturer_id=raw_device.manufacturer_id,
            raw_data=raw_data_bytes,
        )

    @property
    def raw_data_b64(self) -> str | None:
        """Return the raw data as a base64 encoded string"""
        return base64.b64encode(self.raw_data).decode() if self.raw_data else None

    @model_serializer
    def serialize(self):
        """Serialize the BLE device data"""
        return {
            "id": self.id,
            "mac": self.mac,
            "rssi": self.rssi,
            "time": self.time,
            "lat": self.lat,
            "long": self.long,
            "accuracy": self.accuracy,
            "blob_name": self.blob_name,
            "speed": self.speed,
            "name": self.name,
            "local_name": self.local_name,
            "manufacturer_id": self.manufacturer_id,
            "raw_data": self.raw_data_b64,
        }


class AndroidApp(SQLModel, table=True):
    """Schema for Android apps"""

    __tablename__: str = "android_app"  # type: ignore

    app_id: str = Field(primary_key=True)
    name: str = Field(...)
    description: str | None = Field(default=None)


class BLEDeviceUUID(SQLModel, table=True):
    """Association table for BLEDevice and BLEUUID"""

    __tablename__: str = "ble_device_uuid"  # type: ignore

    ble_device_id: int = Field(foreign_key="ble_device.id", primary_key=True)
    uuid: UUID = Field(foreign_key="ble_uuid.full_uuid", primary_key=True)


class AndroidAppUUID(SQLModel, table=True):
    """Association table for AndroidApp and BLEUUID"""

    __tablename__: str = "android_app_uuid"  # type: ignore

    app_id: str = Field(foreign_key="android_app.app_id", primary_key=True)
    uuid: UUID = Field(foreign_key="ble_uuid.full_uuid", primary_key=True)


class BLEUUID(SQLModel, table=True):
    """
    Schema for all BLE UUIDs discovered. This includes:
        Bluetooth SIG assigned UUIDs
        Scanned UUIDs from BLE devices
        Extracted UUIDs from Android apps
    """

    __tablename__: str = "ble_uuid"  # type: ignore

    full_uuid: UUID = Field(primary_key=True)
    short_uuid: int | None = Field(default=None)
    name: str | None = Field(default=None)

    def __hash__(self) -> int:
        return hash(self.full_uuid)


class SyncState(StrEnum):
    """Sync states"""

    PENDING = auto()  # Found in the GCS bucket but not yet processed
    QUEUED = auto()  # Enqueued for processing
    SYNCED = auto()  # Successfully processed
    FAILED = auto()  # Failed to process


class SyncStatus(SQLModel, table=True):
    """Schema for syncing status"""

    __tablename__: str = "sync_status"  # type: ignore

    blob_name: str = Field(primary_key=True)
    state: SyncState = Field(default=SyncState.PENDING)
    process_time: datetime | None = Field(default=None)
    message: str | None = Field(default=None)


class NoSQLData(SQLModel, table=True):
    """Schema for NoSQL data"""

    __tablename__: str = "nosql_data"  # type: ignore

    key: str = Field(primary_key=True)
    value: dict = Field(sa_column=Column(JSON))


class QTMode(IntEnum):
    """Mode of the device"""

    UNKNOWN = 0
    INSTALLER = 1
    DEALER = 2
    USER = 3
    NOSALE = 4
    BCA = 5
    VALET = 6
    BOOTLOAD = 7
    UNCONFIGURED = 8


class QTColor(IntEnum):
    """Color of the device"""

    ORANGE = 1
    BLUE = 2
    LIGHTGREEN = 3
    RED = 4
    MEDIUMPURPLE = 5
    LIGHTGREY = 6


class QTDevice(SQLModel, table=True):
    __tablename__: str = "qt_device"  # type: ignore

    ble_device_id: int = Field(foreign_key="ble_device.id", primary_key=True)
    name: str
    mac: str
    color: QTColor = Field(sa_column=Column(Enum(QTColor)))
    mode: QTMode = Field(sa_column=Column(Enum(QTMode)))
    armed: bool
    snowmode: bool
    vbat: float

    @classmethod
    def from_ble_device(cls: type["QTDevice"], ble_device: BLEDevice) -> "QTDevice":
        assert ble_device.name is not None, "QTDevice requires a name"
        assert ble_device.raw_data is not None, "QTDevice requires raw data"
        assert ble_device.id is not None, "QTDevice requires a BLE device ID"

        def iter_fields(data: bytes) -> Iterable[tuple[int, bytes]]:
            offset = 0
            while offset < len(data):
                length = data[offset]
                if length == 0:
                    return
                # Get type from the byte after length
                type_id = data[offset + 1]
                # Get value excluding length and type bytes
                value = data[offset + 2 : offset + length + 1]
                yield type_id, value
                offset += length + 1

        fields: dict[int, bytes] = {}
        for field_type, value in iter_fields(ble_device.raw_data):
            fields[field_type] = value

        manufacturer_data = fields.get(255, b"")
        name = fields.get(9, b"").decode("utf-8")
        mac = ble_device.mac
        unpacked = struct.unpack("<BBBBBB", manufacturer_data)
        color = QTColor(((unpacked[0] & 0xC0) >> 6) | ((unpacked[1] & 0xC0) >> 4))
        mode = QTMode(((unpacked[2] & 0xC0) >> 6) | ((unpacked[3] & 0x40) >> 4))
        armed = bool(unpacked[3] & 0x80)
        snowmode = bool(unpacked[4] & 0x40)
        vbat = unpacked[5] * 60 / 1000
        return cls(
            name=name,
            mac=mac,
            color=color,
            mode=mode,
            armed=armed,
            snowmode=snowmode,
            vbat=vbat,
            ble_device_id=ble_device.id,
        )
