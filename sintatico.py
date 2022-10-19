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
          

    PROGRAM -> { DEFINITION }
    DEFINITION -> DEF-VARIABLE | DEF-FUNCTION | DEF-TYPE
    DEF-VARIABLE -> VAR id : TYPE ;
    TYPE -> id
    DEF-TYPE -> tipo id = TYPEDESC
    TYPEDESC -> id | '[' TYPEDESC ']' | '{' { FIELD } '}'
    FIELD -> id : TYPE ;
    
    #Estrutura de uma declaração de uma função (assinatura, tipo de retorno  e parametros)
    DEF-FUNCTION -> function id ( PARAMETERS ) [ : TYPE ] BLOCK
    PARAMETERS -> [ PARAMETER { , PARAMETER } ]
    PARAMETER -> id : TYPE
    
    #Escopo de bloco
    BLOCK -> '{' { DEF-VARIABLE } { STATEMENT } '}'
    
    #Estruturas condicionais, repetição, escopo de bloco
    STATEMENT -> if COND BLOCK [ else BLOCK ] 
                 | WHILE COND BLOCK 
                 | VAR = EXP ; 
                 | return [ exp ] ; 
                 | CALL ; 
                 | @ EXP ;
                 | BLOCK
                 
    #Chamando variavel
    VAR -> id | EXP '[' EXP ']' | EXP . id
    
    #Expressões gerais (aritmetica, array, operador ternário) - PRODUÇÃO CAGADA
    EXP -> VAR | ( EXP ) | CALL | EXP as TYPE | new TYPE [ '[' EXP ']' ] | COND ? EXP : EXP
           | - EXP | EXP + EXP | EXP - EXP | EXP * EXP | EXP / EXP | num        
    
    #Removendo ambiguidade do EXP (neste processo foram removidas as recursões à esquerda e feitas as devidas 
    fatorações)
            
    EXP -> VAR | ( EXP ) | CALL | as TYPE EXP' | new TYPE [ '[' EXP ']' ] | COND ? EXP : EXP | EVAL
    EXP' -> as TYPE EXP' | VAR EXP'| ( EXP ) EXP'| CALL EXP' | new TYPE [ '[' EXP ']' ] EXP' | COND ? EXP : EXP EXP'| 
            EVAL EXP' | λ
            
    ---
    EVAL -> SOMA RESTOIGUAL
    RESTOIGUAL -> = SOMA | λ       
    
    SOMA -> MULT RESTOSOMA
    RESTOSOMA -> λ | + SOMA | - SOMA
    
    MULT -> UNO MULT'
    MULT' -> λ | RESTOMULT 
    RESTOMULT -> * MULT | / MULT 
    
    UNO -> + UNO | - UNO | FATOR
    
    FATOR -> num | ( EVAL )
    ---
        
    #Avaliando condições lógicas - PRODUÇÃO CAGADA
    COND -> '(' COND ')' | EXP == EXP | EXP ~= EXP | EXP <= EXP | EXP >= EXP | EXP < EXP | ! COND | COND && COND
            | COND || COND
    
    #Removendo ambiguidade do COND (neste processo foram removidas as recursões à esquerda e feitas as devidas 
    fatorações)
    ---
    COND -> '(' COND ')' | == EXP EXP' | ~= EXP EXP' | <= EXP EXP' | >= EXP EXP' | < EXP EXP' | EVALLOG
    
    EVALLOG -> LOG
    
    LOG -> NOT LOG'
    LOG' -> || LOG' | && LOG' | λ
    
    NOT -> COND NOT'
    NOT' -> ! NOT' | λ        
    ---
                    
    CALL -> id ( EXPLIST ) #chamada de função
    
    EXPLIST -> [ EXP { , EXP } ] #Parametros na chamada de uma função                 
  
