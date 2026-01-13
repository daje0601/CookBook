# 알고리즘 : 문제를 해결하는 절차적 방법 

class SimpleList:
    class Node:
        def __init__(self, item, link):
            self.item = item 
            self.link = link

    def __init__(self):
        self.head = None 
        self.size = 0

    def size(self):
        return self.size 

    def is_empty(self):
        return self.size == 0 


    def insert_front(self, item):
        if self.is_empty() : 
            self.head = self.Node(item, None)
        else:
            self.head = self.Node(item, self.head)
        self.size += 1 

    def insert_after(self, item, previous):
        """노드2 -> 노드3 인데, 2와 3 사이에 넣고 싶은거 잖아. 
        노드#을 노드2 와 노드 3 사이에 넣고 싶거든. 
        노드# 뒤에 노드3을 연결해야해 
        노드2에 노드 # 을 연결해야해. 그럼 되거든. 
        일단 노드 #을 만들어야하니까 self.Node(item, next)는 필요하지 
        노드# 의 다음 노드를 만든 노드에 연결해야지 그래서 self.Node(item, previous.next)
        이걸 이전 노드에 연결해야지 """
        previous.next = self.Node(item, previous.next)



    def delete_front(self, item):
        pass 

    def delete_after(self, item):
        pass 

    def search(self, target):
        # 몇번째 노드에 target이 있는지 찾은건가?
        p = self.head

        for index in range(self.size):
            if target == p.item: 
                return index 
            else: 
                p = p.next 

    def display(self):
        if self.is_empty():
            print("리스트가 비어있습니다.")
            return 
        
        current = self.head
        items = []
        while current:
            items.append(str(current.item))
            current = current.link
        print(" -> ".join(items))
Linkedlist = SimpleList()
Linkedlist.insert_front(2)
Linkedlist.insert_front(3)
Linkedlist.insert_front(4)

Linkedlist.display()