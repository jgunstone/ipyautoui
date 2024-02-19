# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import typing as ty
from multiprocessing.pool import Pool
from ipyautoui.custom.svgspinner import SvgSpinner
import ipywidgets as w
import traitlets as tr
from ipyautoui.custom.selectandclick import SelectMultipleAndClick, FormLayouts
from ipyautoui.constants import PLAY_BUTTON_KWARGS

def pool_runner(tasks, callback=None):
    with Pool() as pool:
        results = [pool.apply_async(task, callback=callback) for task in tasks]
        pool.close()
        pool.join()


class ExecuteTasks(w.VBox):
    """NOTE: callable must not be a lambda fn"""
    tasks = tr.Union([
        tr.List(trait=tr.TraitType(tr.Callable())), 
        tr.Dict(value_trait=tr.TraitType(tr.Unicode(), tr.Callable()))
    ], default_value = {})
    task_names = tr.List(trait=tr.Unicode())
    runner = tr.Callable(default_value = pool_runner)

    @tr.observe("tasks")
    def obs_tasks(self, on_change):
        self.progress.max = self.end
        li = []
        self.spinners = [SvgSpinner() for n in range(self.end)]
        li.append(self.spinners)
        task_names = self.task_names
        if task_names is not None:
            li.append([w.HTML(task+ " |") for task in task_names])
        self.results = [w.HTML() for _ in range(self.end)]
        li.append(self.results)
        self.vbx_tasks.children = [w.HBox(l) for l in zip(*li)]
    
    def __init__(
        self, **kwargs
    ):
        
        if "task_names" not in kwargs:
            kwargs["task_names"] = ["" for _ in range(self.end)]
        self.progress = w.IntProgress(min=0, step=1)
        self.vbx_tasks = w.VBox()
        super().__init__(**kwargs)
        self.children = [self.progress, self.vbx_tasks]


    def start(self):
        self.runner(self.callables, callback=self.callback)

    @property
    def end(self):
        return len(self.tasks)

    @property
    def callables(self):
        if isinstance(self.tasks, list):
            return self.tasks
        else:
            return list(self.tasks.values())
            
    @property 
    def task_names(self):
        if isinstance(self.tasks, list):
            return None
        else:
            return list(self.tasks.keys())
            
    def callback(self, result):
        n = self.progress.value
        self.spinners[n].complete = True
        self.results[n].value = str(result)
        self.progress.value += 1

if __name__ == "__main__":
    from random import random
    from time import sleep
    import functools
    def task():
        t = random() * 2
        sleep(t)
        return f"sleep: {t}"

    def test(s):
        return s
    END = 1
    tasks = {f"task-{_}" : task for _ in range(END)}
    tasks = {f"task-{_}" : functools.partial(test, "asdf") for _ in range(END)}
    ex = ExecuteTasks(tasks=tasks)
    display(ex)
    ex.start()


# %%
class SelectAndExecute(w.HBox):
    title = tr.Unicode()
    tasks = tr.Dict(value_trait=tr.TraitType(tr.Unicode(), tr.Callable()), default_value={})

    @tr.observe("title")
    def obs_title(self, on_change):
        self.select.title = self.title 
        
    @tr.observe("tasks")
    def obs_tasks(self, on_change):
        self.select.select.options = self.tasks.keys()

        def get_select_height(self):
            h = len(self.tasks)*100 / 5.8 
            if h < 100: 
                return 100
            elif h > 600:
                return 600
            else:
                return h
            

        self.select.select.layout.height = f"{get_select_height(self)}px"
    
    def __init__(self, **kwargs):
        self.execute = ExecuteTasks()
        self.select = SelectMultipleAndClick(fn_onclick=self.fn_onclick, fn_layout_form=FormLayouts.align_vertical_left)
        self.select.hbx_message.layout.display = "None"
        {setattr(self.select.bn, k, v) for k, v in PLAY_BUTTON_KWARGS.items()}
        {setattr(self.select, k, v) for k, v in kwargs.items() if k in self.select.traits()}
        super().__init__(**kwargs)
        self.children = [self.select, self.execute]

    def fn_onclick(self, onclick):
        self.execute.progress.value = 0
        self.execute.tasks = {k:v for k, v in self.tasks.items() if k in self.select.select.value}
        self.execute.progress.max = self.execute.end
        self.execute.vbx_tasks.layout.display = ""
        
        self.execute.start()

if __name__ == "__main__":
    from random import random
    from time import sleep

    def task():
        t = random() * 2
        sleep(t)
        return f"sleep: {t}"
    
    END = 20
    tasks = {f"task-{_}" : task for _ in range(END)}
    se = SelectAndExecute(tasks=tasks, title="<b>Generate Selected Schedules</b>")
    display(se)

# %%
if __name__ == "__main__":
    from random import random
    from time import sleep

    def task():
        t = random() * 2
        sleep(t)
        return f"sleep: {t}"
    
    END = 20
    tasks = {f"task-{_}" : task for _ in range(END)}
    se = SelectAndExecute( title="<b>Generate Selected Schedules</b>")
    display(se)

# %%
if __name__ == "__main__":
    se.tasks=tasks

# %%

# %%

# %%

# %%
