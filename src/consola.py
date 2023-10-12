class Console:
    texto_estatico = ""

    def __init__(self):
        self.consola = Console.texto_estatico
    
    def escribir(self, texto):
        self.consola += texto + "\n"
        Console.texto_estatico = self.consola

    def getConsola(self):
        return self.consola

    def limpiar(self):
        self.consola = ""
        Console.texto_estatico = ""
    