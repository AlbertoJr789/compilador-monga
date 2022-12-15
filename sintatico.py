from lexico import TipoToken as tt, Token, Lexico
from tabela import TabelaSimbolos
from semantico import Semantico

"""
 Linguagem Monga

    Gramatica (em e-BNF)::
    
    OBS = { X } significa zero ou mais
          [ X ] significa opcional
          Para tratar '[' e '{' como terminais quando necessario, serão colocados entre aspas
          Para que não seja confuso com o e-BNF
          
    program : { definition }

    definition : def-variable | def-function
    
    def-variable : 'VAR' ID ':' type ';'
    
    type : ID
    
    def-function : FUNCTION ID '(' parameters ')' [':' type] block
    
    parameters : [ parameter { ',' parameter } ]
    
    parameter : ID ':' type
    
    block : '{' { def-variable } { statement } '}'
    
    statement : IF exp block [ ELSE block ]
              | WHILE exp block
              | var '=' exp ';'
              | RETURN [ exp ] ';'
              | call ';'
              | '@' exp ';'
              | block
    
    var : ID | exp '[' exp ']' | exp '.' ID
    
    exp -> atrib
    atrib -> or restoAtrib
    restoAtrib -> '=' atrib | lambda
    or -> and restoOr
    restoOr -> '||' and restoOr | lambda
    and -> not restoAnd
    restoAnd -> '&&' not restoAnd | lambda
    not -> '!' not | rel
    rel -> add restoRel
    restoRel -> '==' add | '!=' add
                | '<' add | '<=' add 
                | '>' add | '>=' add | lambda
    add -> mult restoAdd
    restoAdd -> '+' mult restoAdd 
                | '-' mult restoAdd | lambda
    mult -> uno restoMult
    restoMult -> '*' uno restoMult
                |  '/' uno restoMult 
                |  '%' uno restoMult | lambda
    uno -> '+' uno | '-' uno | fator
    fator -> 'NUMint' | 'NUMfloat' 
             | 'IDENT'  | '(' atrib ')'
    
    call : ID '(' explist ')'
    
    explist : [ exp { ',' exp } ]
    
"""

