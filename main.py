#Nome : Alberto Gusmão Cabral Junior
#RA : 0056119
#Data: 02/10/2022

#implementação dos analisadores léxico, sintático, semântico,
# tabela de símbolos e tratamento de erros para a linguagem de
# programação Monga

from sintatico import Sintatico

if __name__ == '__main__':
    print('Tradutor Monga \n')

    if Sintatico().traduz('Testes/teste_semantico.monga'):
        print("Arquivo sintaticamente correto.")