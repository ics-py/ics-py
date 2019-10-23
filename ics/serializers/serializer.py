from typing import Callable


class Serializer:
    @classmethod
    def get_serializers(cls) -> Callable:
        methods = [
            (method_name, getattr(cls, method_name))
            for method_name in dir(cls)
            if callable(getattr(cls, method_name))
        ]
        return sorted([
            method_callable
            for (method_name, method_callable) in methods
            if method_name.startswith("serialize_")
        ], key=lambda x: x.__name__)
