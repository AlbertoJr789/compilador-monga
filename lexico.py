"""
 Linguagem Monga

    Tokens::

    ID | ATRIB | PTOVIRG | ARIT | OPENPAR | CLOSEPAR | NUM | ERROR | EOF

    Palavras reservadas::

    ARROBA | AS | IF | TYPE | ELSE | NEW | VAR | FUNCTION | RETURN | WHILE | MAIN | THEN

    Comparações e operadores logicos::

    < | > | <= | >= | || (OR) | && (AND) | ! (NEGAÇÃO) | ~=

    Operador ternario::
    ? | :

    Comentarios::
    iniciam com # ate o fim da linha
"""

from os import path

class TipoToken:

    ID = (1, 'id')
    ATRIB = (2, '=')
    PTOVIRG = (3, ';')
    ARIT_SUM = (4,'op_sum')
    ABREPAR = (5, '(')
    FECHAPAR = (6, ')')
    NUM = (7, 'num_inteiro')
    NUMHEX = (8,'num_hex')
    NUMFLOAT = (37,'num_float')
    ERROR = (9, 'erro')
    FIMARQ = (10, 'eof')
    ARROBA = (11,'@')
    IF = (13,'if')
    WHILE = (14,'while')
    TYPE = (15,'type')
    ELSE = (16,'else')
    NEW = (17,'new')
    VAR = (18,'var')
    FUNCTION = (19,'function')
    RETURN = (20,'return')
    COMPAR_IGUAL = (21,'compar_igual')
    AND = (22,'&&')
    OR = (23,'||')
    ID_FUNCTION = (24,'id_function')
    ABREBLOCO = (25,'{')
    FECHABLOCO = (26,'}')
    INTERROGACAO = (27,'?')
    DOISPONTOS = (28,':')
    ABRE_COLCHETE = (29,'[')
    FECHA_COLCHETE = (30,']')
    VIRGULA = (31,',')
    PONTO = (32,'.')
    NOT = (33,'!')
    IDVAR = (34,'idvar')
    COMPAR_NUM = (35,'compar_num')
    ARIT_MULT = (36,'op_mult')


class Token:
    def __init__(self, tipo, lexema, linha):
        self.tipo = tipo
        (const, msg) = tipo
        self.const = const
        self.msg = msg
        self.lexema = lexema
        self.linha = linha

