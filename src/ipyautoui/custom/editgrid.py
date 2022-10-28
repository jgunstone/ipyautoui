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
#       jupytext_version: 1.14.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
"""General widget for editing data"""
# %run __init__.py
# %run ../__init__.py
# %load_ext lab_black

import traitlets as tr
import typing as ty
import collections
import traceback

import immutables
import pandas as pd
import ipywidgets as widgets
from typing import List
from markdown import markdown
from pydantic import BaseModel, Field
from ipydatagrid import CellRenderer, DataGrid, TextRenderer, Expr, VegaExpr
from ipydatagrid.datagrid import SelectionHelper

import ipyautoui.autoipywidget as aui
import ipyautoui.custom.save_button_bar as sb
from ipyautoui._utils import round_sig_figs, obj_from_importstr
from ipyautoui.automapschema import attach_schema_refs

# from ipyautoui.autoipywidget import AutoIpywidget

from ipyautoui.constants import (
    BUTTON_WIDTH_MIN,
    TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT,
    KWARGS_DATAGRID_DEFAULT,
)

frozenmap = immutables.Map

# TODO: Tasks pending completion -@jovyan at 9/14/2022, 5:09:18 PM
#       review how ipydatagrid works. it has a _data trait which has
#       a schema. Perhaps we can make better use of this / contribute
#       back to the main repo.

# BUG: Reported defects -@jovyan at 9/16/2022, 5:25:13 PM
#      the selection when filtered issue is creating a problem.

# TODO: Tasks pending completion -@jovyan at 9/22/2022, 9:25:53 PM
#       Can BaseForm inherit autoipywidget.AutoObject directly?
# -


class BaseForm(widgets.VBox):
    _value = tr.Dict()
    _cls_ui = tr.Callable(default_value=None, allow_none=True)
    # _row_edit_index = tr.Any(default_value=None)

    def __init__(
        self,
        schema: ty.Union[dict, ty.Type[BaseModel]],
        value: dict = None,
        cls_ui: ty.Callable = None,
        update_map_widgets=None,
        fdir=None,
        save: ty.Callable = lambda: print("SAVE"),
        revert: ty.Callable = lambda: print("REVERT"),
        fn_onsave: ty.Callable = lambda: None,
    ):
        self.fn_save = save
        self.fn_revert = revert
        self.fn_onsave = fn_onsave
        self.schema = schema
        self.update_map_widgets = update_map_widgets
        self.fdir = fdir
        self._update_BaseForm()
        super().__init__()
        self.cls_ui = cls_ui
        self.out = widgets.Output()
        if value is not None:
            self.value = value

    def _init_ui(self):
        self.ui = self.cls_ui(
            self.schema,
            value=self.value,
            # update_map_widgets=self.update_map_widgets,
            # fdir=self.fdir,
        )
        self.children = [self.title, self.save_button_bar, self.ui]
        self.save_button_bar._unsaved_changes(False)

    @property
    def cls_ui(self):
        return self._cls_ui

    @cls_ui.setter
    def cls_ui(self, cls_ui):
        if self._cls_ui != cls_ui or self._cls_ui is None:
            if cls_ui is None:
                self._cls_ui = aui.AutoObject
            else:
                self._cls_ui = cls_ui
            self._init_ui()
            self._update_BaseForm_controls()
        else:
            pass

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self.ui.value = value

    def _update_BaseForm(self):
        self.save_button_bar = sb.SaveButtonBar(
            save=self.fn_save, revert=self.fn_revert, fn_onsave=self.fn_onsave
        )
        self.title = widgets.HTML()
        self.save_button_bar._unsaved_changes(False)

    def _update_BaseForm_controls(self):
        self.ui.observe(self._update_value, "_value")
        self.observe(self._watch_BaseForm_change, "_value")

    def _watch_BaseForm_change(self, change):
        self.save_button_bar._unsaved_changes(True)

    def _update_value(self, change):
        self._value = self.ui.value


if __name__ == "__main__":

    class TestModel(BaseModel):
        string: str = Field("string", title="Important String")
        integer: int = Field(40, title="Integer of somesort")
        floater: float = Field(1.33, title="floater")

    def test_save():
        print("Saved.")

    def test_revert():
        print("Reverted.")

    ui = BaseForm(schema=TestModel, save=test_save, revert=test_revert)
    display(ui)

if __name__ == "__main__":
    ui.value = {"string": "adfs", "integer": 2, "floater": 1.22}