class Sintatico:

    def __init__(self,argv = None):
        self.lex = None
        self.tokenAtual = None
        self.deuErro = False
        self.modoPanico = False
        self.tokensSync = (tt.PTOVIRG,tt.FIMARQ)
        self.argv = argv

    def traduz(self, nomeArquivo):
        if not self.lex is None:
            print('ERRO: Já existe um arquivo sendo processado.')
        else:
            self.deuErro = False
            self.lex = Lexico(nomeArquivo)
            self.lex.abreArquivo()
            self.tokenAtual = self.lex.getToken()

            # inicio reconhecimento do fonte
            self.tabsimb = TabelaSimbolos()
            self.semantico = Semantico()

            self.PROGRAM()
            self.consome(tt.FIMARQ)

            try:
                if self.argv[1] == '-t':
                    if not self.argv[2]:
                        print("Defina o nome do arquivo !")
                    else: #escreve tabela de simbolos na raiz do projeto
                        open(self.argv[2],'w').write(self.tabsimb.__str__())
            except Exception:
                    pass

            # fim do reconhecimento do fonte
            self.lex.fechaArquivo()
            return not self.deuErro

    def tokenEsperadoEncontrado(self, token):
        (const, msg) = token
        if self.tokenAtual.const == const:
            return True
        else:
            return False

    def testaVarNaoDeclarada(self, var, linha):
        if self.deuErro:
            return
        if not self.tabsimb.existeIdent(var,'V'):
            self.deuErro = True
            msg = "Variável " + var + " não declarada."
            self.semantico.erroSemantico(msg, linha)
        else:
            return True

    def testaFuncaoNaoDeclarada(self,var,linha):
        if self.deuErro:
            return
        if not self.tabsimb.existeIdent(var,'F'):
            self.deuErro = True
            msg = "Função " + var + " não declarada."
            self.semantico.erroSemantico(msg, linha)


    def consome(self, token):

        if token == tt.ERROR:
            print(f'ERRO LÉXICO [linha {self.tokenAtual.linha}, caractere \'{self.tokenAtual.lexema}\']: '
                  f'NÃO RECONHECIDO OU EXCEDE 32 CARACTERES')
            self.tokenAtual = self.lex.getToken()
            return

        if self.tokenEsperadoEncontrado(token) and not self.modoPanico:

            print(f'consumiu: {self.tokenAtual.tipo}: {self.tokenAtual.lexema}')

            # SEMANTICO
            match self.tokenAtual.tipo:
                # Retornando lexema para declaração/número
                # Primeiro o lexema precisa ser salvo para chamar o próximo token que será consumido depois
                case tt.IDVAR:
                    tokenBkp = self.tokenAtual
                    self.tokenAtual = self.lex.getToken()
                    return tokenBkp
                case tt.ID:
                    tokenBkp = self.tokenAtual
                    self.tokenAtual = self.lex.getToken()
                    return tokenBkp
                case tt.ID_FUNCTION:
                    tokenBkp = self.tokenAtual
                    self.tokenAtual = self.lex.getToken()
                    return tokenBkp
                #Retornando Tipos de número ------
                case tt.NUM:
                    num = self.tokenAtual.lexema
                    self.tokenAtual = self.lex.getToken()
                    return int(num)
                case tt.NUMHEX:
                    num = self.tokenAtual.lexema
                    self.tokenAtual = self.lex.getToken()
                    return hex(int(num))
                case tt.NUMFLOAT:
                    num = self.tokenAtual.lexema
                    self.tokenAtual = self.lex.getToken()
                    return float(num)
                #Retornando Operadores --------
                case tt.COMPAR_NUM:
                    match self.tokenAtual.lexema:
                        case '<':
                            self.tokenAtual = self.lex.getToken()
                            return '<'
                        case '<=':
                            self.tokenAtual = self.lex.getToken()
                            return '<='
                        case '>':
                            self.tokenAtual = self.lex.getToken()
                            return '>'
                        case '>=':
                            self.tokenAtual = self.lex.getToken()
                            return '>='
                        case _:
                            return
                case tt.COMPAR_IGUAL:
                    match self.tokenAtual.lexema:
                        case '==':
                            self.tokenAtual = self.lex.getToken()
                            return '=='
                        case '!=':
                            self.tokenAtual = self.lex.getToken()
                            return '!='
                        case _:
                            return
                case tt.ARIT_SUM:
                    match self.tokenAtual.lexema:
                        case '+':
                            self.tokenAtual = self.lex.getToken()
                            return '+'
                        case '-':
                            self.tokenAtual = self.lex.getToken()
                            return '-'
                        case _:
                            return
                case tt.ARIT_MULT:
                    match self.tokenAtual.lexema:
                        case '*':
                            self.tokenAtual = self.lex.getToken()
                            return '*'
                        case '/':
                            self.tokenAtual = self.lex.getToken()
                            return '/'
                        case '%':
                            self.tokenAtual = self.lex.getToken()
                            return '%'
                        case _:
                            return
                case _:
                    pass

            self.tokenAtual = self.lex.getToken()

        elif not self.modoPanico:
            self.deuErro = True
            self.modoPanico = True
            (const, msg) = token

            print('ERRO DE SINTAXE [linha %d]: era esperado "%s" mas veio "%s"'
                % (self.tokenAtual.linha, msg, self.tokenAtual.lexema))

            print('Modo Panico Ativado')

            #Procurando token de sincronismo ($,;,{,})
            parar = False
            while not parar:
                self.tokenAtual = self.lex.getToken()
                print(self.tokenAtual.tipo)
                for t in self.tokensSync:
                    (const,msg) = t
                    if self.tokenAtual.const == const:
                        parar = True
                        print('Achou Token Sync')
                        self.tokenAtual = self.lex.getToken()
                        self.modoPanico = False
                        break


    # Expandindo não terminais
    #Produção inicial

    # PROGRAM -> { DEFINITION }
    def PROGRAM(self):
        #Será executada até encontrar $
        ret = True
        while not self.tokenEsperadoEncontrado(tt.FIMARQ):
            print('program')
            ret = self.DEFINITION()
            if ret == False:
                print('loop')
                break

    #Reconhecendo se a entrada atual se trata de uma definição de variavel,função ou tipo.
    #DEFINITION -> DEF-VARIABLE | DEF-FUNCTION | DEF-TYPE
    def DEFINITION(self):
        print('definition')
        if self.tokenEsperadoEncontrado(tt.VAR):
            self.DEF_VARIABLE()
        elif self.tokenEsperadoEncontrado(tt.FUNCTION):
            self.DEF_FUNCTION()
        else: #Possivelmente em modo panico
            return False

    #Reconhecendo declarações de variáveis
    # DEF-VARIABLE -> VAR id : TYPE ;
    def DEF_VARIABLE(self):
        print('def-variable')
        self.consome(tt.VAR)
        id = self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        tipo = self.TYPE()
        self.consome(tt.PTOVIRG)
        self.tabsimb.declaraIdent(id.lexema,'V',tipo.lexema)

    #Reconhecendo declarações de funções
    #DEF-FUNCTION -> function id ( PARAMETERS ) [ : TYPE ] BLOCK
    def DEF_FUNCTION(self):
        print('def-function')
        self.consome(tt.FUNCTION)
        id = self.consome(tt.ID_FUNCTION)
        self.consome(tt.ABREPAR)
        self.PARAMETERS()
        self.consome(tt.FECHAPAR)
        if self.tokenEsperadoEncontrado(tt.DOISPONTOS): #Se tiver tipo de retorno explicito
            self.consome(tt.DOISPONTOS)
            tipo = self.TYPE()
            self.tabsimb.declaraIdent(id.lexema,'F',tipo.lexema)
        else:
            self.tabsimb.declaraIdent(id.lexema,'F','VOID')

        self.BLOCK()

    #Reconhecendo parametros da função
    #PARAMETERS -> [ PARAMETER { , PARAMETER } ]
    def PARAMETERS(self):
        print('parameters')
        if self.tokenEsperadoEncontrado(tt.ID) or not self.tokenEsperadoEncontrado(tt.FECHAPAR):
            self.PARAMETER()
            while self.tokenEsperadoEncontrado(tt.VIRGULA):
                self.consome(tt.VIRGULA)
                self.PARAMETER()


    #Reconhecendo cada parametro individualmente
    #PARAMETER -> id : TYPE
    def PARAMETER(self):
        print('parameter')
        id = self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        tipo = self.TYPE()
        self.tabsimb.declaraIdent(id.lexema,'VF',tipo.lexema)

    #Escopo de código
    #BLOCK -> '{' { DEF-VARIABLE } { STATEMENT } '}'
    def BLOCK(self):
        print("block")
        self.consome(tt.ABREBLOCO)
        while self.tokenEsperadoEncontrado(tt.VAR): # definir variavel
            self.DEF_VARIABLE()
        while self.tokenEsperadoEncontrado(tt.IF) or \
              self.tokenEsperadoEncontrado(tt.WHILE) or \
              self.tokenEsperadoEncontrado(tt.ID) or \
              self.tokenEsperadoEncontrado(tt.ID_FUNCTION) or\
              self.tokenEsperadoEncontrado(tt.RETURN) or \
              self.tokenEsperadoEncontrado(tt.ARROBA)or \
              self.tokenEsperadoEncontrado(tt.ABREBLOCO): #filtrar algum statement
            self.STATEMENT()
        self.consome(tt.FECHABLOCO)

    # TYPE -> id
    def TYPE(self):
        print('type')
        if self.tokenEsperadoEncontrado(tt.IDVAR):
           return self.consome(tt.IDVAR)
        else:
            return self.consome(tt.ID)

    ### ---- Aqui é onde o filho chora e a mãe não vê ---- ####

    # statement : IF exp block [ ELSE block ]
    #             | WHILE exp block
    #             | var '=' exp ';'
    #             | RETURN [ exp ] ';'
    #             | call ';'
    #             | '@' exp ';'
    #             | block


    def STATEMENT(self):
        print("statement")
        #Lendo declaração IF-ELSE
        if self.tokenEsperadoEncontrado(tt.IF):
            self.consome(tt.IF)
            self.EXP()
            self.BLOCK()
            if self.tokenEsperadoEncontrado(tt.ELSE):
                self.consome(tt.ELSE)
                self.BLOCK()
        #Lendo declaração WHILE
        if self.tokenEsperadoEncontrado(tt.WHILE):
            self.consome(tt.WHILE)
            self.EXP()
            self.BLOCK()
        #chamando função
        if self.tokenEsperadoEncontrado(tt.ID_FUNCTION):
            self.CALL()
            self.consome(tt.PTOVIRG)
        #declarando variavel
        if self.tokenEsperadoEncontrado(tt.ID):
            var = self.VAR()
            self.consome(tt.ATRIB)
            ret = self.EXP()
            self.consome(tt.PTOVIRG)
            if self.testaVarNaoDeclarada(var.lexema,var.linha):
                self.tabsimb.atribuiValor(var.lexema,ret)
        if self.tokenEsperadoEncontrado(tt.RETURN):
            self.consome(tt.RETURN)
            if not self.tokenEsperadoEncontrado(tt.PTOVIRG):
                self.EXP()
            self.consome(tt.PTOVIRG)
        if self.tokenEsperadoEncontrado(tt.ARROBA):
            self.consome(tt.ARROBA)
            self.EXP()
            self.consome(tt.PTOVIRG)
        if self.tokenEsperadoEncontrado(tt.ABREBLOCO):
            self.BLOCK()


    # Chamada de uma função
    def CALL(self):
        print('call')
        self.consome(tt.ID_FUNCTION)
        self.consome(tt.ABREPAR)
        self.EXPLIST()
        self.consome(tt.FECHAPAR)

    # Lista de parametros ao chamar uma função
    def EXPLIST(self): #TIRAR RECURSÃO
        print('explist')
        self.EXP()
        while self.tokenEsperadoEncontrado(tt.VIRGULA):
            self.consome(tt.VIRGULA)
            self.EXP()

    # var : ID | exp '[' exp ']' | exp '.' ID
    def VAR(self): #TIRAR RECURSÃO
        print('var')
        if self.tokenEsperadoEncontrado(tt.NOT) or\
            self.tokenEsperadoEncontrado(tt.ARIT_SUM) or\
            self.tokenEsperadoEncontrado(tt.NUMHEX) or \
            self.tokenEsperadoEncontrado(tt.NUM) or \
            self.tokenEsperadoEncontrado(tt.NUMFLOAT):
            self.EXP()
            if self.tokenEsperadoEncontrado(tt.ABRE_COLCHETE):
                self.consome(tt.ABRE_COLCHETE)
                res = self.EXP()
                self.consome(tt.FECHA_COLCHETE)
                if not res.lexema.isdigit() or not int(res.lexema) >= 0: #se indice nao for inteiro ou negativo
                    self.semantico.erroSemantico(f'Índice {res.lexema} inválido',res.linha)
            else:
                self.consome(tt.PONTO)
                ID = self.consome(tt.ID)
                self.testaVarNaoDeclarada(ID.lexema,ID.linha)
        else:
            return self.consome(tt.ID)

    # !, + , - , numint, numfloat, (
    def EXP(self):
        print('exp')
        return self.ATRIB()

    def ATRIB(self):
        #print('atrib')
        valor = self.OR()
        return self.RESTOATRIB(valor)

    def RESTOATRIB(self,valor):
        print('restoatrib')
        if self.tokenEsperadoEncontrado(tt.ATRIB):
            self.consome(tt.ATRIB)
            valor2 = self.ATRIB()

            return valor2
        else:
            return valor


    def OR(self):
        #print('or')
        valor = self.AND()
        return self.RESTOOR(valor)

    def RESTOOR(self,valor):
        print('restoor')
        if self.tokenEsperadoEncontrado(tt.OR):
            self.consome(tt.OR)
            valor2 = self.AND()
            self.RESTOOR(valor)

            print(f'valor: {valor}, valor2: {valor2}')

            erroSemantico = False
            #Comparação entre dois numeros (||)
            if type(valor) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True
            if type(valor2) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor2}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True

            if erroSemantico:
                return

            # Or entre valores (||)
            if valor or valor2:
                return 1
            else:
                return 0
        else:
            return valor


    def AND(self):
        #print('and')
        valor = self.NOT()
        return self.RESTOAND(valor)

    def RESTOAND(self,valor):
        print('restoand')
        if self.tokenEsperadoEncontrado(tt.AND):
            self.consome(tt.AND)
            valor2 = self.NOT()
            self.RESTOAND(valor)

            print(f'tipo valor: {valor}, tipo valor2: {valor2}')

            erroSemantico = False
            #Comparação entre dois numeros (&&)
            if type(valor) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True
            if type(valor2) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor2}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True

            if erroSemantico:
                return

            #And entre valores (&&)
            if valor and valor2:
                return 1
            else:
                return 0

        else:
            return valor

    def NOT(self):
        print('not')
        if self.tokenEsperadoEncontrado(tt.NOT):
            self.consome(tt.NOT)
            valor = self.NOT()

            print(f'valor: {valor}')

            erroSemantico = False
            #Comparação entre dois numeros (==, !=)
            if type(valor) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True

            if erroSemantico:
                return

            #Not unário (!)
            if valor:
                return 0
            else:
                return 1
        else:
            return self.REL()

    def REL(self):
        #print('rel')
        valor = self.ADD()
        return self.RESTOREL(valor)

    def RESTOREL(self,valor):
        print('restorel')
        if self.tokenEsperadoEncontrado(tt.COMPAR_IGUAL):
            op = self.consome(tt.COMPAR_IGUAL)
            valor2 = self.ADD()

            print(f'valor: {valor}, valor2: {valor2}')

            erroSemantico = False
            #Comparação entre dois numeros (==, !=)
            if type(valor) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True
            if type(valor2) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor2}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True

            if erroSemantico:
                return

            match op:
                case '!=':
                    if valor != valor2:
                        return 1
                    else:
                        return 0
                case '==':
                    if valor == valor2:
                        return 1
                    else:
                        return 0
                case _:
                    pass

        elif self.tokenEsperadoEncontrado(tt.COMPAR_NUM):
            op = self.consome(tt.COMPAR_NUM)
            valor2 = self.ADD()

            print(f'valor: {valor}, valor2: {valor2}')

            erroSemantico = False
            #Comparação entre dois numeros (==, !=)
            if type(valor) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True
            if type(valor2) is not int:
                self.semantico.erroSemantico(f'Operação lógica com operando [{valor2}] que não é inteiro ',self.tokenAtual.linha)
                erroSemantico = True

            if erroSemantico:
                return

            #Comparação entre dois numeros (<,<=,>,>=)
            match op:
                case '<':
                    if valor < valor2:
                        return 1
                    else:
                        return 0
                case '>':
                    if valor > valor2:
                        return 1
                    else:
                        return 0
                case '<=':
                    if valor <= valor2:
                        return 1
                    else:
                        return 0
                case '>=':
                    if valor >= valor2:
                        return 1
                    else:
                        return 0
                case _:
                    pass

        else:
            return valor

    def ADD(self):
        #print('add')
        valor = self.MULT()
        return self.RESTOADD(valor)

    def RESTOADD(self,valor):
        print('restoadd')
        if self.tokenEsperadoEncontrado(tt.ARIT_SUM):
            op = self.consome(tt.ARIT_SUM)
            valor2 = self.MULT()
            self.RESTOADD(valor)

            converterFloat = False
            # Se tiver fazendo operação  entre inteiro e float, converte resultado pra inteiro
            if isinstance(valor, int) and isinstance(valor2, float):
                converterFloat = True
            if isinstance(valor, float) and isinstance(valor2, int):
                converterFloat = True

            match op:
                case '+':
                    if converterFloat:
                        print('Convertendo resultado pra inteiro')
                        return int(valor + valor2)
                    return valor + valor2
                case '-':
                    if converterFloat:
                        print('Convertendo resultado pra inteiro')
                        return int(valor - valor2)
                    return valor - valor2
                case _:
                    pass
        else:
            return valor


    def MULT(self):
        #print('mult')
        valor = self.UNO()
        return self.RESTOMULT(valor)

    def RESTOMULT(self,valor):
        print('restomult')
        if self.tokenEsperadoEncontrado(tt.ARIT_MULT):
            op = self.consome(tt.ARIT_MULT)
            valor2 = self.UNO()
            self.RESTOMULT(valor)

            converterFloat = False
            converterHex = False
            # Se tiver fazendo operação  entre inteiro e float, converte resultado pra inteiro
            if isinstance(valor, int) and isinstance(valor2, float):
                converterFloat = True
            if not isinstance(valor, float) and isinstance(valor2, int):
                converterFloat = True

            match op:
                case '*':
                    if converterFloat:
                        return int(valor * valor2)
                    return valor * valor2
                case '/':
                    if converterFloat:
                        return int(valor / valor2)
                    return valor / valor2
                case '%':
                    if converterFloat:
                        return int(valor % valor2)
                    return valor % valor2
                case _:
                    pass
        else:
            return valor

    def UNO(self):
        print('uno')
        if self.tokenEsperadoEncontrado(tt.ARIT_SUM):
            op = self.consome(tt.ARIT_SUM)
            valor = self.UNO()
            match op:
                case '+':
                    return valor
                case '-':
                    return -valor
                case _:
                    pass
        else:
            return self.FATOR()

    def FATOR(self):
        print('fator')
        if self.tokenEsperadoEncontrado(tt.NUM):
            return self.consome(tt.NUM)
        if self.tokenEsperadoEncontrado(tt.NUMFLOAT):
            return self.consome(tt.NUMFLOAT)
        if self.tokenEsperadoEncontrado(tt.NUMHEX):
            return self.consome(tt.NUMHEX)
        if self.tokenEsperadoEncontrado(tt.ABREPAR):
            self.consome(tt.ABREPAR)
            self.ATRIB()
            self.consome(tt.FECHAPAR)


