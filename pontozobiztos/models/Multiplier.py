class Multiplier:
    def __init__(self, value, typename, expiration_date):
        self.value = value
        self.type = typename
        self.expiration = expiration_date

    def __repr__(self):
        return str(self.__dict__)