if __name__ == "__main__":
    # With nested object

    class DataFrameCols(BaseModel):
        string: str = Field("string", column_width=100)
        integer: int = Field(1, column_width=80)
        floater: float = Field(3.1415, column_width=70, aui_sig_fig=3)
        something_else: float = Field(324, column_width=100)

    class TestDataFrame(BaseModel):
        dataframe: ty.List[DataFrameCols] = Field(..., format="dataframe")

    schema = attach_schema_refs(TestDataFrame.schema())["properties"]["dataframe"][
        "items"
    ]

    baseform = AutoUi(schema=schema)
    display(baseform)

if __name__ == "__main__":
    di = {"string": "update", "integer": 10, "floater": 3.123, "something_else": 444}
    baseform.value = di

# TODO: rename "add" to "fn_add" so not ambiguous...


class ButtonBar(widgets.HBox):
    def __init__(
        self,
        add: ty.Callable,
        edit: ty.Callable,
        copy: ty.Callable,
        delete: ty.Callable,
        backward: ty.Callable,
        show_message: bool = True,
    ):
        self.show_message = show_message
        self.fn_add = add
        self.fn_edit = edit
        self.fn_copy = copy
        self.fn_delete = delete
        self.fn_backward = backward
        self.out = widgets.Output()
        self._init_form()
        self._init_controls()

    def _init_form(self):
        super().__init__()  # main container
        self.add = widgets.ToggleButton(
            icon="plus",
            button_style="success",
            style={"font_weight": "bold"},
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
        )
        self.edit = widgets.ToggleButton(
            icon="edit",
            button_style="warning",
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
        )
        self.copy = widgets.Button(
            icon="copy",
            button_style="primary",
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
        )
        self.delete = widgets.Button(
            icon="trash-alt",
            button_style="danger",
            layout=widgets.Layout(width=BUTTON_WIDTH_MIN),
        )
        self.message = widgets.HTML()
        children = [self.add, self.edit, self.copy, self.delete]
        children.append(self.message)
        self.children = children

    def _init_controls(self):
        self.add.observe(self._add, "value")
        self.edit.observe(self._edit, "value")
        self.copy.on_click(self._copy)
        self.delete.on_click(self._delete)

    def _add(self, onchange):
        self._reset_message()
        if self.add.value:
            if self.edit.value:
                self.edit.value = False  # If Edit button already clicked on and add is then clicked on then, trigger toggle for Edit button.
            self.add.tooltip = "Go back to table"
            self.add.layout.border = TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT
            self.fn_add()
            if self.show_message:
                self.message.value = markdown("  ➕ _Adding Value_ ")
        else:
            self._reset_message()
            self.add.tooltip = "Add"
            self.add.layout.border = None
            self.add.icon = "plus"
            self.add.button_style = "success"
            self.fn_backward()

    def _edit(self, onchange):
        self._reset_message()
        if self.edit.value:
            if self.add.value:
                self.add.value = False
            self.edit.tooltip = "Go back to table"
            self.edit.layout.border = TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT
            self.fn_edit()
            if self.show_message:
                self.message.value = markdown("  ✏️ _Editing Value_ ")
        else:
            self._reset_message()
            self.edit.tooltip = "Edit"
            self.edit.layout.border = None
            self.edit.icon = "edit"
            self.edit.button_style = "warning"
            self.fn_backward()

    def _copy(self, onchange):
        self._reset_message()
        self.fn_copy()
        if self.show_message:
            self.message.value = markdown("  📝 _Copying Value_ ")

    def _delete(self, click):
        self._reset_message()
        self.fn_delete()
        if self.show_message:
            self.message.value = markdown("  🗑️ _Deleting Value_ ")

    def _reset_message(self):
        self.message.value = ""  # Reset message


if __name__ == "__main__":

    def add():
        print("ADD")

    def edit():
        print("EDIT")

    def copy():
        print("COPY")

    def delete():
        print("DELETE")

    def backward():
        print("BACK")

    button_bar = ButtonBar(
        add=add,
        edit=edit,
        copy=copy,
        delete=delete,
        backward=backward,
    )

    display(button_bar)


# +
# TODO: Move to utils
def is_incremental(li):
    return li == list(range(li[0], li[0] + len(li)))


def get_grid_column_properties_from_schema(schema):
    return schema["items"]["properties"]


def get_name_title_map_from_schema_properties(properties):
    return {k: v["title"] for k, v in properties.items()}


