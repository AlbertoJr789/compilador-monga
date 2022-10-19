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
    ARIT = (4,'op')
    ABREPAR = (5, '(')
    FECHAPAR = (6, ')')
    NUM = (7, 'numero')
    NUMHEX = (8,'numhex')
    ERROR = (9, 'erro')
    FIMARQ = (10, 'eof')
    ARROBA = (11,'@')
    AS = (12,'as')
    IF = (13,'if')
    WHILE = (14,'while')
    TYPE = (15,'type')
    ELSE = (16,'else')
    NEW = (17,'new')
    VAR = (18,'var')
    FUNCTION = (19,'function')
    RETURN = (20,'return')
    COMPAR = (21,'compar')
    OPLOG = (22,'oplog')
    ABREBLOCO = (23,'{')
    FECHABLOCO = (24,'}')
    INTERROGACAO = (25,'?')
    DOISPONTOS = (26,':')
    ABRE_COLCHETE = (27,'[')
    FECHA_COLCHETE = (28,']')
    VIRGULA = (29,',')
    PONTO = (30,'.')
    NOT = (31,'!')

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
        'as': TipoToken.AS,
        'if': TipoToken.IF,
        'while': TipoToken.WHILE,
        'type': TipoToken.TYPE,
        'else': TipoToken.ELSE,
        'new': TipoToken.NEW,
        'var': TipoToken.VAR,
        'function': TipoToken.FUNCTION,
        'return': TipoToken.RETURN,
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
                elif car in {'=', ';', '+', '*', '(', ')',
                             '<','>','|','&',
                             '!','@','{','}','?',
                             ':','~','[',']',',','.'}: #trata operadores aritmeticos e tokens primitivos
                    estado = 4
                elif car == '#': #trata comentario
                    estado = 5
                else:
                    return Token(TipoToken.ERROR, '<' + car + '>', self.linha)
            elif estado == 2:
                # estado que trata nomes (identificadores ou palavras reservadas)
                lexema = lexema + car
                car = self.getChar()
                if car is None or (not car.isalnum()):
                    # terminou o nome
                    self.ungetChar(car)
                    if lexema in Lexico.reservadas:
                        return Token(Lexico.reservadas[lexema], lexema, self.linha)
                    else:
                        return Token(TipoToken.ID, lexema, self.linha)
            elif estado == 3:
                # estado que trata numeros
                lexema = lexema + car
                car = self.getChar()
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
                        return Token(TipoToken.COMPAR, lexema, self.linha)
                    else:  # se não tiver
                        self.ungetChar(lexema[-1])  # 'des-lê'
                        lexema = lexema.replace(lexema[-1], '')  # remove caractere do lexema
                    return Token(TipoToken.ATRIB, lexema, self.linha)
                elif car == '~':
                    lexema = lexema + self.getChar()  # vai tentar procurar um '='
                    if lexema == '~=':
                        return Token(TipoToken.COMPAR, lexema, self.linha)
                    else:  # se não tiver
                        self.ungetChar(lexema[-1])  # 'des-lê'
                        lexema = lexema.replace(lexema[-1], '')  # remove caractere do lexema
                    return Token(TipoToken.ERROR, lexema, self.linha)
                elif car == ';':
                    return Token(TipoToken.PTOVIRG, lexema, self.linha)
                elif car in {'+','-','*','/'}:
                    return Token(TipoToken.ARIT, lexema, self.linha)
                elif car == '(':
                    return Token(TipoToken.ABREPAR, lexema, self.linha)
                elif car == ')':
                    return Token(TipoToken.FECHAPAR, lexema, self.linha)
                elif car in {'<','>'}:
                    lexema = lexema + self.getChar() #vai tentar procurar um '='
                    if lexema in {'<=', '>='}:
                        return Token(TipoToken.COMPAR,lexema,self.linha)
                    else: #se não tiver
                        self.ungetChar(lexema[-1]) # 'des-lê'
                        lexema = lexema.replace(lexema[-1],'') #remove caractere do lexema
                    return Token(TipoToken.COMPAR, lexema, self.linha)
                elif car in {'|','&'}:
                    lexema = lexema + self.getChar()  # vai tentar procurar um '='
                    if lexema in {'||', '&&'}:
                        return Token(TipoToken.OPLOG, lexema, self.linha)
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
            elif estado == 6:
                car = self.getChar()
                lexema = lexema + car
                #tratando numeros hexadecimais
                if car not in self.charsHex:
                    return Token(TipoToken.ERROR,'0x'+ lexema,self.linha)
                else:
                    if car == ';':
                        # terminou o numero
                        self.ungetChar(car)
                        lexema = lexema.replace(lexema[-1],'')
                        return Token(TipoToken.NUMHEX, '0x' + lexema, self.linha)


# lex = Lexico('exemplo.monga')
# lex.abreArquivo()
#
# while(True):
#     token = lex.getToken()
#     print("token= %s , lexema= %s, linha= %d" % (token.msg, token.lexema, token.linha))
#     if token.const == TipoToken.FIMARQ[0]:
#         break
# lex.fechaArquivo()
