import unicodedata

def unicode_tokenizer(text):
    tokens = []
    current = []

    for char in unicodedata.normalize("NFC", str(text)).lower():
        category = unicodedata.category(char)

        if char.isalnum() or category.startswith("M"):
            current.append(char)
        else:
            if current:
                tokens.append("".join(current))
                current = []

    if current:
        tokens.append("".join(current))

    return tokens