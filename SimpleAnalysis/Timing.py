from datetime import datetime

class Timing:
    def __init__(self):
        self.x=None
        self.n=0

    def start(self):
        self.lastTime=datetime.now()

    def end(self):
        now=datetime.now()
        delta=now-self.lastTime
        self.lastTime=now

        if self.x==None:
            self.x=delta
        else:
            self.x+=delta
        self.n+=1

    def average(self):
        if self.n==0: return 0
        return self.x/self.n
    