def get_property_types(properties):
    def fn(t):
        if t == "number":
            t = "float"
        try:
            return eval(t)
        except:
            return str

    return {k: fn(v["type"])() for k, v in properties.items()}


# ui.schema
def get_default_row_data_from_schema_properties(properties: dict) -> ty.Optional[dict]:
    """pulls default value from schema. intended for a dataframe (i.e. rows
    of known columns only). assumes all fields have a 'title' (true when using
    pydantic)

    Args:
        properties (dict): schema["items"]["properties"]

    Returns:
        list: list of dictionary column values
    """
    di = {}
    for k, v in properties.items():
        if "default" in v.keys():
            di[k] = v["default"]
        else:
            return None
    return di


# +
def get_default_grid_data_from_schema(schema: dict) -> pd.DataFrame:
    """pulls default value from schema. intended for a dataframe (i.e. rows
    of known columns only). assumes all fields have a 'title' (true when using
    pydantic)

    Args:
        properties (dict): schema["items"]["properties"]

    Returns:
        list: list of dictionary column values
    """
    if "default" in schema.keys():
        return pd.DataFrame(schema["default"])
    else:
        properties = get_grid_column_properties_from_schema(schema)
        data = get_default_row_data_from_schema_properties(properties)
        if data is not None:
            return pd.DataFrame([data])
        else:
            return pd.DataFrame(get_property_types(properties), index=[])


def get_column_widths_from_schema(schema, column_properties, map_name_title, **kwargs):
    """Set the column widths of the data grid based on column_width given in the schema."""

    # start with settings in properties
    column_widths = {
        v["title"]: v["column_width"]
        for v in column_properties.values()
        if "column_width" in v
    }

    # override with high level schema props
    if "column_widths" in schema:
        column_widths = column_widths | schema["column_widths"]

    # overide with kwargs passed to AutoDataGrid
    if "column_widths" in kwargs:
        _ = {map_name_title[k]: v for k, v in kwargs["column_widths"].items()}
        column_widths = column_widths | _

    return column_widths


def build_renderer(var: ty.Union[str, dict]) -> CellRenderer:
    """builds a renderer for datagrid. if the input is a dict, the function assumes
    the renderer to use is `ipydatagrid.TextRenderer` and initiates it with the dict.
    This is appropriate for simple renderers only. If it is a string, it assumes that
    the renderer must be built by a zero-arg callable function that is referenced by an
    object string.

    Args:
        var (ty.Union[str, dict]): _description_
    """
    fn = lambda v: TextRenderer(**v) if isinstance(v, dict) else obj_from_importstr(v)()
    return fn(var)


def get_column_renderers_from_schema(
    schema, column_properties, map_name_title, **kwargs
) -> dict:
    """when saved to schema the renderer is a PyObject callable..."""

    # start with settings in properties
    renderers = {
        v["title"]: build_renderer(v["renderer"])
        for v in column_properties.values()
        if "renderer" in v
    }

    # override with high level schema props
    if "renderers" in schema:
        renderers = renderers | {k: build_renderer(v) for k, v in schema["renderers"]}

    # overide with kwargs passed to AutoDataGrid
    if "renderers" in kwargs:
        _ = {map_name_title[k]: v for k, v in kwargs["renderers"].items()}
        renderers = renderers | _

    return renderers


def get_global_renderer_from_schema(
    schema, renderer_name, **kwargs
) -> ty.Union[None, CellRenderer]:

    if renderer_name in kwargs:
        return kwargs[renderer_name]

    get_from_schema = lambda r, schema: schema[r] if r in schema.keys() else None
    _ = get_from_schema(renderer_name, schema)

    if _ is not None:
        return build_renderer(_)
    else:
        return None


def get_global_renderers_from_schema(schema, **kwargs) -> dict:
    li_renderers = ["default_renderer", "header_renderer", "corner_renderer"]
    # ^ globally specified ipydatagrid renderers
    renderers = {
        l: get_global_renderer_from_schema(schema, l, **kwargs) for l in li_renderers
    }
    return {k: v for k, v in renderers.items() if v is not None}


def create_grid_caller(schema: dict, **kwargs) -> dict:
    """analagous to `ipyautoui.autowidgets.create_widget_caller`

    Args:
        schema (_type_): _description_
    """
    kwargs_ = kwargs.copy()
    column_properties = get_grid_column_properties_from_schema(schema)
    map_name_title = get_name_title_map_from_schema_properties(column_properties)

    kwargs_["column_widths"] = get_column_widths_from_schema(
        schema, column_properties, map_name_title, **kwargs
    )

    kwargs_["renderers"] = get_column_renderers_from_schema(
        schema, column_properties, map_name_title, **kwargs
    )

    kwargs_ = kwargs_ | get_global_renderers_from_schema(schema, **kwargs)

    return kwargs_


