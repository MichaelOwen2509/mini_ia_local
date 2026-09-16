import unicodedata


def normalizar(texto):
    texto = texto.lower()

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def tokenizar(texto):
    texto = normalizar(texto)

    return [
        palavra.strip(".,?!:;()[]{}\"'")
        for palavra in texto.split()
        if palavra.strip(".,?!:;()[]{}\"'")
    ]