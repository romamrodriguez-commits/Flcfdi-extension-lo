#!/usr/bin/python
import re

class NumerosLetras(object):

    def __init__(self):
        pass

    def NumerosLetras( self, numero, moneda='peso', texto_inicial='', texto_final='', fraccion_letras=False, fraccion=''):
        enletras = texto_inicial
        numero = abs(numero)
        numtmp = '%015d' % numero

        if numero < 1:
            enletras += 'cero ' + self.plural(moneda) + ' '
        else:
            enletras += self.numlet(numero)
            if numero == 1 or numero < 2:
                enletras += moneda + ' '
            elif int(''.join(numtmp[3:])) == 0 or int(''.join(numtmp[9:])) == 0:
                enletras += 'de ' + self.plural(moneda) + ' '
            else:
                enletras += self.plural(moneda) + ' '

        decimal = '%0.2f' % numero
        decimal = decimal.split('.')[1]
        #~ decimal = int((numero-int(numero))*100)
        if fraccion_letras:
            if decimal == 0:
                enletras += 'con cero ' + self.plural(fraccion)
            elif decimal == 1:
                enletras += 'con un ' + fraccion
            else:
                enletras += 'con ' + self.numlet(int(decimal)) + self.plural(fraccion)
        else:
            enletras += decimal

        enletras += texto_final
        return enletras

    def numlet(self, numero):
        numtmp = '%015d' % numero
        co1=0
        letras = ''
        leyenda = ''
        for co1 in range(0,5):
            inicio = co1*3
            cen = int(numtmp[inicio:inicio+1][0])
            dec = int(numtmp[inicio+1:inicio+2][0])
            uni = int(numtmp[inicio+2:inicio+3][0])
            letra3 = self.centena(uni, dec, cen)
            letra2 = self.decena(uni, dec)
            letra1 = self.unidad(uni, dec)

            if co1 == 0:
                if (cen+dec+uni) == 1:
                    leyenda = 'billon '
                elif (cen+dec+uni) > 1:
                    leyenda = 'billones '
            elif co1 == 1:
                if (cen+dec+uni) >= 1 and int(''.join(numtmp[6:9])) == 0:
                    leyenda = "mil millones "
                elif (cen+dec+uni) >= 1:
                    leyenda = "mil "
            elif co1 == 2:
                if (cen+dec) == 0 and uni == 1:
                    leyenda = 'millon '
                elif cen > 0 or dec > 0 or uni > 1:
                    leyenda = 'millones '
            elif co1 == 3:
                if (cen+dec+uni) >= 1:
                    leyenda = 'mil '
            elif co1 == 4:
                if (cen+dec+uni) >= 1:
                    leyenda = ''

            letras += letra3 + letra2 + letra1 + leyenda
            letra1 = ''
            letra2 = ''
            letra3 = ''
            leyenda = ''
        return letras

    def centena(self, uni, dec, cen):
        letras = ''
        numeros = ["","","doscientos ","trescientos ","cuatrocientos ","quinientos ","seiscientos ","setecientos ","ochocientos ","novecientos "]
        if cen == 1:
            if (dec+uni) == 0:
                letras = 'cien '
            else:
                letras = 'ciento '
        elif cen >= 2 and cen <= 9:
            letras = numeros[cen]
        return letras

    def decena(self, uni, dec):
        letras = ''
        numeros = ["diez ","once ","doce ","trece ","catorce ","quince ","dieci","dieci","dieci","dieci"]
        decenas = ["","","","treinta ","cuarenta ","cincuenta ","sesenta ","setenta ","ochenta ","noventa "]
        if dec == 1:
            letras = numeros[uni]
        elif dec == 2:
            if uni == 0:
                letras = 'veinte '
            elif uni > 0:
                letras = 'veinti'
        elif dec >= 3 and dec <= 9:
            letras = decenas[dec]
        if uni > 0 and dec > 2:
            letras = letras+'y '
        return letras

    def unidad(self, uni, dec):
        letras = ''
        numeros = ["","un ","dos ","tres ","cuatro ","cinco ","seis ","siete ","ocho ","nueve "]
        if dec != 1:
            if uni > 0 and uni <= 5:
                letras = numeros[uni]
        if uni >= 6 and uni <= 9:
            letras = numeros[uni]
        return letras

    def plural(self, palabra):
        if re.search('[aeiou]$', palabra):
            return re.sub('$', 's', palabra)
        else:
            return palabra + 'es'
