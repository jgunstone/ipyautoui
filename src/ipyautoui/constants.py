"""contains packages global constants"""
import pathlib

from ipydatagrid import TextRenderer, Expr, VegaExpr

from ipyautoui._utils import frozenmap
# https://www.python.org/dev/peps/pep-0603/
# https://github.com/MagicStack/immutables
# ^
DIR_MODULE = pathlib.Path(__file__).parent
DIR_EXAMPLE = DIR_MODULE.parents[1] / "examples"

BUTTON_WIDTH_MIN = '41px'
BUTTON_WIDTH_MEDIUM = '90px'
BUTTON_HEIGHT_MIN = '25px'
ROW_WIDTH_MEDIUM = '120px'
ROW_WIDTH_MIN = '60px'
BUTTON_MIN_SIZE = frozenmap(width=BUTTON_WIDTH_MIN, height=BUTTON_HEIGHT_MIN)

ADD_BUTTON_KWARGS = frozenmap(
    icon="plus",
    style={},
    button_style="success",
    tooltip="add item",
    layout={"width": BUTTON_WIDTH_MIN, "height": BUTTON_HEIGHT_MIN},
    disabled=False
)
REMOVE_BUTTON_KWARGS = frozenmap(
    icon="minus",
    style={},
    button_style="danger",
    tooltip="remove item",
    layout={"width": BUTTON_WIDTH_MIN, "height": BUTTON_HEIGHT_MIN},
    disabled=False
)
BLANK_BUTTON_KWARGS = frozenmap(
    icon="",
    style={"button_color":"white"},
    layout={"width": BUTTON_WIDTH_MIN, "height": BUTTON_HEIGHT_MIN},
    disabled=True
)

KWARGS_DATAGRID_DEFAULT = frozenmap(
    header_renderer = TextRenderer(
        vertical_alignment="top",
        horizontal_alignment="center",
    )
)

TOGGLEBUTTON_ONCLICK_BORDER_LAYOUT = 'solid yellow 2px'

# documentinfo ------------------------------
#  update this with WebApp data. TODO: delete this? 
ROLES = ('Design Lead',
'Project Engineer',
'Engineer',
'Project Coordinator',
'Project Administrator',
'Building Performance Modeller')

DI_JSONSCHEMA_WIDGET_MAP = frozenmap(**{
    'minimum': 'min',
    'maximum': 'max',
    'enum': 'options',
    'default': 'value',
    'description': 'autoui_description'
})
#  ^ this is how the json-schema names map to ipywidgets.

def load_test_constants():
    """only in use for debugging within the package. not used in production code.

    Returns:
        module: test_constants object
    """
    from importlib.machinery import SourceFileLoader
    path_testing_constants = DIR_MODULE.parents[1] / 'tests' / 'constants.py'
    test_constants = SourceFileLoader("constants", str(path_testing_constants)).load_module()
    return test_constants


def DISPLAY_AUTOUI_EXAMPLE():
    from ipyautoui.autoui import display_template_ui_model
    display_template_ui_model()