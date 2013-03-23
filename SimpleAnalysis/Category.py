# A definition of a category, used by sorting analyses
class Category:
    def __init__(self,name,title,*args,**kwargs):
        self.name=name
        self.title=title
        for k in kwargs:
            v=kwargs[k]
            setattr(self,k,v)

