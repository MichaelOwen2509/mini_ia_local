import numpy as np

from text import tokenizar


# ============================================================
# DADOS DE TREINAMENTO
# ============================================================

FRASES = [

    # PREÇO
    "quanto custa",
    "qual o preço",
    "preço do produto",
    "quanto vale",
    "qual o valor",
    "qual é o valor",
    "quanto é",
    "quanto custa o produto",
    "por quanto vende",
    "qual o preço do produto",
    "quanto eu pago",
    "quanto vou pagar",
    "me diga o preço",
    "me diga o valor",

    # QUANTIDADE
    "quantos temos",
    "qual a quantidade",
    "tem quantos",
    "quantidade do produto",
    "quantas unidades temos",
    "quantas unidades tem",
    "quantas unidades existem",
    "quantos produtos temos",
    "quantos produtos tem",
    "temos quantos",
    "temos quantas unidades",
    "quanto temos",
    "quanto de produto temos",
    "quantas peças temos",
    "quantas peças tem",
    "tem produto",
    "temos produto",
    "existe produto",

    # LOCALIZAÇÃO
    "onde está",
    "onde fica",
    "qual a localização",
    "localização do produto",
    "onde está o produto",
    "onde fica o produto",
    "em qual lugar está",
    "em que lugar está",
    "onde guardamos",
    "onde está guardado",
    "onde está armazenado",
    "qual o local",
    "qual é o local",
    "me diga onde está",

    # FORNECEDOR
    "qual o fornecedor",
    "qual é o fornecedor",
    "fornecedor do produto",
    "quem fornece",
    "quem é o fornecedor",
    "quem fornece o produto",
    "de quem compramos",
    "onde compramos",
    "qual empresa fornece",
    "empresa fornecedora",
    "me diga o fornecedor",
    "quem vende o produto",
    "quem vende",
    "qual fornecedor temos",
    "quem é responsável por fornecer",
    "quem é responsável por fornecer o produto",
    "quem é responsável pelo fornecimento",
    "qual empresa é responsável pelo fornecimento",
    "quem fez o fornecimento",
    "qual empresa forneceu",

    # ÚLTIMA COMPRA
    "qual a data da última compra",
    "qual é a data da última compra",
    "data da última compra",
    "quando foi a última compra",
    "quando compramos",
    "quando compramos o produto",
    "quando foi comprado",
    "quando o produto foi comprado",
    "última compra",
    "data da compra",
    "qual a data da compra",
    "qual foi a última compra",
    "quando foi nossa última compra",
    "data da última compra do produto",
        # CATEGORIA
    "qual a categoria",
    "qual é a categoria",
    "categoria do produto",
    "qual a categoria do produto",
    "em qual categoria está",
    "em que categoria está",
    "qual o tipo do produto",
    "qual é o tipo do produto",
    "que tipo de produto é",
    "que tipo de produto",
    "qual o tipo",
    "me diga a categoria",
    "me diga o tipo do produto",
    "a qual categoria pertence",
    "como é classificado",
    "como o produto é classificado",
    "como esse produto é classificado",
    "como se classifica o produto",
    "qual a classificação do produto",

        # DESCONHECIDO
    "quem é o presidente",
    "quem descobriu o brasil",
    "qual a capital do brasil",
    "me conte uma piada",
    "conte uma piada",
    "como faço um bolo",
    "qual a previsão do tempo",
    "como está o tempo",
    "qual a distância até são paulo",
    "me conte uma história",
    "qual o significado dessa palavra",
    "como funciona um avião",
    "quem inventou a televisão",
    "qual a população do brasil",
    "me fale sobre futebol",
    "qual a idade da terra",
    "como faço café",
    "qual o maior país do mundo",
    "me ensine matemática",
    "o que é inteligência artificial"
]


INTENCOES = [
    "preco",
    "quantidade",
    "localizacao",
    "fornecedor",
    "ultima_compra",
    "categoria",
    "desconhecido"
]


