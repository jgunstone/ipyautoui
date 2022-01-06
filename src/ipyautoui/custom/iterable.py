# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.3
#   kernelspec:
#     display_name: Python [conda env:ipyautoui]
#     language: python
#     name: conda-env-ipyautoui-xpython
# ---

# %%
"""generic iterable object."""
# %run __init__.py
# %load_ext lab_black

# %%
import ipywidgets as widgets
import traitlets
from traitlets import validate
import typing
import immutables
# from pydantic.dataclasses import dataclass
from ipyautoui.basemodel import BaseModel
from pydantic import validator
import uuid
from uuid import UUID
import functools
import math
from ipyautoui.constants import (
    ADD_BUTTON_KWARGS,
    REMOVE_BUTTON_KWARGS,
    BLANK_BUTTON_KWARGS,
    BUTTON_WIDTH_MIN,
    BUTTON_HEIGHT_MIN,
    BUTTON_MIN_SIZE
)
from markdown import markdown

frozenmap = (
    immutables.Map
)  # https://www.python.org/dev/peps/pep-0603/, https://github.com/MagicStack/immutables
BOX = frozenmap({True: widgets.HBox, False: widgets.VBox})
TOGGLE_BUTTON_KWARGS = frozenmap(
    icon="", layout={"width": BUTTON_WIDTH_MIN, "height": BUTTON_HEIGHT_MIN},
)


# %%
class IterableItem(BaseModel):
    index: int
    key: typing.Union[UUID, str, int, float, bool] = None
    item: typing.Any = None
    add: typing.Any = None
    remove: typing.Any = None
    label: typing.Any = None
    orient_rows: bool = True
    row: typing.Any = None
    
    @validator("key", always=True)
    def _key(cls, v, values):
        if v is None:
            return uuid.uuid4()
        else:
            return v
    
    @validator("add", always=True)
    def _add(cls, v, values):
        if v is None:
            return widgets.Button(layout=dict(BUTTON_MIN_SIZE))
        else:
            return v
    
    @validator("remove", always=True)
    def _remove(cls, v, values):
        if v is None:
            return widgets.Button(layout=dict(BUTTON_MIN_SIZE))
        else:
            return v
    
    @validator("label", always=True)
    def _label(cls, v, values):
        if v is None:
            return widgets.HTML('placeholder label')
        else:
            return v
        
    @validator("item", always=True)
    def _item(cls, v, values):
        if v is None:
            return widgets.Button(description='placeholder item')
        else:
            return v
        
    @validator("row", always=True)
    def _row(cls, v, values):
        ItemBox = BOX[values['orient_rows']]
        if v is None:
            v = ItemBox(children=[
                ItemBox(layout=widgets.Layout(flex='1 0 auto')), # buttons
                ItemBox(layout=widgets.Layout(flex='1 0 auto')), # label
                ItemBox(layout=widgets.Layout(flex='100%')), # item
            ]
                              )
            v.children[2].children = [values['item']]
            return v
        else:
            return v
    