class Lexico:

    # dicionario de palavras reservadas
    reservadas = {
        '@': TipoToken.ARROBA,
        'IF': TipoToken.IF,
        'WHILE': TipoToken.WHILE,
        'ELSE': TipoToken.ELSE,
        'VAR': TipoToken.VAR,
        'FUNCTION': TipoToken.FUNCTION,
        'RETURN': TipoToken.RETURN,
        'int': TipoToken.IDVAR,
        'float': TipoToken.IDVAR,
    }

    charsHex = ['0','1','2','3','4','5','6','7','8','9',
    'A','B','C','D','E','F','a','b','c','d','e','f',';']

    def __init__(self, nomeArquivo):
        self.nomeArquivo = nomeArquivo
        self.arquivo = None
        # os atributos buffer e linha sao incluidos no metodo abreArquivo

    def abreArquivo(self):
        if not self.arquivo is None:
            print('ERRO: Arquivo ja aberto')
            quit()
        elif path.exists(self.nomeArquivo):
            self.arquivo = open(self.nomeArquivo, "r")
            # fila de caracteres 'deslidos' pelo ungetChar
            self.buffer = ''
            self.linha = 1
        else:
            print('ERRO: Arquivo "%s" inexistente.' % self.nomeArquivo)
            quit()

    def fechaArquivo(self):
        if self.arquivo is None:
            print('ERRO: Nao ha arquivo aberto')
            quit()
        else:
            self.arquivo.close()

    def getChar(self):
        if self.arquivo is None:
            print('ERRO: Nao ha arquivo aberto')
            quit()
        elif len(self.buffer) > 0:
            #Recebendo caractere
            c = self.buffer[0]
            #Removendo-o do buffer
            self.buffer = self.buffer[1:]
            return c
        else:
            c = self.arquivo.read(1)
            # se nao foi eof, pelo menos um car foi lido
            # senao len(c) == 0
            if len(c) == 0:
                return None
            else:
                return c

    def ungetChar(self, c):
        if not c is None:
            self.buffer = self.buffer + c

    def getToken(self):

        lexema = ''
        estado = 1
        car = None
        ID_Erro = False
        erro_Float = False

        while (True):
            if estado == 1:
                # estado inicial que faz primeira classificacao
                car = self.getChar()
                if car is None:
                    return Token(TipoToken.FIMARQ, '<eof>', self.linha)
                elif car in {' ', '\t', '\n'}:
                    if car == '\n':
                        self.linha = self.linha + 1
                elif car.isalpha(): #trata letras
                    estado = 2
                elif car.isdigit(): #trata digitos
                    car = car + self.getChar()
                    if car == '0x': #numero hex
                        estado = 6
                    else: #numero decimal
                        self.ungetChar(car[-1])
                        car = car.replace(car[-1],'')
                        estado = 3
                elif car in {'=', ';', '+', '*','-','/', '(', ')',
                             '<','>','|','&','!','@','{','}','?',
                             ':','~','[',']',',','.','%'}: #trata operadores aritmeticos e tokens primitivos
                    estado = 4
                elif car == '#': #trata comentario
                    estado = 5
                else:
                    return Token(TipoToken.ERROR, '<' + car + '>', self.linha)
            elif estado == 2:

                # estado que trata nomes (identificadores ou palavras reservadas)
                lexema = lexema + car
                car = self.getChar()
                if car is None or (not car.isalnum()): # terminou o nome

                    ID_Fun = False
                    #Verificando se é um ID de chamada/declaração de função
                    if car == '(':
                        ID_Fun = True

                    self.ungetChar(car)
                    if lexema in Lexico.reservadas:
                        return Token(Lexico.reservadas[lexema], lexema, self.linha)
                    if len(lexema) > 32:  # limite de caracteres para um id
                        return Token(TipoToken.ERROR, lexema, self.linha)
                    elif ID_Erro:
                        ID_Erro = False
                        return Token(TipoToken.ERROR, lexema, self.linha)
                    else:
                        if ID_Fun:
                            return Token(TipoToken.ID_FUNCTION,lexema,self.linha)
                        return Token(TipoToken.ID, lexema, self.linha)

            elif estado == 3:
                # estado que trata numeros
                lexema = lexema + car
                car = self.getChar()

                if car == '.': #Numero flutuante
                    estado = 7
                else:
                    if car is None or (not car.isdigit()):
                        # terminou o numero
                        self.ungetChar(car)
                        return Token(TipoToken.NUM, lexema, self.linha)
            elif estado == 4:
                # estado que trata outros tokens primitivos comuns
                lexema = lexema + car
                if car == '=':
                    lexema = lexema + self.getChar()  # vai tentar procurar um '='
                    if lexema == '==':
                        return Token(TipoToken.COMPAR_IGUAL, lexema, self.linha)
                    else:  # se não tiver
                        self.ungetChar(lexema[-1])  # 'des-lê'
                        lexema = lexema.replace(lexema[-1], '')  # remove caractere do lexema
                    return Token(TipoToken.ATRIB, lexema, self.linha)
                elif car == '!':
                    lexema = lexema + self.getChar()  # vai tentar procurar um '='
                    if lexema == '!=':
                        return Token(TipoToken.COMPAR_IGUAL, lexema, self.linha)
                    else:  # se não tiver
                        self.ungetChar(lexema[-1])  # 'des-lê'
                        lexema = lexema.replace(lexema[-1], '')  # remove caractere do lexema
                elif car == ';':
                    return Token(TipoToken.PTOVIRG, lexema, self.linha)
                elif car in {'+','-'}:
                    return Token(TipoToken.ARIT_SUM, lexema, self.linha)
                elif car in {'*','/','%'}:
                    return Token(TipoToken.ARIT_MULT, lexema, self.linha)
                elif car == '(':
                    return Token(TipoToken.ABREPAR, lexema, self.linha)
                elif car == ')':
                    return Token(TipoToken.FECHAPAR, lexema, self.linha)
                elif car in {'<','>'}:
                    lexema = lexema + self.getChar() #vai tentar procurar um '='
                    if lexema in {'<=', '>='}:
                        return Token(TipoToken.COMPAR_NUM,lexema,self.linha)
                    else: #se não tiver
                        self.ungetChar(lexema[-1]) # 'des-lê'
                        lexema = lexema.replace(lexema[-1],'') #remove caractere do lexema
                    return Token(TipoToken.COMPAR_NUM, lexema, self.linha)
                elif car in {'|','&'}:
                    lexema = lexema + self.getChar()  # vai tentar procurar um '='
                    if lexema == '||':
                        return Token(TipoToken.OR, lexema, self.linha)
                    if lexema == '&&':
                        return Token(TipoToken.AND, lexema, self.linha)
                    else:# se não tiver
                        self.ungetChar(lexema[-1])  # 'des-lê'
                        lexema = lexema.replace(lexema[-1], '')  # remove caractere do lexema
                    return Token(TipoToken.ERROR,lexema,self.linha)
                elif car == '?':
                    return Token(TipoToken.INTERROGACAO,lexema,self.linha)
                elif car == '!':
                    return Token(TipoToken.NOT,lexema,self.linha)
                elif car == ':':
                    return Token(TipoToken.DOISPONTOS,lexema,self.linha)
                elif car == '{':
                    return Token(TipoToken.ABREBLOCO,lexema,self.linha)
                elif car == '}':
                    return Token(TipoToken.FECHABLOCO,lexema,self.linha)
                elif car == '@':
                    return Token(TipoToken.ARROBA,lexema,self.linha)
                elif car == '[':
                    return Token(TipoToken.ABRE_COLCHETE,lexema,self.linha)
                elif car == ']':
                    return Token(TipoToken.FECHA_COLCHETE,lexema,self.linha)
                elif car == ',':
                    return Token(TipoToken.VIRGULA,lexema,self.linha)
                elif car == '.':
                    return Token(TipoToken.PONTO,lexema,self.linha)
            elif estado == 5:
                # consumindo comentario
                while (not car is None) and (car != '\n'):
                    car = self.getChar()
                self.ungetChar(car)
                estado = 1
            elif estado == 6: #estado que trata numeros hexadecimais
                car = self.getChar()
                lexema = lexema + car
                if car not in self.charsHex:
                    return Token(TipoToken.ERROR,'0x'+ lexema,self.linha)
                else:
                    if car == ';':
                        # terminou o numero
                        self.ungetChar(car)
                        lexema = lexema.replace(lexema[-1],'')
                        return Token(TipoToken.NUMHEX, '0x' + lexema, self.linha)

            elif estado == 7: #estado que trata float
                lexema = lexema + car
                car = self.getChar()

                if car is None or (not car.isdigit()):
                    # terminou o numero
                    if car == '.':  # Chegou outro ponto, retorna erro
                        erro_Float = True
                    elif car.isalnum(): # Individuo ta enfiando letra no meio de um numero float
                        erro_Float = True
                    else:
                        if erro_Float:
                            return Token(TipoToken.ERROR, lexema, self.linha)
                        self.ungetChar(car)
                        return Token(TipoToken.NUMFLOAT, lexema, self.linha)



# lex = Lexico('Testes/if_else_log.monga')
# lex.abreArquivo()
#
# while(True):
#     token = lex.getToken()
#     print("token= %s , lexema= %s, linha= %d" % (token.msg, token.lexema, token.linha))
#     if token.const == TipoToken.FIMARQ[0]:
#         break
# lex.fechaArquivo()
