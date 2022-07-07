import math

# E -> E + T | E - T | T
# T -> T * P | T / P |  P
# P -> P ^ F | exp [ F ] | F
# F -> ( E ) | id

# 12 -> Token.id = "id", Token.value = 12
# ( -> Token.id = "(", Token.value = None

class Token:
    def __init__(self, id: str, value):
        self.id = id
        self.value = value

    def __str__(self):
        return 'id = ' + self.id

    def __repr__(self):
        return self.id


class LexicalAnalyzer:
    def __init__(self, _input: str):
        self.__input__ = _input.lower().replace(' ', '')
        self.__index_token__ = -1
        self.__index_input__ = -1
        self.tokens = self.__get_tokens__()

    def __get_tokens__(self):
        tokens = []
        while True:
            token = self.__get_token__()
            if token is None:
                break
            tokens.append(token)

        return tokens

    def __get_token__(self) -> Token:
        valid_tokens = {
            'numbers': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
            'operators': ['+', '-', '*', '/', '^', '(', ')', '[', ']', 'exp'],
        }

        buffer = ''
        token = None
        while True:
            self.__index_input__ += 1
            if self.__index_input__ >= len(self.__input__) or self.__index_input__ < 0:
                return token

            char = self.__input__[self.__index_input__]

            if (char == '.') and (token is not None):
                token.value += char
            elif char in valid_tokens['numbers']:
                if token is None:
                    token = Token("id", char)
                else:
                    token.value += char
            elif (char in valid_tokens['operators']) and (token is None):
                return Token(char, None)
            elif char == 'e' and buffer == '':
                buffer += char
            elif char == 'x' and buffer == 'e':
                buffer += char
            elif char == 'p' and buffer == 'ex':
                buffer += char
                return Token(buffer, None)
            else:
                self.__index_input__ -= 1
                return token

    def get_all_tokens(self):
        return self.tokens

    def next_token(self):
        self.index_token += 1
        if self.index_token >= len(self.tokens):
            return self.tokens[self.index_token]
        return None

    def previous_token(self):
        self.index_token -= 1
        if self.index_token < 0:
            return self.tokens[self.index_token]
        return None