class AutoGrid(DataGrid):
    """a thin wrapper around DataGrid that makes makes it possible to initiate the
    grid from a json-schema / pydantic model"""

    _value = tr.List()
    schema = tr.Dict()

    @tr.observe("schema")
    def _update_from_schema(self, change):
        self.map_name_title = get_name_title_map_from_schema_properties(self.properties)
        self.kwargs_merge_schema = create_grid_caller(self.schema)

    @tr.validate("schema")
    def _valid_schema(self, proposal):
        if "type" in proposal["value"] and proposal["value"]["type"] == "array":
            if (
                "items" in proposal["value"]
                and "properties" in proposal["value"]["items"]
            ):
                return proposal["value"]
            else:
                raise tr.TraitError("schema have items and properties")
        else:
            raise tr.TraitError('schema must be of of type == "array"')

    def __init__(
        self,
        schema: ty.Union[dict, ty.Type[BaseModel]],
        data: ty.Optional[pd.DataFrame] = None,
        value: ty.Optional[list] = None,
        by_alias: bool = False,
        by_title: bool = True,
        kwargs_datagrid_default: frozenmap = frozenmap(),
        kwargs_datagrid_update: frozenmap = frozenmap(),
        **kwargs,
    ):
        # accept schema or pydantic schema
        self.kwargs = kwargs
        self.by_title = by_title
        self.model, self.schema = aui._init_model_schema(schema, by_alias=by_alias)
        data = self._init_data(data)
        super().__init__(
            data,
            **self.kwargs_merge_schema,
        )

    def _init_data(self, data) -> pd.DataFrame:
        if data is None:
            data = get_default_grid_data_from_schema(self.schema)
            if self.by_title:
                data = data.rename(columns=self.map_name_title)
        else:
            if set(data.columns) == set(self.map_name_title.keys()):
                data = data.rename(columns=self.map_name_title)
        return data

    @property
    def properties(self):
        return get_grid_column_properties_from_schema(self.schema)

    def set_row_value(self, key: int, value: dict):
        """Set a chosen row using the key and a value given.

        Note: We do not call value setter to apply values as it resets the datagrid.

        Args:
            key (int): The key of the row.
            value (dict): The data we want to input into the row.
        """
        if set([col for col, v in value.items()]) != set(
            [col for col, v in self.value[0].items()]
        ):
            raise Exception("Columns of value given do not match with value keys.")

        # value_with_titles is used for datagrid
        value_with_titles = {
            self.di_field_to_titles.get(name): v for name, v in value.items()
        }
        for col, sig_fig in self.aui_sig_figs.items():
            value_with_titles[col] = round_sig_figs(
                value_with_titles[col], sig_figs=sig_fig
            )

        for column, v in value_with_titles.items():
            self.set_cell_value(column, key, v)

        self._value[key] = {k: v for k, v in value.items()}

    def _round_sig_figs(self, df):
        """Round values in dataframe to desired significant figures as given in the schema.

        Args:
            df (pd.DataFrame): dataframe to round sig figs on.
        """
        for k, v in self.aui_sig_figs.items():
            df.loc[:, k] = df.loc[:, k].apply(lambda x: round_sig_figs(x, sig_figs=v))
        return df

    def _check_value(self, value: list):
        """Checking column names in value passed match those within the dataframe.

        Args:
            value (list): list of dicts.
        """
        for di_value in value:
            columns = [name for name in di_value.keys()]
            if not collections.Counter(columns) == collections.Counter(
                self.li_field_names
            ):
                raise Exception(
                    "Schema fields and data fields do not match.\nRejected Columns:"
                    f" {set(columns) ^ set(self.li_field_names)}"
                )

    def _set_titles(self, value: list):
        """Replace field names with titles in value passed.

        Args:
            value (list): Replace all the keys in the dictionaries with associated titles from schema.
        """
        data = [
            {
                self.di_field_to_titles.get(name): value
                for name, value in di_value.items()
            }  # Replace name from value with title from schema
            for di_value in value
        ]
        return data

    def filter_by_column_name(self, column_name: str, li_filter: list):
        """Filter rows to display based on a column name and a list of objects belonging to that column.

        Args:
            column_name (str): column name we want to apply the transform to.
            li_filter (list): Values within the column we want to display in the grid.
        """
        self.transform(
            [
                {
                    "type": "filter",
                    "columnIndex": self.data.columns.get_loc(column_name) + 1,
                    "operator": "in",
                    "value": li_filter,
                }
            ]
        )

    # move rows around
    # ----------------
    def _swap_rows(self, key_a: int, key_b: int):
        """Swap two rows by giving their keys.

        Args:
            key_a (int): Key of a row.
            key_b (int): Key of another row.
        """
        di_a = self.value[key_a]
        di_b = self.value[key_b]
        self.set_row_value(key=key_b, value=di_a)
        self.set_row_value(key=key_a, value=di_b)

    def _move_row_down(self, key: int):
        """Move a row down.

        Args:
            key (int): Key of the row
        """
        if key + 1 == len(self.data):
            raise Exception("Can't move down last row.")
        self._swap_rows(key_a=key, key_b=key + 1)

    def _move_row_up(self, key: int):
        """Move a row up.

        Args:
            key (int): Key of the row
        """
        if key - 1 == -1:
            raise Exception("Can't move up first row.")
        self._swap_rows(key_a=key, key_b=key - 1)

    def _move_rows_up(self, li_keys: List[int]):
        """Move multiple rows up.

        Args:
            li_key (List[int]): List of row keys.
        """
        if is_incremental(sorted(li_keys)) is False:
            raise Exception("Only select a property or block of properties.")
        for key in sorted(li_keys):
            self._move_row_up(key)
        self.selections = [
            {"r1": min(li_keys) - 1, "r2": max(li_keys) - 1, "c1": 0, "c2": 2}
        ]

    def _move_rows_down(self, li_keys: List[int]):
        """Move multiple rows down.

        Args:
            li_key (List[int]): List of row keys.
        """
        if is_incremental(sorted(li_keys)) is False:
            raise Exception("Only select a property or block of properties.")
        for key in sorted(li_keys, reverse=True):
            self._move_row_down(key)
        self.selections = [
            {"r1": min(li_keys) + 1, "r2": max(li_keys) + 1, "c1": 0, "c2": 2}
        ]

    # ----------------

    @property
    def di_default_value(self):
        """Obtain default value given in schema."""
        return {
            col_name: (col_data["default"] if "default" in col_data.keys() else None)
            for col_name, col_data in self.properties.items()
        }

    @property
    def di_field_to_titles(self):
        return {field: di["title"] for field, di in self.properties.items()}

    @property
    def selected_visible_cell_iterator(self):
        """
        An iterator to traverse selected cells one by one.
        """
        # Copy of the front-end data model
        view_data = self.get_visible_data()

        # Get primary key from dataframe
        index_key = self.get_dataframe_index(view_data)

        # Serielize to JSON table schema
        view_data_object = self.generate_data_object(view_data, "ipydguuid", index_key)

        return SelectionHelper(view_data_object, self.selections, self.selection_mode)

    @property
    def selected_rows_data(self):
        """Get the data selected in the table which is returned as a dataframe."""
        s = self.selected_visible_cell_iterator
        rows = set([l["r"] for l in s])
        return [s._data["data"][r] for r in rows]

    @property
    def selected_keys(self):
        """Return the keys of the selected rows. still works if transform applied."""
        s = self.selected_visible_cell_iterator
        index = self.get_dataframe_index(self.data)
        rows = set([l["r"] for l in s])
        return [s._data["data"][r][index] for r in rows]

    @property
    def li_field_names(self):
        return [col_name for col_name, col_data in self.properties.items()]

    @property
    def aui_sig_figs(self):
        self._aui_sig_figs = {
            col_data["title"]: col_data["aui_sig_fig"]
            for col_name, col_data in self.properties.items()
            if "aui_sig_fig" in col_data
        }
        return self._aui_sig_figs

    @property
    def kwargs_datagrid_update(self):
        return self._kwargs_datagrid_update

    @kwargs_datagrid_update.setter
    def kwargs_datagrid_update(self, value):
        self._kwargs_datagrid_update = value
        for k, v in value.items():
            setattr(self, k, v)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == [] or value is None:
            self._value = []
            self.data = self.df_empty
        else:
            self._check_value(value)
            self._value = value
            data = self._set_titles(self._value)
            df = pd.DataFrame.from_dict(data)
            self.data = self._round_sig_figs(df)