"""

class Sintatico:

    def __init__(self):
        self.lex = None
        self.tokenAtual = None
        self.deuErro = False
        self.modoPanico = False
        self.tokensSync = (tt.PTOVIRG,tt.FIMARQ)

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
            self.consome( tt.FIMARQ )
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
        if self.tokenEsperadoEncontrado(token) and not self.modoPanico:
            print(f'consumiu: {self.tokenAtual.tipo}: {self.tokenAtual.lexema}')
            self.tokenAtual = self.lex.getToken()
        elif not self.modoPanico:
            self.deuErro = True
            self.modoPanico = True
            (const, msg) = token
            print('ERRO DE SINTAXE [linha %d]: era esperado "%s" mas veio "%s"'
               % (self.tokenAtual.linha, msg, self.tokenAtual.lexema))

            #Procurando token de sincronismo ($ ou ;)
            parar = False
            while not parar:
                self.tokenAtual = self.lex.getToken()
                for t in self.tokensSync:
                    (const,msg) = t
                    if self.tokenAtual.const == const:
                        parar = True
                        break

        elif self.tokenEsperadoEncontrado(token): #Achou token de sincronismo, cancela modo panico
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
            msg = "Variavel " + var + " nao declarada."
            self.semantico.erroSemantico(msg, linha)
            quit()

    # Expandindo não terminais
    #Produção inicial
    def PROGRAM(self):
        #Será executada até encontrar $
        while not self.tokenEsperadoEncontrado(tt.FIMARQ):
            print('program')
            self.DEFINITION()

    #Reconhecendo se a entrada atual se trata de uma definição de variavel,função ou tipo.
    def DEFINITION(self):
        print('definition')
        if self.tokenEsperadoEncontrado(tt.VAR):
            self.DEF_VARIABLE()
        if self.tokenEsperadoEncontrado(tt.FUNCTION):
            self.DEF_FUNCTION()
        if self.tokenEsperadoEncontrado(tt.TYPE):
            self.DEF_TYPE()
        if self.tokenEsperadoEncontrado(tt.PTOVIRG):
            self.consome(tt.PTOVIRG)

    #Reconhecendo declarações de variáveis
    def DEF_VARIABLE(self):
        print('def-variable')
        self.consome(tt.VAR)
        self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        self.TYPE()
        self.consome(tt.PTOVIRG)

    #Reconhecendo declarações de funções
    def DEF_FUNCTION(self):
        print('def-function')
        self.consome(tt.FUNCTION)
        self.consome(tt.ID)
        self.consome(tt.ABREPAR)
        self.PARAMETERS()
        self.consome(tt.FECHAPAR)
        if self.tokenEsperadoEncontrado(tt.DOISPONTOS): #Se tiver tipo de retorno explicito
            self.consome(tt.DOISPONTOS)
            self.TYPE()
        self.BLOCK()

    #Reconhecendo parametros da função
    def PARAMETERS(self):
        print('parameters')
        if self.tokenEsperadoEncontrado(tt.ID) or not self.tokenEsperadoEncontrado(tt.FECHAPAR):
            self.PARAMETER()
            while self.tokenEsperadoEncontrado(tt.VIRGULA):
                self.consome(tt.VIRGULA)
                self.PARAMETER()


    #Reconhecendo cada parametro individualmente
    def PARAMETER(self):
        print('parameter')
        self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        self.TYPE()

    #Escopo de código
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

    def STATEMENT(self):
        print("statement")
        #Lendo declaração IF-ELSE
        if self.tokenEsperadoEncontrado(tt.IF):
            self.consome(tt.IF)
            self.COND()
            self.BLOCK()
            if self.tokenEsperadoEncontrado(tt.ELSE):
                self.consome(tt.ELSE)
                self.BLOCK()
        #Lendo declaração WHILE
        if self.tokenEsperadoEncontrado(tt.WHILE):
            self.consome(tt.WHILE)
            self.COND()
            self.BLOCK()
        #Declarando variável ou chamando uma função
        if self.tokenEsperadoEncontrado(tt.ID):
            self.consome(tt.ID)
            if self.tokenEsperadoEncontrado(tt.ABREPAR): #É uma chamada de função
                self.CALL()
            else: #É uma Declaração de variável
                self.VAR()
                self.consome(tt.ATRIB)
                self.EXP()
                self.consome(tt.PTOVIRG)
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

    #Definindo um tipo
    def DEF_TYPE(self):
        print("def-type")
        self.consome(tt.TYPE)
        self.consome(tt.ID)
        self.consome(tt.ATRIB)
        self.TYPE_DESC()
        self.consome(tt.PTOVIRG)

    #Lendo um possível campo estruturado
    def TYPE_DESC(self):
        print("type-desc")
        if self.tokenEsperadoEncontrado(tt.ID): #Tipo Simples
            self.consome(tt.ID)
        elif self.tokenEsperadoEncontrado(tt.ABRE_COLCHETE): #Aparentemente é um Array
            self.consome(tt.ABRE_COLCHETE)
            self.TYPE_DESC()
            self.consome(tt.FECHA_COLCHETE)
        elif self.tokenEsperadoEncontrado(tt.ABREBLOCO):
            while self.tokenEsperadoEncontrado(tt.ID): #Possui mais de um campo
                self.FIELD()
            self.consome(tt.FECHABLOCO)

    def TYPE(self):
        print('type')
        self.consome(tt.ID)

    def FIELD(self):
        print('field')
        self.consome(tt.ID)
        self.consome(tt.DOISPONTOS)
        self.TYPE()
        self.consome(tt.PTOVIRG)

    #Produções que necessitaram de alterações
    # Avaliando expressões
    def EXP(self):
        print('exp')
        if self.tokenEsperadoEncontrado(tt.NUM) or\
           self.tokenEsperadoEncontrado(tt.ARIT): #numero ou sinal aritmetico
            self.EVAL()
        if self.tokenEsperadoEncontrado(tt.ID): #variavel ou chamada de função
            self.consome(tt.ID)
            if self.tokenEsperadoEncontrado(tt.ABREPAR): #está chamando função
                self.CALL()
            else: #chamando variavel
                self.VAR()
        if self.tokenEsperadoEncontrado(tt.ABREPAR): #alguma expressão entre parenteses
            self.consome(tt.ABREPAR)
            self.EXP()
            self.consome(tt.FECHAPAR)
        if self.tokenEsperadoEncontrado(tt.AS): #casting
            self.consome(tt.AS)
            self.TYPE()
            self.EXP2()
        if self.tokenEsperadoEncontrado(tt.NEW):
            self.consome(tt.NEW)
            self.TYPE()
            if self.tokenEsperadoEncontrado(tt.ABRE_COLCHETE):
                self.consome(tt.ABRE_COLCHETE)
                self.EXP()
                self.consome(tt.FECHA_COLCHETE)
        else: #Operador ternario
            self.COND()
            self.consome(tt.INTERROGACAO)
            self.EXP()
            self.consome(tt.DOISPONTOS)
            self.EXP()


    def EXP2(self):
        print('EXP2')
        if self.tokenEsperadoEncontrado(tt.ID): #variavel ou chamada de função
            self.consome(tt.ID)
            if self.tokenEsperadoEncontrado(tt.ABREPAR): #está chamando função
                self.CALL()
            else: #chamando variavel
                self.VAR()
            self.EXP2()

    #Avaliando expressões aritméticas
    #---
    def EVAL(self):
        print('eval')
        self.SOMA()
        self.RESTOIGUAL()

    def RESTOIGUAL(self):
        print('restoigual')
        if self.tokenEsperadoEncontrado(tt.ATRIB):
            self.consome(tt.ATRIB)
            self.SOMA()

    def SOMA(self):
        print('soma')
        self.MULT()
        self.RESTOSOMA()

    def RESTOSOMA(self):
        print('restosoma')
        if self.tokenAtual.lexema == '+' or self.tokenAtual.lexema == '-':
            self.consome(tt.ARIT)
            self.SOMA()

    def MULT(self):
        print('mult')
        self.UNO()
        self.RESTOMULT()

    def RESTOMULT(self):
        print('resto mult')
        if self.tokenAtual.lexema == '*' or self.tokenAtual.lexema == '/':
            self.consome(tt.ARIT)
            self.MULT()

    def UNO(self):
        print('uno')
        if self.tokenAtual.lexema == '+' or self.tokenAtual.lexema == '-':
            self.consome(tt.ARIT)
            self.UNO()
        else:
            self.FATOR()

    def FATOR(self):
        print('fator')
        if self.tokenEsperadoEncontrado(tt.NUM):
            self.consome(tt.NUM)
        else:
            self.consome(tt.ABREPAR)
            self.EVAL()
            self.consome(tt.FECHAPAR)

    #----

    def COND(self): #TIRAR RECURSÃO
        print('cond')
        if self.tokenEsperadoEncontrado(tt.ABREPAR):
            self.consome(tt.ABREPAR)
            self.COND()
            self.consome(tt.FECHAPAR)
        if self.tokenEsperadoEncontrado(tt.NOT):
            self.EVALLOG()
        else:
            self.EXP()
            self.consome(tt.COMPAR)
            self.EXP()

    def EVALLOG(self):
        print('evallog')
        self.LOG()

    def LOG(self):
        print('log')
        self.NOT()
        self.LOG2()

    def LOG2(self):
        print('log2')
        if self.tokenEsperadoEncontrado(tt.OPLOG):
            self.consome(tt.OPLOG)
            self.LOG2()

    def NOT(self):
        print('not')
        self.COND()
        self.NOT2()

    def NOT2(self):
        print('not2')
        if self.tokenEsperadoEncontrado(tt.NOT):
            self.consome(tt.NOT)
            self.NOT2()

    #Chamada de uma função
    def CALL(self):
        print('call')
        self.consome(tt.ABREPAR)
        self.EXPLIST()
        self.consome(tt.FECHAPAR)

    #Lista de parametros ao chamar uma função
    def EXPLIST(self): #TIRAR RECURSÃO
        print('explist')
        if not self.tokenEsperadoEncontrado(tt.FECHAPAR):
            self.EXP()
            while not self.tokenEsperadoEncontrado(tt.FECHAPAR):
                self.consome(tt.VIRGULA)
                self.EXP()


    def VAR(self): #TIRAR RECURSÃO
        print('var')
        if self.tokenEsperadoEncontrado(tt.ABRE_COLCHETE):
            self.consome(tt.ABRE_COLCHETE)
            self.EXP()
            self.consome(tt.FECHA_COLCHETE)
        else:
            self.consome(tt.PONTO)
            self.consome(tt.ID)









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

