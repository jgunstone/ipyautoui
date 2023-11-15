# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""file upload wrapper"""
# %load_ext lab_black
# %run ../_dev_maplocal_params.py

# +
import ipywidgets as w
from markdown import markdown
from IPython.display import display, clear_output
from pydantic import BaseModel, field_validator, Field, ValidationInfo
import pathlib
import typing as ty
import stringcase
from datetime import datetime
import traitlets as tr
import json
import logging
from ipyautoui.constants import DELETE_BUTTON_KWARGS
from ipyautoui._utils import getuser
from ipyautoui.autodisplay import DisplayObject, DisplayPath, ORDER_DEFAULT
from ipyautoui.custom.iterable import Array
from ipyautoui.autodisplay_renderers import render_file
from ipyautoui.env import Env
from ipyautoui.constants import DELETE_BUTTON_KWARGS
from ipyautoui.autodisplay import ORDER_NOTPATH

IPYAUTOUI_ROOTDIR = Env().IPYAUTOUI_ROOTDIR
logger = logging.getLogger(__name__)


# -


class File(BaseModel):
    name: str
    fdir: pathlib.Path = pathlib.Path(".")
    path: pathlib.Path = Field(pathlib.Path("overide.me"), validate_default=True)

    @field_validator("path")
    @classmethod
    def _path(cls, v, info: ValidationInfo):
        values = info.data
        return values["fdir"] / values["name"]


# +
def read_file_upload_item(di: dict, fdir=pathlib.Path("."), added_by=None):
    if added_by is None:
        added_by = getuser()
    return File(**di | dict(fdir=fdir, added_by=added_by))


def add_file(upld_item, fdir=pathlib.Path(".")):
    f = read_file_upload_item(upld_item, fdir=fdir)
    f.path.write_bytes(upld_item["content"])
    return f


def add_files_to_dir(upld_value, fdir=pathlib.Path(".")):
    di = {}
    for l in upld_value:
        f = add_file(l, fdir=fdir)
        di[l["name"]] = f
    return [v.path for v in di.values()]


# +
def add_files(upld_value, fdir=pathlib.Path(".")):
    if not pathlib.Path(fdir).exists():
        pathlib.Path(fdir).mkdir(exist_ok=True)
    return add_files_to_dir(upld_value, fdir=fdir)


class FileUploadToDir(w.VBox):
    _value = tr.Unicode(default_value=None, allow_none=True)
    fdir = tr.Instance(klass=pathlib.PurePath, default_value=pathlib.Path("."))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if pathlib.Path(value).is_file():
            self.add_file([pathlib.Path(value)])
        else:
            pass

    @property
    def path(self):
        if self.value is None:
            return None
        else:
            return pathlib.Path(self.value)

    def __init__(self, **kwargs):
        self.upld = w.FileUpload()
        self.bn_delete = w.Button(**DELETE_BUTTON_KWARGS)
        self._show_bn_delete("")
        self.fdisplay = DisplayPath(value=None, order=("exists", "openpreview", "name"))
        self._init_controls()
        super().__init__(**kwargs)
        if "value" in kwargs:
            self.value = kwargs["value"]
        self.children = [
            w.HBox([self.bn_delete, self.upld, self.fdisplay]),
            self.fdisplay.bx_out,
        ]
        self.fdisplay.children = [self.fdisplay.bx_bar]

    def _init_controls(self):
        self.upld.observe(self._upld, "value")
        self.observe(self._show_bn_delete, "_value")
        self.bn_delete.on_click(self._bn_delete)

    def _upld(self, on_change):
        paths = add_files(self.upld.value, fdir=self.fdir)
        self.add_file(paths)
        self.upld.value = ()

    def _bn_delete(self, on_click):
        self.path.unlink()
        self._value = None
        self.fdisplay.value = None

    def _show_bn_delete(self, on_change):
        if self.value is None:
            self.bn_delete.layout.display = "None"
        else:
            self.bn_delete.layout.display = ""

    def add_file(self, paths: list[str]):
        if len(paths) > 1:
            raise ValueError("asdf")
        elif len(paths) == 0:
            return
        else:
            if self.path is not None:
                self.path.unlink(missing_ok=True)
            self.fdisplay.value = str(paths[0])
            self._value = str(paths[0])


if __name__ == "__main__":
    fupld = FileUploadToDir(value="IMG_0688.jpg")
    display(fupld)


# -

class FilesUploadToDir(Array):
    fdir = tr.Instance(klass=pathlib.PurePath, default_value=pathlib.Path("."))
    kwargs_display_path = tr.Dict(default_value={}, allow_none=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _post_init(self, **kwargs):
        self.fn_remove = self.fn_remove_file
        self.add_remove_controls = "remove_only"
        self.show_hash = None
        value = kwargs.get("value")
        if value is not None:
            self.add_files(value)
        kwargs_display_path = kwargs.get("kwargs_display_path")
        self.kwargs_display_path = (lambda v: {} if v is None else v)(
            kwargs_display_path
        )
        self.upld = w.FileUpload(**dict(multiple=True))
        self.children = [self.upld] + list(self.children)
        self._init_controls_FilesUploadToDir()

    def _init_controls_FilesUploadToDir(self):
        self.upld.observe(self._upld, "value")

    def _upld(self, on_change):
        paths = add_files(self.upld.value, fdir=self.fdir)
        self.add_files(paths)
        self.upld.value = ()

    def add_files(self, paths: list[str]):
        for p in paths:
            self.add_row(
                widget=DisplayPath(
                    str(p), **self.kwargs_display_path | dict(order=ORDER_NOTPATH)
                )
            )

    def fn_remove_file(self, bx=None):
        p = pathlib.Path(bx.widget.value)
        p.unlink(missing_ok=True)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self.boxes = []
        self.add_files(value)


if __name__ == "__main__":
    p = pathlib.Path()
    p_ = list(IPYAUTOUI_ROOTDIR.parents)[2] / "docs" / "images" / "logo.png"
    upld = FilesUploadToDir(value=[str(p_)])
    display(upld)
    # test

if __name__ == "__main__":
    upld.value = ["__init__.py", "../automapschema.yaml"]

if __name__ == "__main__":
    from pydantic import BaseModel, Field
    from ipyautoui.custom.fileupload import AutoUploadPaths
    from ipyautoui import AutoUi

    class Test(BaseModel):
        string: str
        paths: list[pathlib.Path] = Field(
            title="A longish title about something",
            description="with a rambling description as well...",
            json_schema_extra=dict(autoui="__main__.FilesUploadToDir"),
        )

    value = {"string": "string", "paths": ["__init__.py"]}
    aui = AutoUi(Test, value=value, nested_widgets=[AutoUploadPaths])
    display(aui)
