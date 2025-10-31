from Queue import CircularQueue

class Product:
    def __init__(self,name,url,data):
        self.name=name
        self.url=url
        self.data=data
        current = CircularQueue.get_last(data)
        change = CircularQueue.find_daily_diff(data)
        max_change = CircularQueue.find_max_diff(data)

