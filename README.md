# Trouting

![](https://github.com/soldni/trouting/raw/main/static/logo.png)

Trouting (short for Type Routing) is a simple class decorator that allows to define multiple interfaces for a method that behave differently depending on input types.

To install for PyPI trouting, run:

```bash
pip install trouting
```

The logo of trouting was generated using [Stable Diffusion](https://github.com/CompVis/stable-diffusion) with prompt *"A Kandinsky painting titled The Trout Who Routes"* and slightly edited by the author.

## Example

Imagine you want to define a class whose method behaves differently depending on whether the input is a string or an integer. You can do this with trouting as follows:

```python
from trouting import trouting
class MyClass:
    @Interface
    def add_one(self, a: Any) -> Any:
        # fallback method
        raise TypeError(f"Type {type(a)} not supported")

    @add_one.add_interface(a=int)
    def add_one_int(self, a: int) -> int:
        # a is an int
        return a + 1

    @add_one.add_interface(a=str)
    def add_one_str(self, a: str) -> str:
        # a is a str
        return a + "1"
```

Now, when using `MyClass`, the method `add_one` will behave differently depending on the input type:

```python
my_class = MyClass()
my_class.add_one(1) # returns 2
my_class.add_one("1") # returns "11"
my_class.add_one([1]) # raises TypeError
```