# -

if __name__ == "__main__":

    class DataFrameCols(BaseModel):
        string: str = Field(
            "string",
            title="Important String",
            column_width=120,
        )
        integer: int = Field(40, title="Integer of somesort", column_width=150)
        floater: float = Field(1.33, title="Floater", column_width=70, aui_sig_fig=3)

    class TestDataFrame(BaseModel):
        # dataframe: ty.List[DataFrameCols] = Field(..., format="dataframe")
        __root__: ty.List[DataFrameCols] = Field(..., format="dataframe")

    # schema = attach_schema_refs(TestDataFrame.schema())["properties"]["dataframe"]

    grid = AutoGrid(schema=TestDataFrame)
    display(grid)


if __name__ == "__main__":
    eg_value = [
        {
            "string": "important string",
            "integer": 1,
            "floater": 3.14,
        },
        {
            "string": "update",
            "integer": 4,
            "floater": 3.12344,
        },
        {"string": "evening", "integer": 5, "floater": 3.14},
        {"string": "morning", "integer": 5, "floater": 3.14},
        {"string": "number", "integer": 3, "floater": 3.14},
    ]
    grid.value = eg_value * 10

if __name__ == "__main__":
    grid = AutoGrid(
        schema=TestDataFrame,
        value=eg_value,
    )
    display(grid)


