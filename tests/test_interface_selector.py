import unittest
from typing import Any, Type


from trouting.trouting import route


class Mapper:
    """
    InterfaceMapper is a base class for all interface mappers.
    """

    @route
    def map(self, value: Any) -> Type[Any]:
        raise NotImplementedError()

    @map.add_interface(value=list)  # type: ignore
    def map_list(self, value: list) -> Type[list]:
        return list

    @map.add_interface(value=dict)  # type: ignore
    def map_dict(self, value: dict) -> Type[dict]:
        return dict


class Mapper2(Mapper):
    @route
    def map(self, value: Any) -> Type[Any]:
        return super().map(value)

    @map.add_interface(value=int)  # type: ignore
    def map_int(self, value: int) -> Type[int]:
        return int


class TestInterface(unittest.TestCase):
    def test_base_interface(self):
        mapper: Mapper = Mapper()

        value = ["a", "b", "c"]
        self.assertEqual(mapper.map(value), list)

        value = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(mapper.map(value), dict)

        with self.assertRaises(NotImplementedError):
            mapper.map(1)

    def test_inherited_interface(self):
        mapper: Mapper2 = Mapper2()

        value = ["a", "b", "c"]
        self.assertEqual(mapper.map(value), list)

        value = 1
        self.assertEqual(mapper.map(value), int)
