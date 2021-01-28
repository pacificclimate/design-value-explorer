from pickle import PickleBuffer


class Thing:
    def __init__(self, greeting, target):
        self.greeting = greeting
        self.target = target

    def __str__(self):
        return f"<Thing {self.greeting}, {self.target}>"


class ZeroCopyThing(Thing):
    def __reduce_ex__(self, protocol):
        if protocol >= 5:
            return type(self)._reconstruct, (PickleBuffer(self),), None
        else:
            # PickleBuffer is forbidden with pickle protocols <= 4.
            return type(self)._reconstruct, (bytearray(self),)

    @classmethod
    def _reconstruct(cls, obj):
        with memoryview(obj) as m:
            # Get a handle over the original buffer object
            obj = m.obj
            if type(obj) is cls:
                # Original buffer object is a ZeroCopyByteArray, return it
                # as-is.
                return obj
            else:
                return cls(obj)
