# yapf: disable
import json
from typing import Any, Self

import log21
from pydantic import BaseModel, validator

# yapf: enable


class BaseDataModel(BaseModel):
    """A base model for data models.

    :param data: The data to be stored in the model.
    """

    data: Any = {}


class BaseAPIResponse(BaseDataModel):
    """A base model for an API response.

    :param success: A boolean indicating whether the request was successful.
    :param message: A message to be displayed to the user.
    :param error: An error message to be displayed to the user.
    :param data: The data to be returned in the response.
    """

    success: bool
    message: str = ""
    error: str = ""


class Coordinate(BaseModel):
    """A model for a coordinate point."""

    lat: float
    lng: float

    @validator("lat")
    def validate_lat(cls, value):
        """Validates the latitude value."""
        if not (-90 <= value <= 90):  # pylint: disable=superfluous-parens
            raise ValueError("Latitude must be between -90 and 90.")
        return value

    @validator("lng")
    def validate_lng(cls, value):
        """Validates the longitude value."""
        if not (-180 <= value <= 180):  # pylint: disable=superfluous-parens
            raise ValueError("Longitude must be between -180 and 180.")
        return value

    @classmethod
    def from_str(cls, value: str, raise_error: bool = False):
        """Creates a Coordinate object from a string.

        :param value: A string containing the latitude and longitude values.
        :return: A Coordinate object.
        """
        if value == "":
            return None
        # Check if the string is JSON
        try:
            data = json.loads(value)
            return cls(**data)
        except json.JSONDecodeError:
            # If it's not JSON, assume it's a 'lat, lng' string
            try:
                lat, lng = map(float, value.split(","))
                return cls(lat=lat, lng=lng)
            except ValueError:
                if raise_error:
                    raise ValueError(f"Invalid coordinate input: {value}")
                log21.warn("Invalid coordinate input: %s", args=(value, ))
                return None

    @classmethod
    def validate_coordinate(cls, value):
        """Validates the coordinate value."""
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            return cls.from_str(value)
        elif isinstance(value, dict):
            return cls(**value)
        raise ValueError(f"Invalid coordinate input: {value}")

    def to_list(self, latlng: bool = False) -> list[float]:
        """Converts the coordinate to a list.

        :param latlng: If True, the list will be in the format [lat, lng]. Otherwise, it
            will be in the format [lng, lat].
        :return: A list containing the latitude and longitude values.
        """
        if latlng:
            return [self.lat, self.lng]
        return [self.lng, self.lat]

    @classmethod
    def from_list(cls, value: list[float], latlng: bool = False) -> Self:
        """Creates a Coordinate object from a list.

        :param value: A list containing the latitude and longitude values.
        :param latlng: If True, the list is in the format [lat, lng]. Otherwise, it's in
            the format [lng, lat].
        :return: A Coordinate object.
        """
        if latlng:
            return cls(lat=value[0], lng=value[1])
        return cls(lat=value[1], lng=value[0])

    @property
    def latlng(self) -> str:
        """Returns the latitude and longitude values as a string."""
        return f"{self.lat}, {self.lng}"

    @property
    def lnglat(self) -> str:
        """Returns the longitude and latitude values as a string."""
        return f"{self.lng}, {self.lat}"

    def as_dict(self) -> dict[str, float]:
        """Returns the latitude and longitude values as a dictionary."""
        return {"lat": self.lat, "lng": self.lng}

    def __hash__(self) -> int:
        """Returns the hash of the coordinate."""
        return hash((self.lat, self.lng))
