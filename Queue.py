class CircularQueue:
    def __init__(self, size):
        self.size = size
        self.queue = [None] * size
        self.front = self.rear = -1

    def enqueue(self, value):
        if (self.rear + 1) % self.size == self.front:
            print("Queue is full!")
            return

        if self.front == -1:
            self.front = 0

        self.rear = (self.rear + 1) % self.size
        self.queue[self.rear] = value

    def dequeue(self):
        if self.front == -1:
            print("Queue is empty!")
            return None

        value = self.queue[self.front]

        if self.front == self.rear:
            self.front = self.rear = -1
        else:
            self.front = (self.front + 1) % self.size

        return value

    def find_max_diff(self):
        global max, min
        if self.front == -1:
            print("Queue is empty")
            return None

        i = self.front
        while True:
            if self.queue[i]>=max:
                max = self.queue[i]
            if self.queue[i]<=min:
                min = self.queue[i]
            if i == self.rear:
                break
            i = (i + 1) % self.size
        return max-min

    def find_daily_diff(self):
        if self.front == -1:
            print("Queue is empty")
            return 0

        if self.front == self.rear:
            return 0

        prev = self.queue[self.rear - 1]
        curr = self.queue[self.rear]

        if prev in (None, 0):
            return 0

        return int(100-(curr * 100 / prev))

    def get_last(self):
        return self.queue[self.rear]

    def display(self):
        if self.front == -1:
            print("Queue is empty")
            return

        print("Queue contents:", end=" ")
        i = self.front
        while True:
            print(self.queue[i], end=" ")
            if i == self.rear:
                break
            i = (i + 1) % self.size
        print()