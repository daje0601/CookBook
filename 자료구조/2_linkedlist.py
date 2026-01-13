class Node:
    def __init__(self, item, link):
        self.item = item 
        self.link = link

class SimpleList:
    def __init__(self):
        self.head = None 
        self.size = 0

    def size(self):
        return self.size 

    def is_empty(self):
        return self.size == 0 


    def insert_front(self, item):
        if self.is_empty() : 
            self.head = Node(item, None)
        else:
            self.head = Node(item, self.head)
        self.size += 1 

    def insert_after(self, item):
        pass 

    def delete_front(self, item):
        pass 

    def delete_after(self, item):
        pass 

    def display(self):
        if self.is_empty():
            print("리스트가 비어있습니다.")
            return 
        
        current = self.head
        items = [ ]
        while current:
            items.append(str(current.item))
            current = current.link
        print(" -> ".join(items))
Linkedlist = SimpleList()
Linkedlist.insert_front(2)
Linkedlist.insert_front(3)
Linkedlist.insert_front(4)

Linkedlist.display()