ALVOS = np.array(
    [0] * 14 +
    [1] * 18 +
    [2] * 14 +
    [3] * 20 +
    [4] * 14 +
    [5] * 19 +
    [6] * 20
)

class RedeNeural:

    def __init__(self):

        self.vocabulario = sorted({
            palavra
            for frase in FRASES
            for palavra in tokenizar(frase)
        })

        self.palavra_para_id = {
            palavra: i
            for i, palavra in enumerate(self.vocabulario)
        }

        entrada = len(self.vocabulario)
        ocultos = 8
        saida = len(INTENCOES)

        np.random.seed(42)

        self.W1 = np.random.randn(entrada, ocultos) * 0.1
        self.b1 = np.zeros(ocultos)

        self.W2 = np.random.randn(ocultos, saida) * 0.1
        self.b2 = np.zeros(saida)

    def vetorizar(self, frase):

        vetor = np.zeros(len(self.vocabulario))

        for palavra in tokenizar(frase):

            if palavra in self.palavra_para_id:
                vetor[self.palavra_para_id[palavra]] = 1

        return vetor

    @staticmethod
    def softmax(x):

        x = x - np.max(x)

        exp = np.exp(x)

        return exp / np.sum(exp)

    def treinar(self, epocas=2000, taxa_aprendizado=0.1):

        X = np.array([
            self.vetorizar(frase)
            for frase in FRASES
        ])

        for epoca in range(epocas):

            erro_total = 0

            for i in range(len(X)):

                x = X[i]

                # FORWARD

                z1 = x @ self.W1 + self.b1

                a1 = np.maximum(0, z1)

                z2 = a1 @ self.W2 + self.b2

                y = self.softmax(z2)

                alvo = ALVOS[i]

                # LOSS

                erro = -np.log(y[alvo] + 1e-9)

                erro_total += erro

                # BACKPROPAGATION

                dz2 = y.copy()

                dz2[alvo] -= 1

                dW2 = np.outer(a1, dz2)

                db2 = dz2

                da1 = dz2 @ self.W2.T

                dz1 = da1 * (z1 > 0)

                dW1 = np.outer(x, dz1)

                db1 = dz1

                # ATUALIZAÇÃO DOS PESOS

                self.W2 -= taxa_aprendizado * dW2
                self.b2 -= taxa_aprendizado * db2

                self.W1 -= taxa_aprendizado * dW1
                self.b1 -= taxa_aprendizado * db1

            if epoca % 500 == 0:

                print(
                    f"Época {epoca} | "
                    f"erro: {erro_total:.4f}"
                )

    def salvar(self, caminho="modelo_rede.npz"):
        """Salva os pesos e o vocabulário da rede para uso posterior."""
        np.savez(
            caminho,
            W1=self.W1,
            b1=self.b1,
            W2=self.W2,
            b2=self.b2,
            vocabulario=np.array(self.vocabulario, dtype=object)
        )

    @classmethod
    def carregar(cls, caminho="modelo_rede.npz"):
        """Carrega uma rede previamente treinada."""
        dados = np.load(caminho, allow_pickle=True)

        rede = cls.__new__(cls)
        rede.vocabulario = dados["vocabulario"].tolist()
        rede.palavra_para_id = {
            palavra: i
            for i, palavra in enumerate(rede.vocabulario)
        }

        rede.W1 = dados["W1"]
        rede.b1 = dados["b1"]
        rede.W2 = dados["W2"]
        rede.b2 = dados["b2"]

        return rede

    def prever(self, frase):

        x = self.vetorizar(frase)

        if np.sum(x) == 0:
            return None, 0.0

        z1 = x @ self.W1 + self.b1

        a1 = np.maximum(0, z1)

        z2 = a1 @ self.W2 + self.b2

        probabilidades = self.softmax(z2)

        indice = np.argmax(probabilidades)

        confianca = probabilidades[indice]

        if confianca < 0.75:
            return None, confianca

        return INTENCOES[indice], confianca