# +
import ipywidgets as w
from pydantic import ValidationError
import traitlets as tr
import json
import logging

from ipyautoui.watch_validate import pydantic_validate

logger = logging.getLogger(__name__)

# +
class JsonableDict(w.VBox):
    _value = tr.Dict() # allow_none=True, default_value={}

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, str):
            self.text.value = value
        elif isinstance(value, dict):
            self.text.value = json.dumps(value)
        elif value is None:
            pass
        else:
            raise ValueError(f"value must be a dict or jsonable string, not {value}")
            

    def __init__(self, **kwargs):
        value = kwargs.get("value")
        kwargs = {k:v for k, v in kwargs.items() if k != "value"}
        self.text = w.Textarea(**kwargs)
        self.out = w.Output()
        self.html = w.HTML()
        super().__init__()
        self.children = [self.text, self.html]
        self._init_controls()
        self.value = value

    def _init_controls(self):
        self.text.observe(self._update, "value")
        


    def _update(self, on_change):
        try: 
            jsonable_dict = json.loads(self.text.value)
            self.text.layout.border = 'solid 2px green'
            self._value = jsonable_dict
            self.html.value = f"<code>{self.value}</code>"
        except Exception as e:
            self.text.layout.border = 'solid 2px red'
            self.html.value = "<code>not valid json</code>"
            logger.info(e)

class JsonableModel(JsonableDict):
    _value = tr.Union([tr.List(), tr.Dict()])
    
    model = tr.Type(klass=object, default_value=None, allow_none=True)
    has_error = tr.Bool(default_value=False)

    def __init__(self, model=None, **kwargs):
        self.model = model
        super().__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, str):
            self.text.value = value
        elif isinstance(value, dict) or isinstance(value, list):
            self.text.value = json.dumps(value)
        elif value is None:
            pass
        else:
            self.has_error = True
            raise ValueError(f"value must be a dict or jsonable string, not {value}")
        self.has_error = False

    def _update(self, on_change):
        try:
            jsonable_dict = json.loads(self.text.value)
            if self.model is not None:
                # Validate against the pydantic model
                validated_value = pydantic_validate(self.model, jsonable_dict)
                self.text.layout.border = 'solid 2px green'
                self._value = validated_value
                self.html.value = f"<code>{self.value}</code>"
                self.has_error = False
            else:
                # No model, just validate JSON
                self.text.layout.border = 'solid 2px green'
                self._value = jsonable_dict
                self.html.value = f"<code>{self.value}</code>"
                self.has_error = False
        except ValidationError as e:
            self.has_error = True
            self.text.layout.border = 'solid 2px red'
            self.html.value = f"<code>Validation Error: {str(e)}</code>"
            logger.info(e)
        except Exception as e:
            self.has_error = True
            self.text.layout.border = 'solid 2px red'
            self.html.value = "<code>not valid json</code>"
            logger.info(e)


# -

if __name__ == "__main__":
    from IPython.display import display
    jd = JsonableDict(value={"b": 12})
    display(jd)
if __name__ == "__main__":
    display(jd.value) 

if __name__ == "__main__":
    jd.value = {"a": [1,2,3]}


