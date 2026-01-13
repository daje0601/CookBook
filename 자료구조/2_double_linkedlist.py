class Node:
    """이중연결리스트의 노드 클래스"""
    def __init__(self, elem, prev, next):
        self.elem = elem  # 노드가 저장하는 데이터 (영문자)
        self.prev = prev  # 이전 노드를 가리키는 포인터
        self.next = next  # 다음 노드를 가리키는 포인터

class DoublyLinkedList:
    """이중연결리스트 클래스 - head와 tail 더미 노드 사용"""
    def __init__(self):
        # 더미 노드 생성 과정 (3단계)
        # 1. head 더미 노드 생성 (데이터=None, prev=None, next=None)
        self.head = Node(None, None, None)
        
        # 2. tail 더미 노드 생성 (데이터=None, prev=head를 가리킴, next=None)
        self.tail = Node(None, self.head, None)
        
        # 3. head의 next가 tail을 가리키도록 설정 (양방향 연결 완성)
        #    결과: head <-> tail 형태로 연결됨
        self.head.next = self.tail
        
        # 리스트의 실제 데이터 노드 개수 (더미 노드 제외)
        self.size = 0
    
    def add(self, r, e):
        """순위 r(1부터 시작)에 원소 e를 추가하는 메서드"""
        
        # 유효성 검사: r은 1부터 size+1까지 가능
        # size+1은 맨 끝에 추가하는 경우를 허용
        if r < 1 or r > self.size + 1:
            print("invalid position")
            return
        
        # r번째 위치 찾기
        # curr는 새 노드가 삽입될 위치의 노드를 가리킴
        # 예: r=2일 때, head -> 1번노드 -> 2번노드(curr)
        curr = self.head
        for _ in range(r):
            curr = curr.next
        
        # 새 노드를 curr 바로 앞에 삽입
        # new_node의 prev는 curr의 이전 노드를, next는 curr를 가리킴
        new_node = Node(e, curr.prev, curr)
        
        # curr의 이전 노드가 new_node를 가리키도록 설정
        curr.prev.next = new_node
        
        # curr의 prev가 new_node를 가리키도록 설정
        # 결과: ... <-> curr.prev <-> new_node <-> curr <-> ...
        curr.prev = new_node
        
        # 리스트 크기 1 증가
        self.size += 1
    
    def delete(self, r):
        """순위 r(1부터 시작)의 원소를 삭제하는 메서드"""
        
        # 유효성 검사: r은 1부터 size까지만 가능 (빈 리스트면 삭제 불가)
        if r < 1 or r > self.size:
            print("invalid position")
            return
        
        # 삭제할 r번째 노드 찾기
        # head.next부터 시작 (첫 번째 실제 데이터 노드)
        curr = self.head.next
        for _ in range(r - 1):  # r-1번 이동하면 r번째 노드 도달
            curr = curr.next
        
        # curr 노드를 리스트에서 제거
        # curr의 이전 노드가 curr의 다음 노드를 가리키도록 설정
        curr.prev.next = curr.next
        
        # curr의 다음 노드가 curr의 이전 노드를 가리키도록 설정
        # 결과: ... <-> curr.prev <-> curr.next <-> ...
        # (curr는 연결에서 제외됨)
        curr.next.prev = curr.prev
        
        # 리스트 크기 1 감소
        self.size -= 1
    
    def get_entry(self, r):
        """순위 r(1부터 시작)의 원소를 출력하는 메서드"""
        
        # 유효성 검사: r은 1부터 size까지만 가능
        if r < 1 or r > self.size:
            print("invalid position")
            return
        
        # r번째 노드 찾기
        # head.next부터 시작 (첫 번째 실제 데이터 노드)
        curr = self.head.next
        for _ in range(r - 1):  # r-1번 이동하면 r번째 노드 도달
            curr = curr.next
        
        # r번째 노드의 데이터 출력
        print(curr.elem)
    
    def print_list(self):
        """리스트의 모든 원소를 저장 순위대로 공백없이 출력하는 메서드"""
        
        # head의 다음 노드(첫 번째 데이터 노드)부터 시작
        curr = self.head.next
        
        # 출력할 문자들을 저장할 리스트
        result = []
        
        # tail 더미 노드 직전까지 순회
        while curr != self.tail:
            result.append(curr.elem)  # 현재 노드의 데이터 추가
            curr = curr.next          # 다음 노드로 이동
        
        # 리스트의 모든 문자를 공백 없이 연결하여 출력
        # 빈 리스트일 경우 빈 문자열 출력
        print(''.join(result) if result else '')


def main():
    """메인 함수 - 사용자 입력을 받아 연산 수행"""
    
    # 첫 번째 줄: 수행할 연산의 총 개수 입력
    n = int(input())
    
    # 이중연결리스트 객체 생성
    dll = DoublyLinkedList()
    
    # n개의 연산을 순차적으로 처리
    for _ in range(n):
        # 한 줄을 입력받아 공백으로 분리
        # 예: "A 2 x" -> ['A', '2', 'x']
        operation = input().split()
        
        # 첫 번째 문자로 연산 종류 판별
        if operation[0] == 'A':  # Add 연산
            r = int(operation[1])    # 두 번째 요소: 순위 (정수로 변환)
            e = operation[2]          # 세 번째 요소: 삽입할 문자
            dll.add(r, e)             # add 메서드 호출
        
        elif operation[0] == 'D':  # Delete 연산
            r = int(operation[1])    # 두 번째 요소: 순위 (정수로 변환)
            dll.delete(r)             # delete 메서드 호출
        
        elif operation[0] == 'G':  # Get entry 연산
            r = int(operation[1])    # 두 번째 요소: 순위 (정수로 변환)
            dll.get_entry(r)          # get_entry 메서드 호출
        
        elif operation[0] == 'P':  # Print list 연산
            dll.print_list()          # print_list 메서드 호출
                                     # (P 연산은 추가 인자 없음)


# 프로그램 시작점
# 이 파일이 직접 실행될 때만 main() 함수 호출
# (다른 파일에서 import할 때는 실행되지 않음)
if __name__ == "__main__":
    main()