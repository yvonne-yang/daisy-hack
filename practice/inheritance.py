class Parent: 
    def __init__(self, score):
        self.score = score
    
    def calculate_score(self):
        self.score += 1
class Child(Parent):
    def __init__(self):
        pass

def main():
    a = Child(1)
    b = Parent(1)
    a.calculate_score()
    print(a.score)



main()