import unittest
from typing import Any, Union

from trouting.core import trouting


class Mapper:
    """
    InterfaceMapper is a base class for all interface mappers.
    """

    @trouting
    def map(self, value: Any) -> float:
        raise NotImplementedError(str(type(value)))

    @map.add_interface(value=(int, float))
    def map_number(self, value: Union[int, float]) -> float:
        return float(value)

    @map.add_interface(value=str)
    def map_str(self, value: str) -> float:
        return float(value)


class TestMultipleTypes(unittest.TestCase):
    def test_multiple_types(self):
        mapper: Mapper = Mapper()

        value = 1
        resp = mapper.map(value)
        self.assertEqual(resp, 1.0)
        self.assertEqual(type(resp), float)

        value = 1.0
        resp = mapper.map(value)
        self.assertEqual(resp, 1.0)
        self.assertEqual(type(resp), float)

        value = "1"
        resp = mapper.map(value)
        self.assertEqual(resp, 1.0)
        self.assertEqual(type(resp), float)

        with self.assertRaises(NotImplementedError):
            value = "1".encode("utf-8")
            mapper.map(value)
