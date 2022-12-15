#Nome : Alberto Gusmão Cabral Junior
#RA : 0056119
#Data: 14/12/2022

#implementação dos analisadores léxico, sintático, semântico,
# tabela de símbolos e tratamento de erros para a linguagem de
# programação Monga

from sintatico import Sintatico
import sys

if __name__ == '__main__':
    print('Tradutor Monga \n')

    if Sintatico(sys.argv).traduz('Testes/Incorreto/declaracao_variaveis.monga'):
        print("Arquivo sintaticamente correto.")
    else:
        print('Arquivo com erros,verifique o log')