from lexico import TipoToken as tt, Token, Lexico
from tabela import TabelaSimbolos
from semantico import Semantico
import Testes

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

    def __init__(self):
        self.lex = None
        self.tokenAtual = None
        self.deuErro = False
        self.modoPanico = False
        self.tokensSync = (tt.PTOVIRG,tt.FIMARQ,tt.FECHABLOCO,tt.ABREBLOCO)

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
            # fim do reconhecimento do fonte
            self.lex.fechaArquivo()
            return not self.deuErro

    def tokenEsperadoEncontrado(self, token):
        (const, msg) = token
        if self.tokenAtual.const == const:
            return True
        else:
            return False

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
                # Retornando lexema para declaração
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
                case _:
                    pass

            self.tokenAtual = self.lex.getToken()

        elif not self.modoPanico:
            self.deuErro = True
            self.modoPanico = True
            (const, msg) = token

            print('ERRO DE SINTAXE [linha %d]: era esperado "%s" mas veio "%s"'
                % (self.tokenAtual.linha, msg, self.tokenAtual.lexema))

            #Procurando token de sincronismo ($,;,{,})
            parar = False
            while not parar:
                self.tokenAtual = self.lex.getToken()
                for t in self.tokensSync:
                    (const,msg) = t
                    if self.tokenAtual.const == const:
                        parar = True
                        break

        elif self.tokenEsperadoEncontrado(token): #Achou token de sincronismo, cancela modo panico
            print('consumiu sync')
            self.tokenAtual = self.lex.getToken()
            self.modoPanico = False
        else:
            pass

    def salvaLexema(self):
        return self.tokenAtual.lexema

    def salvaLinha(self):
        return self.tokenAtual.linha

    def testaVarNaoDeclarada(self, var, linha):
        if self.deuErro:
            return
        if not self.tabsimb.existeIdent(var):
            self.deuErro = True
            msg = "Variável " + var + " não declarada."
            self.semantico.erroSemantico(msg, linha)
            quit()

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
        self.tabsimb.declaraIdent(id.lexema,tipo.lexema)

    #Reconhecendo declarações de funções
    #DEF-FUNCTION -> function id ( PARAMETERS ) [ : TYPE ] BLOCK
    def DEF_FUNCTION(self):
        print('def-function')
        self.consome(tt.FUNCTION)
        self.consome(tt.ID_FUNCTION)
        self.consome(tt.ABREPAR)
        self.PARAMETERS()
        self.consome(tt.FECHAPAR)
        if self.tokenEsperadoEncontrado(tt.DOISPONTOS): #Se tiver tipo de retorno explicito
            self.consome(tt.DOISPONTOS)
            self.TYPE()
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
        self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        self.TYPE()

    #Escopo de código
    #BLOCK -> '{' { DEF-VARIABLE } { STATEMENT } '}'
    def BLOCK(self):
        print("block")
        self.consome(tt.ABREBLOCO)
        while self.tokenEsperadoEncontrado(tt.VAR): # definir variavel
            self.DEF_VARIABLE()
        while self.tokenEsperadoEncontrado(tt.IF) or \
              self.tokenEsperadoEncontrado(tt.WHILE) or \
              self.tokenEsperadoEncontrado(tt.ID)or \
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
        #declarando variavel
        if self.tokenEsperadoEncontrado(tt.ID):
            var = self.VAR()
            self.consome(tt.ATRIB)
            self.EXP()
            self.consome(tt.PTOVIRG)
            self.testaVarNaoDeclarada(var.lexema,var.linha)

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
            self.tokenEsperadoEncontrado(tt.NUM):
            self.EXP()
            if self.tokenEsperadoEncontrado(tt.ABRE_COLCHETE):
                self.consome(tt.ABRE_COLCHETE)
                self.EXP()
                self.consome(tt.FECHA_COLCHETE)
            else:
                self.consome(tt.PONTO)
                self.consome(tt.ID)
        else:
            return self.consome(tt.ID)

    # !, + , - , numint, numfloat, (
    def EXP(self):
        print('exp')
        self.ATRIB()

    def ATRIB(self):
        #print('atrib')
        self.OR()
        self.RESTOATRIB()

    def RESTOATRIB(self):
        print('restoatrib')
        if self.tokenEsperadoEncontrado(tt.ATRIB):
            self.consome(tt.ATRIB)
            self.ATRIB()

    def OR(self):
        #print('or')
        self.AND()
        self.RESTOOR()

    def RESTOOR(self):
        print('restoor')
        if self.tokenEsperadoEncontrado(tt.OR):
            self.consome(tt.OR)
            self.AND()
            self.RESTOOR()

    def AND(self):
        #print('and')
        self.NOT()
        self.RESTOAND()

    def RESTOAND(self):
        print('restoand')
        if self.tokenEsperadoEncontrado(tt.AND):
            self.consome(tt.AND)
            self.NOT()
            self.RESTOAND()

    def NOT(self):
        print('not')
        if self.tokenEsperadoEncontrado(tt.NOT):
            self.consome(tt.NOT)
            self.NOT()
        else:
            self.REL()

    def REL(self):
        #print('reç')
        self.ADD()
        self.RESTOREL()

    def RESTOREL(self):
        print('restorel')
        if self.tokenEsperadoEncontrado(tt.COMPAR_IGUAL):
            self.consome(tt.COMPAR_IGUAL)
            self.ADD()
        elif self.tokenEsperadoEncontrado(tt.COMPAR_NUM):
            self.consome(tt.COMPAR_NUM)
            self.ADD()

    def ADD(self):
        #print('add')
        self.MULT()
        self.RESTOADD()

    def RESTOADD(self):
        print('restoadd')
        if self.tokenEsperadoEncontrado(tt.ARIT_SUM):
            self.consome(tt.ARIT_SUM)
            self.MULT()
            self.RESTOADD()

    def MULT(self):
        #print('mult')
        self.UNO()
        self.RESTOMULT()

    def RESTOMULT(self):
        print('restomult')
        if self.tokenEsperadoEncontrado(tt.ARIT_MULT):
            self.consome(tt.ARIT_MULT)
            self.UNO()
            self.RESTOMULT()

    def UNO(self):
        print('uno')
        if self.tokenEsperadoEncontrado(tt.ARIT_SUM):
            self.consome(tt.ARIT_SUM)
            self.UNO()
        else:
            self.FATOR()

    def FATOR(self):
        print('fator')
        if self.tokenEsperadoEncontrado(tt.NUM):
            self.consome(tt.NUM)
        if self.tokenEsperadoEncontrado(tt.NUMFLOAT):
            self.consome(tt.NUMFLOAT)
        if self.tokenEsperadoEncontrado(tt.NUMHEX):
            self.consome(tt.NUMHEX)
        if self.tokenEsperadoEncontrado(tt.ABREPAR):
            self.consome(tt.ABREPAR)
            self.ATRIB()
            self.consome(tt.FECHAPAR)



    ##################################################################
    # Segue uma funcao para cada variavel da gramatica
    ##################################################################

    def F(self):
        self.C()
        self.Rf()

    def Rf(self):
        if self.tokenEsperadoEncontrado( tt.FIMARQ ):
            pass
        else:
            self.C()
            self.Rf()

    def C(self):
        if self.tokenEsperadoEncontrado( tt.READ ):
            self.R()
        elif self.tokenEsperadoEncontrado( tt.PRINT ):
            self.P()
        else:
            self.A()

    def A(self):
        var = self.salvaLexema()
        self.consome( tt.IDENT )
        self.consome( tt.ATRIB )
        valor = self.E()
        self.consome( tt.PTOVIRG )
        if not self.tabsimb.existeIdent(var):
            self.tabsimb.declaraIdent(var, valor)
        else:
            self.tabsimb.atribuiValor(var, valor)

    def R(self):
        self.consome( tt.READ )
        self.consome( tt.OPENPAR )
        var = self.salvaLexema()
        linha = self.salvaLinha()
        self.consome( tt.IDENT )
        self.consome( tt.CLOSEPAR )
        self.consome( tt.PTOVIRG )

        valor = eval(input("Input: "))
        self.testaVarNaoDeclarada(var, linha)
        self.tabsimb.atribuiValor(var, valor)

    def P(self):
        self.consome( tt.PRINT )
        self.consome( tt.OPENPAR )
        var = self.salvaLexema()
        linha = self.salvaLinha()
        self.consome( tt.IDENT )
        self.consome( tt.CLOSEPAR )
        self.consome( tt.PTOVIRG )
        self.testaVarNaoDeclarada(var, linha)
        valor = self.tabsimb.pegaValor(var)
        print(valor)

    def E(self):
        valor1 = self.M()
        valor2 = self.Rs(valor1)
        return valor2

    def Rs(self, valor1):
        if self.tokenEsperadoEncontrado( tt.ADD ):
            self.consome( tt.ADD )
            valor2 = self.M()
            valor3 = valor1 + valor2
            return self.Rs(valor3)
        else:
            return valor1

    def M(self):
        valor1 = self.Op()
        valor2 = self.Rm(valor1)
        return valor2

    def Rm(self, valor1):
        if self.tokenEsperadoEncontrado( tt.MULT ):
            self.consome( tt.MULT )
            valor2 = self.Op()
            valor3 = valor1 * valor2
            return self.Rm(valor3)
        else:
            return valor1

    def Op(self):
        if self.tokenEsperadoEncontrado( tt.OPENPAR ):
            self.consome( tt.OPENPAR )
            valor = self.E()
            self.consome( tt.CLOSEPAR )
            return valor
        elif self.tokenEsperadoEncontrado( tt.NUM ):
            num = self.salvaLexema()
            self.consome( tt.NUM )
            return int(num)
        else:
            var = self.salvaLexema()
            linha = self.salvaLinha()
            self.consome(tt.IDENT)
            self.testaVarNaoDeclarada(var, linha)
            valor = self.tabsimb.pegaValor(var)
            return valor

