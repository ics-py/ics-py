from typing import Callable


class Serializer:
    @classmethod
    def get_serializers(cls) -> Callable:
        methods = dir(cls)
        return [m for m in methods if m.__name__.startswith('serialize_') ]
