

class Descritor():
    def __init__(self,colunas,lista):
        self.colunas=colunas
        self.lista=lista

    def descrever(self):
       string=self.descreverLinhas()+'\n'+self.descreverColunas()+'\n'+self.descreverLinhas()+'\n'+self.descreverValores()
       return string

    def maioStringdeUmaColuna(self,coluna):
        lista=[len(str(x[coluna])) for x in self.lista] 
        lista.append(len(self.colunas[coluna]))
        return max(lista)

    def descreverLinhas(self):
        string=''
        for x in range(len(self.colunas)):
           nCarecteresDaColuna=len(self.colunas[x])

           nMenos=abs(nCarecteresDaColuna-self.maioStringdeUmaColuna(x) ) +nCarecteresDaColuna if  nCarecteresDaColuna<self.maioStringdeUmaColuna(x) else  nCarecteresDaColuna
           string+=f'+{'-'*nMenos}'
        return string+'+'

    def descreverColunas(self):
        string=''
        for x in range(len(self.colunas)):
            nCarecteresDaColuna=len(self.colunas[x])
            nEspacoes=abs(nCarecteresDaColuna-self.maioStringdeUmaColuna(x) if  nCarecteresDaColuna<self.maioStringdeUmaColuna(x) else  0)
            string+=f'|{self.colunas[x]+' '*nEspacoes}'
        return string+'|'

    def descreverValores(self):
         string=''
         for x in  range(len(self.lista)):
            for y in range(len(self.lista[x])):
                valoratual=self.lista[x][y]
                nCarecteresDaColuna=len(str(valoratual))
                nEspacoes=abs(nCarecteresDaColuna-self.maioStringdeUmaColuna(y) if  nCarecteresDaColuna<self.maioStringdeUmaColuna(y) else 0)
                string+=f'|{str(valoratual)+' '*nEspacoes}'
            string+='|\n'+self.descreverLinhas()+'\n'
         return string




