import inspect
from dataclasses import MISSING
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


class trouting(Generic[P, R]):
    """An interface is a decorator that select the correct method to call
    based on the types of the arguments. For example, in the class below,
    the method `add_one` is customized for the type `int` and `str`, but
    fails for any other type of `a`.

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
    """

    bounded_args: Tuple[str, ...]
    interfaces: Dict[Tuple[type, ...], Callable[Concatenate[Any, P], R]]

    def __init__(
        self, interfaced_method: Callable[Concatenate[Any, P], R]
    ) -> None:
        """Create an Interface object.

        Args:
            interfaced_method: The method to be interfaced; it is also the
                default method if no matching interface is found.
        """
        self.interfaces = {}
        self._interfaced_method = interfaced_method
        self._method_signature = inspect.signature(interfaced_method)
        self._obj = None

    def _expand_interface_combinations(
        self, nested_interface_spec: Dict[str, Union[type, Tuple[type, ...]]]
    ) -> Sequence[Dict[str, type]]:
        """Expand an interface spec with multiple types per argument into
        multiple interface specs with a single type per argument."""

        expanded_interfaces: Sequence[Dict[str, type]] = [{}]
        for interface_args, interface_types in sorted(
            nested_interface_spec.items(), key=lambda x: x[0]
        ):
            if isinstance(interface_types, type):
                interface_types = (interface_types,)

            expanded_interfaces = [
                {**interface, interface_args: interface_type}
                for interface in expanded_interfaces
                for interface_type in interface_types
            ]

        return expanded_interfaces

    def add_interface(
        self, **kwargs: Union[type, Tuple[type, ...]]
    ) -> Callable[[Callable[Concatenate[Any, P], R]], "trouting"]:
        """Add an interface to the Interface for specific arguments and types.

        Args:
            **kwargs: The arguments and types to add an interface for.
                the key is the argument name, the value is the type.
        """

        interface_specs = self._expand_interface_combinations(kwargs)
        current_interface_args = tuple(interface_specs[0].keys())

        if not hasattr(self, "bounded_args"):
            self.bounded_args = current_interface_args
        elif self.bounded_args != current_interface_args:
            raise ValueError(
                "All interfaces must have the same arguments; the current "
                f"interface has arguments {current_interface_args}, but the "
                f"previous interface has arguments {self.bounded_args}"
            )

        def _add_interface(
            method: Callable[Concatenate[Any, P], R]
        ) -> "trouting":
            for interface_spec in interface_specs:
                # register the same method for all types in the interface spec
                self.interfaces[tuple(interface_spec.values())] = method
            return self

        return _add_interface

    def __get__(
        self, obj: Any, type: Optional[Type] = None
    ) -> Callable[Concatenate[P], R]:
        """Return a bound method that calls the correct interface."""
        return partial(self.__call__, __obj__=obj)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Call the interfaced method with the correct interface."""

        if (obj := kwargs.pop("__obj__", MISSING)) is MISSING:
            raise ValueError(
                "__obj__ is required; `Interface._run_interface` "
                "was improperly called; You might have called a trouted "
                "method in an invalid way; If you think you are using this "
                "library correctly, please file a bug report."
            )

        sig_vals = self._method_signature.bind(self, *args, **kwargs)
        method_to_call = None

        current_types = (
            type(sig_vals.arguments[arg_name])
            for arg_name in self.bounded_args
        )

        # fall back to the default method if we didn't find anything
        method_to_call = self.interfaces.get(
            tuple(current_types), self._interfaced_method
        )

        return method_to_call(obj, *args, **kwargs)
