from dataclasses import dataclass
from typing import Dict, Any, Optional

from generators import generate_metal
from metal import Metal
from rarity import Rarity


@dataclass
class ResourceRecord:
    id: int
    data: Any


class Resources:
    _lastIndex: int = -1
    _data: Dict[int, Any] = {}

    def register(self, resource: Any) -> ResourceRecord:
        index = self._lastIndex + 1
        self._data[index] = resource
        self._lastIndex = index
        return ResourceRecord(index, resource)

    def findById(self, rid: int) -> Optional[Any]:
        return self._data[rid]

    def findByData(self, data: Any) -> Optional[ResourceRecord]:
        for key, res_data in self._data.items():
            if res_data == data:
                return ResourceRecord(key, res_data)
        return None

    def get_metals(self):
        return [ResourceRecord(key, data) for key, data in self._data.items() if isinstance(data, Metal)]


generator_conf = {
    "metals": {
        Rarity.COMMON: 5,
        Rarity.RARE: 3
    }
}


def generate_resources() -> Resources:
    res = Resources()
    for rarity, count in generator_conf["metals"].items():
        for i in range(0, count):
            res.register(generate_metal(rarity, 1))
    print(res.get_metals())
    return res
