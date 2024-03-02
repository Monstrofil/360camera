# from types import NoneType
from types import NoneType

import pydantic


return_model = pydantic.create_model(
            'test',
            **{
                "value": (NoneType, ...),
            },
        )


print(return_model(value=None))
