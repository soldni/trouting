import inspect
from dataclasses import MISSING
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
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

    bounded_args: Union[Tuple[str, ...], None]
    interfaces: Dict[Tuple[type, ...], Callable[Concatenate[Any, P], R]]

    def __init__(
        self, fallback_method: Callable[Concatenate[Any, P], R]
    ) -> None:
        """Create an Interface object.

        Args:
            interfaced_method: The method to be interfaced; it is also the
                default method if no matching interface is found.
        """
        self.interfaces = {}
        self.bounded_args = None
        self.fallback_method = fallback_method
        self.is_descriptor = inspect.ismethoddescriptor(fallback_method)

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

        if self.bounded_args is None:
            self.bounded_args = current_interface_args
        elif self.bounded_args != current_interface_args:
            raise TypeError(
                "All interfaces must have the same arguments; the current "
                f"interface has arguments {current_interface_args}, but the "
                f"previous interface has arguments {self.bounded_args}"
            )

        def _add_interface(
            method: Callable[Concatenate[Any, P], R]
        ) -> "trouting":
            if self.is_descriptor:
                if not inspect.ismethoddescriptor(method):
                    raise TypeError(
                        "All interfaces must be descriptors; the current "
                        "interface is a function."
                    )
                elif not isinstance(self.fallback_method, type(method)):
                    raise TypeError(
                        "All interfaces must be of the same type; the current "
                        f"interface is a {type(method)}, but the previous "
                        f"interface is {type(self.fallback_method)}."
                    )

            for interface_spec in interface_specs:
                # register the same method for all types in the interface spec
                # have to add an ignore because pyright is being a bit too
                # clever here.
                self.interfaces[  # pyright: ignore
                    tuple(interface_spec.values())
                ] = method

            return self

        return _add_interface

    def __get__(self, obj: Any, type: Any) -> Callable[Concatenate[P], R]:
        """Return a bound method that calls the correct interface."""
        return partial(
            self.__call__, __trouting_obj__=obj, __trouting_type__=type
        )

    def _bound_method(self, method: Any, obj: Any, cls: Any) -> Callable:
        if self.is_descriptor:
            bound_method = method.__get__(obj, cast(type, cls))
        else:
            # populate the first argument with the object or class here
            bound_method = partial(method, obj or cls)
        return bound_method

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Call the interfaced method with the correct interface."""

        if (
            __trouting_obj__ := kwargs.pop("__trouting_obj__", MISSING)
        ) is MISSING:
            raise ValueError(
                "__trouting_obj__ is required; `Interface._run_interface` "
                "was improperly called; You might have called a trouted "
                "method in an invalid way; If you think you are using this "
                "library correctly, please file a bug report."
            )
        if (
            __trouting_type__ := kwargs.pop("__trouting_type__", MISSING)
        ) is MISSING:
            raise ValueError(
                "__trouting_type__ is required; `Interface._run_interface` "
                "was improperly called; You might have called a trouted "
                "method in an invalid way; If you think you are using this "
                "library correctly, please file a bug report."
            )

        bounded_fallback_method = self._bound_method(
            self.fallback_method, __trouting_obj__, __trouting_type__
        )

        sig_vals = inspect.signature(bounded_fallback_method).bind(
            *args, **kwargs
        )

        current_types = tuple(
            type(sig_vals.arguments[arg_name])
            for arg_name in (self.bounded_args or tuple())
        )

        method_to_call = self.interfaces.get(current_types, None)
        if method_to_call is None:
            method_to_call = bounded_fallback_method
        else:
            method_to_call = self._bound_method(
                method_to_call, __trouting_obj__, __trouting_type__
            )

        return method_to_call(*args, **kwargs)