# +
class DataHandler(BaseModel):
    fn_get_all_data: ty.Callable
    fn_post: ty.Callable
    fn_patch: ty.Callable
    fn_delete: ty.Callable
    fn_copy: ty.Callable


class RowUiCallables(BaseModel):
    add: ty.Callable
    edit: ty.Callable


# -

# IDEA: Possible implementations -@jovyan at 9/3/2022, 11:29:20 AM
# review having both AutoGrid and EditGrid. This means an additional
# nesting that requires keeping the _value of both the AutoGrid
# object and the EditGrid object up-to-date. or maybe AutoGrid
# doesn't require a _value trait as it is never used within EditGrid.
class EditGrid(widgets.VBox):
    _value = tr.List()

    def __init__(
        self,
        schema: ty.Union[dict, ty.Type[BaseModel]],
        value: ty.Optional[dict] = None,
        by_alias: bool = False,
        datahandler: DataHandler = None,
        ui_add: ty.Callable = None,
        ui_edit: ty.Callable = None,
        kwargs_datagrid_default: frozenmap = {},
        kwargs_datagrid_update: frozenmap = {},
        description: str = "",
        fn_on_copy: ty.Callable = None,
    ):
        self.ui_add = ui_add
        self.ui_edit = ui_edit
        self.fn_on_copy = fn_on_copy
        self.model, self.schema = aui._init_model_schema(schema, by_alias=by_alias)
        self.datahandler = datahandler
        if self.datahandler is not None:
            value = self.datahandler.fn_get_all_data()
        self.out = widgets.Output()
        self._init_form(
            value=value,
            schema=self.schema,
            kwargs_datagrid_default=kwargs_datagrid_default,
            kwargs_datagrid_update=kwargs_datagrid_update,
            description=description,
        )
        self._init_controls()
        self._edit_bool = False  # Initially define edit mode to be false

    def _init_form(
        self,
        schema,
        value,
        kwargs_datagrid_default,
        kwargs_datagrid_update,
        description,
    ):
        super().__init__(layout={"width": "100%"})  # main container
        self.button_bar = ButtonBar(
            add=self._add,
            edit=self._edit,
            copy=self._copy,
            delete=self._delete,
            backward=self._backward,
            show_message=False,
        )
        self.description = widgets.HTML(description)
        self.grid = AutoGrid(
            schema=schema,
            value=value,
            selection_mode="row",
            kwargs_datagrid_default=kwargs_datagrid_default,
            kwargs_datagrid_update=kwargs_datagrid_update,
        )
        self.baseform = BaseForm(
            schema=self.schema["items"],
            save=self._save,
            revert=self._revert,
            fn_onsave=self._onsave,
        )
        self.baseform.title.value = ""
        self.button_bar.layout = widgets.Layout(padding="0px 20px")
        self.baseform.save_button_bar.layout = widgets.Layout(padding="0px 20px")
        self.baseform.layout = widgets.Layout(padding="0px 0px 40px 0px")
        self.children = [self.description, self.button_bar, self.baseform, self.grid]
        self.baseform.layout.display = "none"  # Hide base form menu

    def _init_controls(self):
        self.grid.observe(self._update_baseform, "selections")

    def _update_baseform(self, onchange):
        if (
            len(self.grid.selected_keys) == 1
            and self.baseform.layout.display == "block"
        ):
            print(self.di_row_value)
            self.baseform.value = self.di_row_value
            self.baseform.save_button_bar._unsaved_changes(False)

    def _update_baseform_ui(self, cls_ui):
        if type(self.baseform) != cls_ui:
            self.baseform.cls_ui = cls_ui

    @property
    def selected_row(self):
        return self.grid.selected_keys[0]

    def _add(self):
        self.baseform.cls_ui = self.ui_add
        try:
            self._edit_bool = False  # Editing mode is False, therefore addition mode
            self.grid.clear_selection()  # Clear selection of data grid. We don't want to replace an existing value by accident.
            self.initial_value = self.grid.di_default_value
            self.baseform.value = self.grid.di_default_value
            self.baseform.save_button_bar._unsaved_changes(False)
            self._display_baseform()
            self.button_bar.message.value = markdown("  ➕ _Adding Value_ ")
        except Exception as e:
            self.button_bar.message.value = markdown("  ☠️ _Failed to add_")
            traceback.print_exc()

    def _edit(self):
        self.baseform.cls_ui = self.ui_edit
        try:
            self._check_one_row_selected()
            if len(self.grid.selected_keys) == 0:
                raise ValueError("you must select a row")
            self.initial_value = self.di_row_value
            self.baseform.value = self.di_row_value  # Set values in fields
            self.baseform.save_button_bar._unsaved_changes(
                False
            )  # Set unsaved changes button back to False
            self._display_baseform()
            self.button_bar.message.value = markdown("  ✏️ _Editing Value_ ")
            self._edit_bool = True  # Editing mode is True
        except Exception as e:
            self.button_bar.edit.value = False
            self.button_bar.message.value = markdown(
                "  👇 _Please select one row from the table!_ "
            )
            traceback.print_exc()

    def _copy(self):
        try:
            if self.grid.selected_keys == set():
                self.button_bar.message.value = markdown(
                    "  👇 _Please select a row from the table!_ "
                )
            else:
                li_values_selected = [
                    self.value[i] for i in sorted([i for i in self.grid.selected_keys])
                ]
                if self.fn_on_copy is not None:
                    li_values_selected = self.fn_on_copy(li_values_selected)
                if self.datahandler is not None:
                    for value in li_values_selected:
                        self.datahandler.fn_copy(value)
                    self._reload_all_data()
                else:
                    self.value += li_values_selected
                    # ^ add copied values

                self.button_bar.message.value = markdown("  📝 _Copied Data_ ")
                self._edit_bool = False  # Want to add the values
        except Exception as e:
            self.button_bar.message.value = markdown(
                "  👇 _Please select a row from the table!_ "
            )
            traceback.print_exc()

    def _delete(self):
        try:
            self._set_toggle_buttons_to_false()
            if self.grid.selected_keys:
                print(f"Row Number: {self.grid.selected_keys}")
                if self.datahandler is not None:
                    value = [self.value[i] for i in self.grid.selected_keys]
                    for v in value:
                        self.datahandler.fn_delete(v)
                    self._reload_all_data()
                else:
                    self.value = [
                        value
                        for i, value in enumerate(self.value)
                        if i not in self.grid.selected_keys
                    ]
                    # ^ Only set for values NOT in self.grid.selected_keys
                self.button_bar.message.value = markdown("  🗑️ _Deleted Row_ ")

            else:
                self.button_bar.message.value = markdown(
                    "  👇 _Please select one row from the table!_"
                )
        except Exception as e:
            traceback.print_exc()

    def _check_one_row_selected(self):
        if len(self.grid.selected_keys) > 1:
            raise Exception(
                markdown("  👇 _Please only select ONLY one row from the table!_")
            )

    def _save(self):
        if self._edit_bool:  # If editing then use patch
            if self.datahandler is not None:
                value = self.baseform.value
                self.datahandler.fn_patch(value)
                self._reload_all_data()
            else:
                value = self.value
                value[self.selected_row] = self.baseform.value
                self.value = value
                # ^ Call setter
        else:  # Else, if adding values, use post
            if self.datahandler is not None:
                value = self.baseform.value
                self.datahandler.fn_post(value)
                self._reload_all_data()
            else:
                if not self.grid._data["data"]:  # If no data in grid
                    self.value = [self.baseform.value]
                else:
                    # Append new row onto data frame and set to grid's data.
                    value = self.value
                    value.append(self.baseform.value)
                    self.value = value  # Call setter

    def _onsave(self):
        self._display_grid()
        self._set_toggle_buttons_to_false()
        if self._edit_bool:  # If editing
            self.button_bar.message.value = markdown(
                "  💾 _Successfully updated row_ "
            )  # TODO: Make generic
        else:
            self.button_bar.message.value = markdown(
                "  💾 _Successfully added row_ "
            )  # TODO: Make generic

    def _backward(self):
        self._display_grid()

    def _revert(self):
        self.baseform.value = self.initial_value

    def _set_toggle_buttons_to_false(self):
        if self.button_bar.add.value is True:
            self.button_bar.add.value = False
        elif self.button_bar.edit.value is True:
            self.button_bar.edit.value = False

    def _display_grid(self):
        if self.button_bar.edit.value or self.button_bar.add.value:
            # ^ Don't remove display of base form if already showing when going from edit to add (or vice versa).
            pass
        else:
            self.baseform.layout.display = "none"  # Hides base form menu
            self._set_toggle_buttons_to_false()

    def _display_baseform(self):
        self.baseform.layout.display = "block"  # Displays base form menu

    def _reload_all_data(self):
        if self.datahandler is not None:
            self.value = self.datahandler.fn_get_all_data()

    @property
    def value(self):
        self._value = self.grid._value
        return self._value

    @value.setter
    def value(self, value):
        self.grid.value = value
        self._value = self.grid.value

    @property
    def di_row_value(self):  # TODO: remove THIS
        try:
            self._check_one_row_selected()  # Performing checks to see if only one row is selected
            di = self.grid.selected_rows_data[0]
            cols = [v["title"] for k, v in self.baseform.schema["properties"].items()]
            return {c: di[c] for c in cols}

        except Exception as e:
            self.button_bar.message.value = markdown(f"_{e}_")
            traceback.print_exc()