# %%
class Array(widgets.VBox, traitlets.HasTraits):
    """generic iterable. pass a list of items"""
    # -----------------------------------------------------------------------------------
    value = traitlets.List()
    _show_hash = traitlets.Unicode(allow_none=True)
    _add_remove_controls = traitlets.Unicode(allow_none=True)
    _sort_on = traitlets.Unicode(allow_none=True)
    
    @validate("show_hash")
    def _validate_show_hash(self, proposal):
        if proposal.value not in ["index", "key", None]:
            raise ValueError(
                f'{proposal} given. allowed values of show_hash are "index", "key" and None only'
            )
        return proposal
    
    @validate("_add_remove_controls")
    def _validate_add_remove_controls(self, proposal):
        if proposal.value not in ["add_remove", "append_only", "remove_only", None]:
            raise ValueError(
                f'{proposal} given. allowed values of _add_remove_controls are "add_remove", "append_only", "remove_only", None only'
            )
        return proposal
    
    @validate("_sort_on")
    def _validate_add_remove_controls(self, proposal):
        if proposal.value not in ["index", "key", None]:
            raise ValueError(
                f'{proposal} given. allowed values of sort_on are "index", "key" and None only'
            )
        return proposal
    
    def _update_value(self, onchange):
        self.value = [a.item.value for a in self.iterable]
        
    # -----------------------------------------------------------------------------------
    def __init__(
        self,
        items: typing.List=None,
        toggle=False,
        title=None,
        fn_add: typing.Callable = lambda: display("add item"),
        fn_add_dialogue: typing.Callable = None,
        fn_remove: typing.Callable = lambda: display("remove item"),
        watch_value: bool = True,
        minlen: int =1,
        maxlen: int =None,
        add_remove_controls: str ='add_remove',
        show_hash: str ='index',
        sort_on='index',
        orient_rows=True
    ):
        self.orient_rows = orient_rows
        self.minlen = minlen  # TODO: validation. must be > 1
        if maxlen is None:
            maxlen = 100
        self.maxlen = maxlen
        self.fn_add = fn_add
        self.fn_add_dialogue = fn_add_dialogue
        self.fn_remove = fn_remove
        self.watch_value = watch_value
        self.zfill = 2
        
        self.iterable = self._init_iterable(items)
        self._init_form()
        self._toggle = toggle
        self.title = title
        
        self.add_remove_controls = add_remove_controls # calls self._init_controls()
        self.show_hash = show_hash
        self.sort_on= sort_on

    def _init_iterable(self, items):
        return [
            IterableItem(
                index=n,
                key=uuid.uuid4(),
                item=i,
            )
            for n, i in enumerate(items)
        ]
    
    @property
    def items(self):
        return [i.item for i in self.iterable]
    
    @items.setter
    def items(self, value: typing.List):
        self.iterable = self._init_iterable(value)
        self._update_rows_box()
        self._update_rows()
        self._init_controls()
    
    def _init_form(self):
        # init containers
        super().__init__(layout=widgets.Layout(width='100%', display="flex", flex="flex-grow")) # main container
        self.rows_box = BOX[not self.orient_rows](layout=widgets.Layout(width='100%', display="flex", flex="flex-grow"))
        self.title_box = widgets.HBox(layout=widgets.Layout(display="flex", flex="flex-grow")) #BOX[self.orient_rows]
        self.toggle_button = widgets.ToggleButton(icon="minus",layout=dict(BUTTON_MIN_SIZE))
        self.toggle_button.value = True
        self._refresh_children()
        self._update_rows_box()
        
    def _refresh_children(self):
        self.children = [self.title_box, self.rows_box]
        
    # buttons ---------------    
    def _style_zeroth_buttonbar(self):
        if self.add_remove_controls is None:
            pass
        elif self.add_remove_controls == "add_remove":
            [setattr(self.iterable[0].add, k, v)for k, v in ADD_BUTTON_KWARGS.items()]
            [setattr(self.iterable[0].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        elif self.add_remove_controls == "append_only":
            [setattr(self.iterable[0].add, k, v)for k, v in ADD_BUTTON_KWARGS.items()]
            [setattr(self.iterable[0].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        elif self.add_remove_controls == "remove_only":
            [setattr(self.iterable[0].add, k, v)for k, v in BLANK_BUTTON_KWARGS.items()]
            [setattr(self.iterable[0].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        else:
            pass
        
    def _style_nth_buttonbar(self, index):
        if self.add_remove_controls is None:
            pass
        elif self.add_remove_controls == "add_remove":
            [setattr(self.iterable[index].add, k, v)for k, v in ADD_BUTTON_KWARGS.items()]
            [setattr(self.iterable[index].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        elif self.add_remove_controls == "append_only":
            [setattr(self.iterable[index].add, k, v)for k, v in BLANK_BUTTON_KWARGS.items()]
            [setattr(self.iterable[index].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        elif self.add_remove_controls == "remove_only":
            [setattr(self.iterable[index].add, k, v)for k, v in BLANK_BUTTON_KWARGS.items()]
            [setattr(self.iterable[index].remove, k, v)for k, v in REMOVE_BUTTON_KWARGS.items()]
        else:
            pass
        
    def _style_buttonbar(self, index):
        if index == 0: 
            self._style_zeroth_buttonbar()
        else:
            self._style_nth_buttonbar(index)
        
    def _update_buttonbar_box(self, index):
        if self.add_remove_controls is None:
            buttons_box = []
        else:
            self.iterable[index].add = widgets.Button(layout=dict(BUTTON_MIN_SIZE))
            self.iterable[index].remove = widgets.Button(layout=dict(BUTTON_MIN_SIZE))
            buttons_box = [self.iterable[index].add, self.iterable[index].remove]
        self.iterable[index].row.children[0].children = buttons_box
        
    def _update_buttonbar(self, index):
        self._update_buttonbar_box(index)
        self._style_buttonbar(index)
        
    def _update_label(self, index):
        if self.show_hash is None:
            labels_box = []
            self.iterable[index].row.children[1].children = labels_box
            return 
        if self.show_hash == "index":
            label = str(self.iterable[index].index).zfill(self.zfill) + ". "    
        elif self.show_hash == "key":
            label = str(self.iterable[index].key)
        else:
            label = ''
        self.iterable[index].label.value = f"<b>{label}</b>"
        labels_box = [self.iterable[index].label]
        self.iterable[index].row.children[1].children = labels_box
        
    def _update_row(self, index):
        self._update_buttonbar(index)
        self._update_labels()
        
    def _update_buttonbars(self):
        [self._update_buttonbar(index) for index, item in enumerate(self.iterable)];
        
    def _update_labels(self):
        [self._update_label(index) for index, item in enumerate(self.iterable)];

    def _update_rows(self):
        [self._update_row(index) for index, item in enumerate(self.iterable)];
        
    def _update_rows_box(self):
        self.rows_box.children = [i.row for i in self.iterable]
        
    @property
    def add_remove_controls(self):
        if self._add_remove_controls is None:
            return None
        else:
            return self._add_remove_controls#.value
    
    @add_remove_controls.setter
    def add_remove_controls(self, value: str):
        self._add_remove_controls = value
        self._update_buttonbars()
        self._init_controls()
        
    @property
    def show_hash(self):
        return self._show_hash
    
    @show_hash.setter
    def show_hash(self, value: str):
        self._show_hash = value
        self._update_labels() 
        
    @property
    def toggle(self):
        return self._toggle
    
    @toggle.setter
    def toggle(self, value: bool):
        self._toggle = value
        self.toggle_button.value = True
        self._update_header()
        
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, value: typing.Union[str, None]):
        self._title = value
        if self.title is None:
            self.html_title = widgets.HTML(self.title)
        else:
            self.html_title = widgets.HTML(markdown(self.title))
        self._update_header()
    
    def _update_header(self):
        header = []
        if self.toggle:
            header.append(self.toggle_button)
        if self.title is not None:
            header.append(self.html_title)
        self.title_box.children = header
        
    def _toggle_button(self, change):
        if self.toggle_button.value:
            self.toggle_button.icon = "minus"
            self.children = [self.title_box, self.rows_box]
        else:
            self.toggle_button.icon = "plus"
            self.children = [self.title_box]
            
    def _init_row_controls(self, key=None):
        if self.add_remove_controls == "append_only":
            self.iterable[0].add.on_click(self._add_row)
        else:
            self._get_attribute(key, 'add').on_click(functools.partial(self._add_row, key=key))
        self._get_attribute(key, 'remove').on_click(functools.partial(self._remove_rows, key=key))
        if self.watch_value:
            self._get_attribute(key, 'item').observe(self._update_value, names="value")

    def _init_controls(self):
        self.toggle_button.observe(self._toggle_button, "value")
        [self._init_row_controls(key=i.key) for i in self.iterable]
        # self._init_row_controls(item.key)  # TODO
        
    def _sort_iterable(self):
        if self.sort_on == 'index':
            sort = sorted(self.iterable, key=lambda k: k.index)
        elif self.sort_on == 'key':
            sort = sorted(self.iterable, key=lambda k: str(k.key))
        else:
            sort = self.iterable
        for n, s in enumerate(sort):
            s.index = n
        return sort
    
    def _get_attribute(self, key, get):
        return [getattr(r, get) for r in self.iterable if r.key == key][0]
    
    def _add_row(self, onclick, key=None):
        if self.fn_add_dialogue is None:
            self.add_row(key=key)
        else:
            out = widgets.Output()
            self.children =  [self.title_box, out, self.rows_box]
            with out:
                display(self.fn_add_dialogue(cls=self))
            
    
    def add_row(self, key=None, new_key=None, add_kwargs=None):
        """add row to array after key. if key=None then append to end"""
        if len(self.iterable) >= self.maxlen:
            print('len(self.iterable) >= self.maxlen')
            return None
        
        if add_kwargs is None:
            add_kwargs = {}
        if key is None: 
            if len(self.iterable) == 0:
                index = 0
            else:
                key = self.iterable[-1].key
                index = self._get_attribute(key, 'index') # append
        else:
            index = self._get_attribute(key, 'index')
            
        if new_key is not None:
            if new_key in [i.key for i in self.iterable]:
                print(f'{new_key} already exists in keys')
                return None
           
        # add item
        new_item = self.fn_add(**add_kwargs)
        item = IterableItem(
            index=index,
            key=new_key,
            item=new_item,
        )
        self.iterable.insert(index+1, item)
        self.iterable = self._sort_iterable()  # update map
        index = self._get_attribute(item.key, 'index')
        self._update_row(index)
        self._update_rows_box()
        self._init_row_controls(item.key)  # init controls
        if self.watch_value:
            self._update_value("change")
            
    def _remove_rows(self, onclick, key=None):
        if len(self.iterable) <= 1:
            pass
        else:
            n = self._get_attribute(key, 'index')
            self.iterable.pop(n)
            self.iterable = self._sort_iterable()
            if self.watch_value:
                self._update_value("change")
            self._update_rows_box()
            self._update_labels() 
            if n == 0:
                key = self.iterable[0].key
                self._init_row_controls(key=key)
                self._update_row(n)


    def remove_row(self, key=None, remove_kwargs=None):
        if key is None: 
            key = self.iterable[-1].key
        self._remove_rows("click", key=key)
        self.fn_remove(**remove_kwargs)
        
class Dictionary(Array):
    value = traitlets.Dict()
    
    def _update_value(self, onchange):
        self.value = {a.key: a.item.value for a in self.iterable}
        
    # -----------------------------------------------------------------------------------
    def __init__(
        self,
        items: typing.Dict=None,
        toggle=False,
        title=None,
        fn_add: typing.Callable = lambda: display("add item"),
        fn_add_dialogue: typing.Callable = None,
        fn_remove: typing.Callable = lambda: display("remove item"),
        watch_value: bool = True,
        minlen: int =1,
        maxlen: int =None,
        add_remove_controls: str ='add_remove',
        show_hash: str ='index',
        sort_on='index',
        orient_rows=True
    ):
        super().__init__(items,
            toggle=toggle,
            title=title,
            fn_add=fn_add,
            fn_add_dialogue=fn_add_dialogue,
            fn_remove=fn_remove,
            watch_value=watch_value,
            minlen=minlen,
            maxlen=maxlen,
            add_remove_controls=add_remove_controls,
            show_hash=show_hash,
            sort_on=sort_on,
            orient_rows=orient_rows
        )
    
    @property
    def items(self):
        return {i.key: i.item for i in self.iterable}
    
    def _init_iterable(self, items):
        return [
            IterableItem(
                index=n,
                key=k,
                add=widgets.Button(**ADD_BUTTON_KWARGS),
                remove=widgets.Button(**REMOVE_BUTTON_KWARGS),
                item=v,
            )
            for n, (k, v) in enumerate(items.items())
        ]
    
class AutoIterable:
    pass  # TODO: create AutoIterable class that works with the AutoUi class for iterables



# %%
if __name__ == "__main__":
    import random
    from IPython.display import Markdown

    def get_di():
        words = [
            "a",
            "AAA",
            "AAAS",
            "aardvark",
            "Aarhus",
            "Aaron",
            "ABA",
            "Ababa",
            "aback",
            "abacus",
            "abalone",
            "abandon",
            "abase",
        ]
        n = random.randint(0, len(words) - 1)
        m = random.randint(0, 1)
        _bool = {0: False, 1: True}
        return {words[n]: _bool[m]}

    def fn_add():
        return TestItem(di=get_di())

    class TestItem(widgets.HBox, traitlets.HasTraits):
        value = traitlets.Dict()

        def __init__(self, di: typing.Dict = get_di()):
            self.value = di
            self._init_form()
            self._init_controls()

        def _init_form(self):
            self._label = widgets.HTML(f"{list(self.value.keys())[0]}")
            self._bool = widgets.ToggleButton(list(self.value.values())[0])
            super().__init__(children=[self._bool, self._label])#self._acc, 

        def _init_controls(self):
            self._bool.observe(self._set_value, names="value")

        def _set_value(self, change):
            self.value = {self._label.value: self._bool.value}
            
    di_arr = {
        'items':[fn_add()],
        'fn_add':fn_add,
        'maxlen':10,
        'show_hash':'index',
        'toggle':True,
        'title':'Array',
        'add_remove_controls': 'append_only',
        'orient_rows':False
        
    }

    arr = Array(**di_arr)
    display(arr)


# %%
if __name__ == "__main__":
    di_di = {
        'items':{'key':fn_add()},
        'fn_add':fn_add,
        'maxlen':10,
        'show_hash':None,
        'toggle':True,
        'title':'Array',
        'add_remove_controls': 'append_only',
        'orient_rows':True
    }

    di = Dictionary(**di_di)
    display(di)

# %%
if __name__ == "__main__":
    di.add_remove_controls = 'add_remove'
    di.show_hash = 'index'
