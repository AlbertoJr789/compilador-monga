#Nome : Alberto Gusmão Cabral Junior
#RA : 0056119
#Data: 02/10/2022

#implementação dos analisadores léxico, sintático, semântico,
# tabela de símbolos e tratamento de erros para a linguagem de
# programação Monga, gerada pela gramática especificada na seção 2

from sintatico import Sintatico

if __name__ == '__main__':
    print('Tradutor Monga \n')

    parser = Sintatico()
    ok = parser.traduz('exemplo.monga')
    if ok:
        print("Arquivo sintaticamente correto.")