class AnalisadorSintatico:
    def __init__(self):
        # usar Token.id para procurar pela gramatica
        self.gramatica = {
            "E'": [["E"]],
            "E": [
                ["E", "+", "T"],
                ["E", "-", "T"],
                ["T"]
            ],
            "T": [
                ["T", "*", "P"],
                ["T", "/", "P"],
                ["P"]
            ],
            "P": [
                ["P", "^", "F"],
                ["exp", "[", "F", "]"],
                ["F"]
            ],
            "F": [
                ["(", "E", ")"],
                ["id"]  # PROBLEMA
            ]
        }

        self.simbolos_gramaticais = ["E'", "E", "T", "P", "F", "+", "-", "*", "/", "^", "exp", "[", "]", "(", ")", "id"]
        self.colecao = self.regras()

    def gerar_regras_com_bolinha(self, nao_terminal): #regras do automato do livro, cap 4.5 a 4.7;
        comeco = [nao_terminal, "->"]
        regras = []
        for producao in self.gramatica[nao_terminal]:
            for i in range(len(producao)+1):
                nova_regra = producao.copy()
                nova_regra.insert(i, "●")  # BOLINHA!!!
                regras.append(comeco + nova_regra)
        return regras

    def CLOSURE(self, I):
        J = I.copy()
        while True:
            adicionou = False
            for regra in J:
                index = regra.index("●")
                simbolo = None
                if index != len(regra)-1:
                    simbolo = regra[index+1]
                if simbolo in self.gramatica.keys():
                    for nova_regra in self.gerar_regras_com_bolinha(simbolo):
                        if nova_regra[2] == "●" and (not nova_regra in J):
                            adicionou = True
                            J.append(nova_regra)
            if not adicionou:
                break
        return J

    def GOTO(self, I, X):
        regras_desejadas = []
        for regra in I:
            index = regra.index("●")
            if index != len(regra)-1 and regra[index+1] == X:
                nova_regra = regra.copy()
                nova_regra[index], nova_regra[index+1] = nova_regra[index+1], nova_regra[index]
                regras_desejadas.append(nova_regra)
        return self.CLOSURE(regras_desejadas)

    def regras(self): #coleçao canonica
        C = [self.CLOSURE([["E'", "->", "●", "E"]])]
        index = -1
        while True:
            novo_set_add = False
            for I in C:
                index += 1
                for X in self.simbolos_gramaticais:
                    goto = self.GOTO(I, X)
                    if len(goto) > 0 and (not goto in C):
                        novo_set_add = True
                        C.append(goto)
            if not novo_set_add:
                break

        return C

    ##def FOLLOW(self, nao_terminal): ##NÃO UTILIZADO
        ##if nao_terminal == "E":
            ##return ["+", "-", ")"]
        ##elif nao_terminal == "T":
            ##return ["*", "/", "+", "-", ")"]
        ##elif nao_terminal == "P":
            ##return ["^", "*", "/", "+", "-", ")"]
        ##elif nao_terminal == "F":
            ##return ["]", "^", "*", "/", "+", "-", ")"]
        ##else:
            ##return None

    def is_terminal(self, a):
        return a in ['+', '-', '*', '/', '^', 'exp', '(', ')', '[', ']', 'id']

    def ACTION(self, i, a): #SHIFT, REDUCE, ERROR, ACCEPT
        I = self.colecao[i]

        goto = self.GOTO(I, a.id)

        if self.is_terminal(a.id) and goto in self.colecao:
            j = self.colecao.index(goto)
            return ["shift", j]

        regras = I.copy()
        reducao = None
        for regra in regras:
            if regra[-1] == "●":
                reducao = regra.copy()
                reducao.remove("●")
                break

        if reducao != None and reducao[0] != "E'":
            return ["reduce", reducao]

        if reducao != None and reducao[0] == "E'" and a.id == "$":
            return ["accept"]

        return None

    def executar(self, lista_tokens):
        pilha_estados = [0]
        pilha_ops = []
        lista_tokens_index = 0
        a = lista_tokens[lista_tokens_index]

        print("%-45s%-45s%-45s%-45s" % ("STACK", "INPUT", "ACTION", "PILHA OPS"))

        while True:
            s = pilha_estados[-1]
            action = self.ACTION(s, a)

            if action == None:
                print("ERRO")
                print(s)
                print(a)
                break

            if action[0] == "shift" or action[0] == "accept":
                print("%-45s%-45s%-45s%-45s" % (pilha_estados, list(lista_tokens[lista_tokens_index:]), action[0], pilha_ops))
            elif action[0] == "reduce":
                print("%-45s%-45s%-45s%-45s" % (pilha_estados, list(lista_tokens[lista_tokens_index:]), action[0] + " by " + " ".join(action[1]), pilha_ops))

            if action[0] == "shift":
                pilha_estados.append(action[1])

                # pega a leitura para rodar o codigo depois
                if a.id == "id":
                    pilha_ops.append(a.value)
                else:
                    pilha_ops.append(a.id)

                lista_tokens_index += 1
                if lista_tokens_index > len(lista_tokens) - 1:
                    a.id = "$"
                else:
                    a = lista_tokens[lista_tokens_index]
            elif action[0] == "reduce":
                num_simbolos = len(action[1]) - 2

                for _ in range(num_simbolos):
                    pilha_estados.pop()

                goto = self.colecao.index(self.GOTO(self.colecao[pilha_estados[-1]], action[1][0]))
                pilha_estados.append(goto)

                producao = action[1]
                if producao == ["P", "->", "P", "^", "F"]:
                    f = float(pilha_ops.pop())
                    pot = pilha_ops.pop()
                    p = float(pilha_ops.pop())
                    result = p ** f
                    pilha_ops.append(result)
                elif producao == ["T", "->", "T", "*", "P"]:
                    p = float(pilha_ops.pop())
                    vezes = pilha_ops.pop()
                    t = float(pilha_ops.pop())
                    result = t * p
                    pilha_ops.append(result)
                elif producao == ["E", "->", "E", "+", "T"]:
                    t = float(pilha_ops.pop())
                    adi = pilha_ops.pop()
                    e = float(pilha_ops.pop())
                    result = e + t
                    pilha_ops.append(result)
                elif producao == ["T", "->", "T", "/", "P"]:
                    p = float(pilha_ops.pop())
                    divi = pilha_ops.pop()
                    t = float(pilha_ops.pop())
                    result = t / p
                    pilha_ops.append(result)
                elif producao == ["E", "->", "E", "-", "T"]:
                    t = float(pilha_ops.pop())
                    menos = pilha_ops.pop()
                    e = float(pilha_ops.pop())
                    result = e - t
                    pilha_ops.append(result)
                elif producao == ["P", "->", "exp", "[", "F", "]"]:
                    _ = pilha_ops.pop()
                    f = float(pilha_ops.pop())
                    _ = pilha_ops.pop()
                    exp = pilha_ops.pop()
                    result = math.exp(f)
                    pilha_ops.append(result)
                elif producao == ["F", "->", "(", "E", ")"]:
                    _ = pilha_ops.pop()
                    e = float(pilha_ops.pop())
                    _ = pilha_ops.pop()
                    pilha_ops.append(e)
            elif action[0] == "accept":
                print("FUNCIONOU!!!")
                break
            else:
                print("ERRO GRAVE")
                break

        print("RESULTADO FINAL: ", pilha_ops[0])


entrada = input('Digite o input: ')
analyzer = LexicalAnalyzer(entrada)
anal_sin = AnalisadorSintatico()
anal_sin.executar(analyzer.get_all_tokens())

