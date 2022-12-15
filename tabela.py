from Simbolo import Simbolo

class TabelaSimbolos:

    def __init__(self):
        self.tabela = dict()

    def existeIdent(self, nome, categoria):
        if nome in self.tabela and self.tabela[nome].categoria == categoria:
            return True
        else:
            return False

    def declaraIdent(self, nome, categoria,tipo):
        if not self.existeIdent(nome,categoria):
            self.tabela[nome] = Simbolo(categoria,tipo)
            return True
        else:
            return False

    def atribuiValor(self, nome, valor):
        self.tabela[nome].valor = valor

    def __str__(self):
        s = "--- Tabela de Simbolos --- \n"
        for e in self.tabela.keys():
            s += e + ': ' + self.tabela[e].__str__() + "\n"
        return s
