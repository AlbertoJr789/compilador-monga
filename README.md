# A Linguagem Monga

A linguagem Monga é uma linguagem procedural simples. Ela oferece os tipos int, float, arrays e records (structs); estruturas de controle while e if-then-else; variáveis globais e locais; e funções com parâmetros e retorno de valores. Além disso, ela gera código objeto compatível com C, o que permite que programas Monga possam chamar funções das bibliotecas padrão de C.

# Léxico

Comentários em Monga começam com # e terminam no final da linha. Identificadores são como em C. Numerais, tanto inteiros como ponto flutuante, podem ser escritos em decimal ou em hexa (começando com 0x).

A lista de palavras reservadas segue abaixo:

as   |   else  |  function

if   |   new   |  return

type  |  var   |  while

# Sintaxe

A sintaxe da linguagem segue abaixo, em EBNF. Note que { X } significa uma lista de zero ou mais ocorrências de X e [ X ] significa um X opcional. Itens entre aspas simples ou em maiúsculas denotam terminais (tokens), outros nomes denotam não-terminais.

program : { definition }

definition : def-variable | def-function | def-type

def-variable : VAR ID ':' type ';'

type : ID

def-type : TYPE ID '=' typedesc ;

typedesc : ID | '[' typedesc ']' | '{' { field } '}'

field : ID ':' type ';' ;

def-function : FUNCTION ID '(' parameters ')' [':' type] block

parameters : [ parameter { ',' parameter } ]

parameter : ID ':' type

block : '{' { def-variable } { statement } '}'

statement : IF cond block [ ELSE block ]
          | WHILE cond block
          | var '=' exp ';'
          | RETURN [ exp ] ';'
          | call ';'
          | '@' exp ';'
          | block

var : ID | exp '[' exp ']' | exp '.' ID

exp : NUMERAL
    | var
    | '(' exp ')'
    | call
    | exp AS type
    | NEW type [ '[' exp ']' ]
    | '-' exp
    | exp '+' exp
    | exp '-' exp
    | exp '*' exp
    | exp '/' exp
    | cond '?' exp ':' exp

cond :  '(' cond ')'
	| exp '==' exp
	| exp '~=' exp
	| exp '<=' exp
	| exp '>=' exp
	| exp '<' exp
	| exp '>' exp
	| '!' cond
	| cond '&&' cond
	| cond '||' cond

call : ID '(' explist ')'

explist : [ exp { ',' exp } ]
