from json import JSONEncoder


class CustomEncoder(JSONEncoder):
    def default(self, o):
        if getattr(o, 'json_serializable', None):
            return o.json_serializable()
        return JSONEncoder.default(self, o)
