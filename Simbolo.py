
class Simbolo:

    def __init__(self,categoria,tipo,valor = None):
        self.categoria = categoria
        self.tipo = tipo
        self.valor = valor

    def __str__(self):
        s = ''
        match self.categoria:
            case 'F':
                s = f'Identificador de Funcao | Tipo de Retorno: {self.tipo} |'
            case 'V':
                s = f'Identificador de Variavel | Tipo: {self.tipo} | Valor: {self.valor}'
            case 'VF':
                s = f'Identificador de Variavel de Função | Tipo: {self.tipo}'

        return s