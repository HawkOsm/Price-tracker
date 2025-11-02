class CircularQueue:
    def __init__(self, size):
        assert size > 0
        self.size = size
        self.queue = [None] * size
        self.front = 0       # index of the oldest element
        self.count = 0       # how many valid elements (0..size)

    # add newest; overwrite oldest when full
    def enqueue(self, value):
        insert = (self.front + self.count) % self.size
        self.queue[insert] = value
        if self.count == self.size:
            self.front = (self.front + 1) % self.size   # drop oldest
        else:
            self.count += 1

    def dequeue(self):
        if self.count == 0:
            return None
        v = self.queue[self.front]
        self.front = (self.front + 1) % self.size
        self.count -= 1
        return v

    def _idx(self, i_from_oldest):
        # helper: 0 is oldest, count-1 is newest
        return (self.front + i_from_oldest) % self.size

    def get_last(self):
        if self.count == 0:
            return None
        return self.queue[self._idx(self.count - 1)]

    def find_max_diff(self):
        if self.count == 0:
            return None
        max_price = float("-inf")
        min_price = float("inf")
        for i in range(self.count):
            v = self.queue[self._idx(i)]
            if v is None:
                continue
            if v > max_price: max_price = v
            if v < min_price: min_price = v
        if max_price == float("-inf"):   # all None
            return None
        return max_price - min_price

    def find_daily_diff(self):
        # percentage change from previous to latest: positive means drop
        if self.count < 2:
            return 0
        prev = self.queue[self._idx(self.count - 2)]
        curr = self.queue[self._idx(self.count - 1)]
        if prev in (None, 0):
            return 0
        return int(100 - (curr * 100 / prev))

    def display(self):
        if self.count == 0:
            print("Queue is empty")
            return
        print("Queue contents:", end=" ")
        for i in range(self.count):
            print(self.queue[self._idx(i)], end=" ")
        print()
