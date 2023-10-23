from ipyautoui.basemodel import BaseModel
from pydantic import Field, conint
from datetime import datetime, date
import pathlib
import typing as ty
from pydantic_extra_types.color import Color


class ComplexSerialisation(BaseModel):
    """all of these types need to be serialised to json and parsed back to objects upon reading..."""

    file_chooser: pathlib.Path = pathlib.Path(".")
    date_picker_string: ty.Optional[
        date
    ] = (
        date.today()
    )  # TODO: serialisation / parsing round trip not working... # TODO: fix this!
    naive_datetime_picker_string: ty.Optional[
        datetime
    ] = datetime.now()  # TODO: update with ipywidgets-v8 # TODO: fix this!
    color_picker_ipywidgets: Color = "#f5f595"
    markdown_widget: str = Field(json_schema_extra=dict(format="markdown"))
    any_of: ty.Union[conint(ge=0, le=3), str] = Field(
        description="anyof widget. once selected the type is fixed."
    )