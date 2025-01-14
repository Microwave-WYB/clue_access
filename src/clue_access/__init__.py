from collections.abc import Callable

from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select

from clue_access.schemas import (
    BLEUUID,
    AndroidApp,
    AndroidAppUUID,
    BLEDevice,
    BLEDeviceUUID,
    QTColor,
    QTDevice,
    QTMode,
)


def main() -> None:
    # try connecting to the database
    try:
        run_in_session(lambda session: session.exec(select(1)).first())
        print("Successfully connected to the database")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")


def get_engine() -> Engine:
    return create_engine("postgresql://postgres:infra_wireless_scanning@localhost:5432/cluedb")


def run_in_session[T](func: Callable[[Session], T]) -> T:
    with Session(get_engine()) as session:
        return func(session)


__all__ = [
    "get_engine",
    "run_in_session",
    "BLEUUID",
    "AndroidApp",
    "AndroidAppUUID",
    "BLEDevice",
    "BLEDeviceUUID",
    "QTColor",
    "QTDevice",
    "QTMode",
]
