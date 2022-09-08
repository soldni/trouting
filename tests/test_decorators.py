from typing import Any
from unittest import TestCase

from trouting import trouting


class TroutedClass:
    @trouting
    @classmethod
    def add_one(cls, a: Any) -> Any:
        raise TypeError(f"Type {type(a)} not supported for +1")

    @add_one.add_interface(a=int)
    @classmethod
    def add_one_int(cls, a: int) -> int:
        return a + 1

    @add_one.add_interface(a=str)
    @classmethod
    def add_one_str(cls, a: str) -> str:
        return a + "1"

    @trouting
    def add_two(self, a: Any) -> Any:
        raise TypeError(f"Type {type(a)} not supported for +2")

    @add_two.add_interface(a=int)
    def add_two_int(self, a: int) -> int:
        return a + 2

    @add_two.add_interface(a=str)
    def add_two_str(self, a: str) -> str:
        return a + "2"

    @trouting
    @staticmethod
    def add_three(a: Any) -> Any:
        raise TypeError(f"Type {type(a)} not supported for +3")

    @add_three.add_interface(a=int)
    @staticmethod
    def add_three_int(a: int) -> int:
        return a + 3

    @add_three.add_interface(a=str)
    @staticmethod
    def add_three_str(a: str) -> str:
        return a + "3"


class TestDecorators(TestCase):
    def test_classmethod(self):
        self.assertEqual(TroutedClass.add_one(1), 2)
        self.assertEqual(TroutedClass.add_one("1"), "11")

    def test_instance_method(self):
        self.assertEqual(TroutedClass().add_two(1), 3)
        self.assertEqual(TroutedClass().add_two("1"), "12")

    def test_staticmethod(self):
        # TODO[soldni]: need to fix typing annotation for trouting
        # so that pylance doesn't freak out when using staticmethod
        self.assertEqual(TroutedClass.add_three(1), 4)  # pyright: ignore
        self.assertEqual(TroutedClass.add_three("1"), "13")  # pyright: ignore

    def test_raise_error_uneven_interfaces(self):
        class _:
            @trouting
            @classmethod
            def add_one(cls, a: Any) -> Any:
                raise TypeError(f"Type {type(a)} not supported for +1")

            with self.assertRaises(TypeError):

                @add_one.add_interface(a=int)
                def add_one_int(cls, a: int) -> int:
                    return a + 1

            with self.assertRaises(TypeError):
                # Type ignore because this is intentionally wrong
                @add_one.add_interface(a=str)  # type: ignore
                @staticmethod
                def add_one_str(a: str) -> str:
                    return a + "1"
