class Point:
    def __init__(self, value, source, timestamp, description, mid):
        self.value = value
        self.source = source
        self.timestamp = timestamp
        self.description = description
        self.mid = mid

    def __repr__(self):
        return str(self.__dict__)
