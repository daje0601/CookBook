class Node:
    """이중연결리스트의 노드 클래스"""
    def __init__(self, elem, prev, next):
        self.elem = elem  # 노드가 저장하는 데이터 (영문자)
        self.prev = prev  # 이전 노드를 가리키는 포인터
        self.next = next  # 다음 노드를 가리키는 포인터

class DoublyLinkedList:
    """이중연결리스트 클래스 - 비더미 구조 (head와 tail이 실제 데이터 노드)"""
    def __init__(self):
        # 비더미 구조: 빈 리스트일 때 head와 tail이 None
        self.head = None
        self.tail = None
        
        # 리스트의 실제 데이터 노드 개수
        self.size = 0
    
    def add(self, r, e):
        """순위 r(1부터 시작)에 원소 e를 추가하는 메서드"""
        
        # 유효성 검사: r은 1부터 size+1까지 가능
        if r < 1 or r > self.size + 1:
            print("invalid position")
            return
        
        # 새 노드 생성
        new_node = Node(e, None, None)
        
        # 경우 1: 빈 리스트에 첫 노드 추가
        if self.size == 0:
            self.head = new_node
            self.tail = new_node
        
        # 경우 2: 맨 앞에 추가 (r == 1)
        elif r == 1:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        
        # 경우 3: 맨 뒤에 추가 (r == size + 1)
        elif r == self.size + 1:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        
        # 경우 4: 중간에 추가
        else:
            # r번째 위치의 노드 찾기
            curr = self.head
            for _ in range(r - 1):
                curr = curr.next
            
            # new_node를 curr 앞에 삽입
            new_node.prev = curr.prev
            new_node.next = curr
            curr.prev.next = new_node
            curr.prev = new_node
        
        self.size += 1
    
    def delete(self, r):
        """순위 r(1부터 시작)의 원소를 삭제하는 메서드"""
        
        # 유효성 검사: r은 1부터 size까지만 가능
        if r < 1 or r > self.size:
            print("invalid position")
            return
        
        # 삭제할 r번째 노드 찾기
        curr = self.head
        for _ in range(r - 1):
            curr = curr.next
        
        # 경우 1: 노드가 하나뿐일 때
        if self.size == 1:
            self.head = None
            self.tail = None
        
        # 경우 2: 첫 번째 노드 삭제
        elif curr == self.head:
            self.head = curr.next
            self.head.prev = None
        
        # 경우 3: 마지막 노드 삭제
        elif curr == self.tail:
            self.tail = curr.prev
            self.tail.next = None
        
        # 경우 4: 중간 노드 삭제
        else:
            curr.prev.next = curr.next
            curr.next.prev = curr.prev
        
        self.size -= 1
    
    def get_entry(self, r):
        """순위 r(1부터 시작)의 원소를 출력하는 메서드"""
        
        # 유효성 검사: r은 1부터 size까지만 가능
        if r < 1 or r > self.size:
            print("invalid position")
            return
        
        # r번째 노드 찾기
        curr = self.head
        for _ in range(r - 1):
            curr = curr.next
        
        # r번째 노드의 데이터 출력
        print(curr.elem)
    
    def print_list(self):
        """리스트의 모든 원소를 저장 순위대로 공백없이 출력하는 메서드"""
        
        # 빈 리스트인 경우
        if self.head is None:
            print('')
            return
        
        # head부터 시작
        curr = self.head
        result = []
        
        # tail까지 순회
        while curr is not None:
            result.append(curr.elem)
            curr = curr.next
        
        # 리스트의 모든 문자를 공백 없이 연결하여 출력
        print(''.join(result))


def main():
    """메인 함수 - 사용자 입력을 받아 연산 수행"""
    
    # 첫 번째 줄: 수행할 연산의 총 개수 입력
    n = int(input())
    
    # 이중연결리스트 객체 생성
    dll = DoublyLinkedList()
    
    # n개의 연산을 순차적으로 처리
    for _ in range(n):
        # 한 줄을 입력받아 공백으로 분리
        operation = input().split()
        
        # 빈 입력 처리
        if len(operation) == 0:
            continue
        
        # 첫 번째 문자로 연산 종류 판별
        if operation[0] == 'A':  # Add 연산
            if len(operation) >= 3:
                r = int(operation[1])
                e = operation[2]
                dll.add(r, e)
        
        elif operation[0] == 'D':  # Delete 연산
            if len(operation) >= 2:
                r = int(operation[1])
                dll.delete(r)
        
        elif operation[0] == 'G':  # Get entry 연산
            if len(operation) >= 2:
                r = int(operation[1])
                dll.get_entry(r)
        
        elif operation[0] == 'P':  # Print list 연산
            dll.print_list()


# 프로그램 시작점
if __name__ == "__main__":
    main()