if __name__ == "__main__":
    AUTO_GRID_DEFAULT_VALUE = [
        {
            "string": "important string",
            "integer": 1,
            "floater": 3.14,
        },
        {
            "string": "update",
            "integer": 4,
            "floater": 3.12344,
        },
        {"string": "evening", "integer": 5, "floater": 3.14},
        {"string": "morning", "integer": 5, "floater": 3.14},
        {"string": "number", "integer": 3, "floater": 3.14},
    ]

    class DataFrameCols(BaseModel):
        string: str = Field("string", column_width=100)
        integer: int = Field(1, column_width=80)
        floater: float = Field(3.1415, column_width=70, aui_sig_fig=3)

    class TestDataFrameOnly(BaseModel):
        """a description of TestDataFrame"""

        __root__: ty.List[DataFrameCols] = Field(
            default=AUTO_GRID_DEFAULT_VALUE, format="dataframe"
        )


if __name__ == "__main__":
    description = markdown(
        "<b>The Wonderful Edit Grid Application</b><br>Useful for all editing purposes"
        " whatever they may be 👍"
    )
    editgrid = EditGrid(
        schema=TestDataFrameOnly, description=description, ui_add=None, ui_edit=AutoUi
    )
    display(editgrid)

if __name__ == "__main__":

    class TestDataFrame(BaseModel):
        __root__: ty.List[DataFrameCols] = Field(
            default=AUTO_GRID_DEFAULT_VALUE, format="dataframe"
        )


if __name__ == "__main__":
    from ipyautoui import AutoUi
    from ipyautoui.autoipywidget import AutoIpywidget

    ui = AutoIpywidget(schema=TestDataFrame)
    display(ui)

if __name__ == "__main__":
    description = markdown(
        "<b>The Wonderful Edit Grid Application</b><br>Useful for all editing purposes"
        " whatever they may be 👍"
    )
    editgrid = EditGrid(
        schema=TestDataFrame, description=description, ui_add=None, ui_edit=AutoUi
    )
    editgrid.value = AUTO_GRID_DEFAULT_VALUE

    display(editgrid)


# editgrid.grid.selected_rows_data

# editgrid.grid.selected_rows

# editgrid.grid.selected_keys

# editgrid.grid.get_dataframe_index(editgrid.grid.data)

# editgrid.grid._data["data"]

# editgrid.grid._data["schema"]

# editgrid.grid._data["fields"]
