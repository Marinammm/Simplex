import numpy
import sys

# le o arquivo e inicializa as variaveis
entrada = open(sys.argv[1], "r")
s = entrada.read()
s = s.split('\n')
i = 0
modo = s[i]
i += 1
if modo == "modo 2":
    tipo = s[i]
    i += 1
originalLines = int(s[i])
lines = originalLines + 1
i += 1
originalColumns = int(s[i])
columns = originalColumns + 1
i += 1
PL = s[i].replace("{", "[")
PL = PL.replace("}", "]")
PL = numpy.array(eval(PL))
PL = PL.astype(float)

# coloca uma matriz identidade na PL a partir da coluna especificada
def insertIdentity(matriz, column, lines, originalLines):
    vector = numpy.zeros(originalLines)
    matriz = numpy.insert(matriz, [column], [vector], axis=1)
    for i in range(1, lines):
        matriz[i][column] = 1
        column += 1
    return matriz


# deve ser chamada sempre depois de uma funcao que modifica a quantidade
# de colunas da PL, como makeFPI e makeTableau
def updateNumberColumns(columns, lines):
    columns += lines
    return columns


# coloca em FPI nos casos em que b > 0
# se b < 0, nao corrige
def makeFPI(PL, column, lines, originalLines):
    PL = insertIdentity(PL, column, lines, originalLines)
    return PL


# adiciona a matriz de operacoes a esquerda e nega c
def makeTableau(FPI, lines, originalLines):
    FPI[0] = -FPI[0]
    FPI = insertIdentity(FPI, 0, lines, originalLines)
    return FPI


def needsAuxiliar(FPI, columns, lines):
    for i in range(lines):
        if FPI[i][columns-1] < 0:
            return True
    return False


# corrige b < 0, monta o tableau completo da PL auxiliar
def makeAuxiliar(PL, columns, lines, originalLines):
    PL = insertIdentity(PL, 0, lines, originalLines)
    columns = updateNumberColumns(columns, originalLines)
    for i in range(lines):
        if PL[i][columns-1] < 0:
            PL[i] = -PL[i]
    PL = insertIdentity(PL, columns-1, lines, originalLines)
    PL[0] = 0
    for i in range(originalLines):
        PL[0][columns-1+i] = 1
    return PL

# usar antes de rodar o simplex, quando a base e obvia olhando o tableau
def getBase(PL, lines, columns):
    base = []
    for i in range(lines):
        base.append(columns-1-lines+i)
    return base


def getPivotColumn(matriz, columns, originalLines):
    for i in range(originalLines, columns-1):
        if matriz[0][i] < 0:
            return i
    return 0


def getPivotLine(matriz, lines, columns, c):
    less = 99999999999999999  # numero arbitrariamente grande
    line = 0
    for i in range(1, lines):
        if matriz[i][c] > 0:
            if matriz[i][columns]/matriz[i][c] < less:
                less = matriz[i][columns]/matriz[i][c]
                line = i
    return line


def pivot(tableau, lines, columns, c, l):
    tableau[l] = tableau[l]/tableau[l][c]
    for i in range(l):
        x = -tableau[i][c]
        tableau[i] = tableau[i] + tableau[l] * x
    for i in range(l+1, lines):
        x = -tableau[i][c]
        tableau[i] = tableau[i] + tableau[l] * x
    # arredonda para 5 casas decimais
    for i in range(lines):
        for j in range(columns):
            tableau[i][j] = round(tableau[i][j], 5)
    tableau = tableau.astype(float)
    return tableau


def simplexPrimal(tableau, lines, originalLines, columns, base, modo):
    if modo == 2:
        print tableau, '\n'
    c = getPivotColumn(tableau, columns, originalLines)
    while c > 0:  # enquanto houver valores negativos no vetor c
        l = getPivotLine(tableau, lines, columns-1, c)
        if l == 0:  # nao encontrou elemento positivo na coluna
            certificado = getCertificadoIlimitada(tableau, originalLines, columns, c, base)
            print "PL ilimitada, aqui esta um certificado: ", certificado
            return None
        tableau = pivot(tableau, lines, columns, c, l)
        if modo == 2:
            for i in range(lines):
                for j in range(columns):
                    tableau[i][j] = round(tableau[i][j], 5)
            print tableau, '\n'
        base[l-1] = c
        c = getPivotColumn(tableau, columns, originalLines)
    return tableau


def simplexPrimalAuxiliar(tableau, lines, originalLines, columns, base):
    # zera vetor c nas entradas da base
    for i in range(1, lines):
        tableau[0] += -tableau[i]
    # inicia o simplex
    c = getPivotColumn(tableau, columns, originalLines)
    while c > 0:
        l = getPivotLine(tableau, lines, columns-1, c)
        if l == 0:
            break
        tableau = pivot(tableau, lines, columns, c, l)
        base[l-1] = c
        c = getPivotColumn(tableau, columns,  originalLines)
    return tableau


# confere se a PL original e viavel a partir da auxiliar
def isViable(tableau, columns):
    if tableau[0][columns-1] < 0:
        return False
    return True


# apos o simplex da auxiliar, arruma o tableau para comecar o simplex na
# PL original
def returnToOriginal(tableau, PL, lines, originalLines, columns, base):
    # tira as colunas da base original da PL auxiliar
    for i in range(originalLines):
        tableau = numpy.delete(tableau, columns-2, 1)
        columns -= 1
    # coloca o vator c original
    tableau[0, originalLines:] = -PL[0]
    # zera o vetor c nas entradas da base atual
    for i in range(originalLines):
        tableau = pivot(tableau, lines, columns, base[i], i+1)
    return tableau


# retorna o vetor solucao da PL
def getSolution(tableau, lines, columns, originalColumns, base):
    for i in range(lines):
        for j in range(columns):
            tableau[i][j] = round(tableau[i][j], 5)
    solution = numpy.zeros(columns-lines-1)
    for i in range(lines):
        solution[base[i]-lines] = tableau[i+1][columns-1]
    solution = solution[:originalColumns]
    return solution


# funciona pro certificado de inviabilidade e pra solucao da dual
def getCertificado(tableau, lines):
    for i in range(lines):
        for j in range(columns):
            tableau[i][j] = round(tableau[i][j], 5)
    return tableau[0, :lines]


def getCertificadoIlimitada(tableau, lines, columns, c, base):
    for i in range(lines):
        for j in range(columns):
            tableau[i][j] = round(tableau[i][j], 5)
    certificado = numpy.zeros(columns-lines-1)
    certificado[c-lines] = 1
    for i in range(lines):
        certificado[base[i]-lines] = -tableau[i+1][c]
    return certificado

# encontra a linha do elemento a ser pivoteada no simplex dual
def getLineDual(tableau, lines, columns):
    for i in range(1, lines):
        if tableau[i][columns-1] < 0:
            return i
    return 0

# encontra a coluna do elemento a ser pivoteado no simplex dual
def getColumnDual(tableau, originalLines, columns, l):
    less = 99999999999999999  # numero arbitrariamente grande
    c = 0
    for i in range(originalLines, columns-1):
        if tableau[l][i] < 0:
            if tableau[0][i]/-tableau[l][i] < less:
                less = tableau[0][i]/-tableau[l][i]
                c = i
    return c


def simplexDual(tableau, lines, originalLines, columns):
    print tableau, '\n'
    l = getLineDual(tableau, lines, columns)
    while l > 0:
        c = getColumnDual(tableau, originalLines, columns, l)
        if c == 0:  # nao encontrou elemento negativo na linha
            break
        tableau = pivot(tableau, lines, columns, c, l)
        for i in range(lines):
            for j in range(columns):
                tableau[i][j] = round(tableau[i][j], 5)
        print tableau, '\n'
        l = getLineDual(tableau, lines, columns)
    return tableau


def modo1(PL, originalLines, originalColumns, lines, columns, modo):
    FPI = makeFPI(PL, originalColumns, lines, originalLines)
    columns = updateNumberColumns(columns, originalLines)

    # roda a auxiliar se algum b for negativo
    if needsAuxiliar(FPI, columns, lines):
        auxiliar = makeAuxiliar(FPI, columns, lines, originalLines)
        columns = updateNumberColumns(columns, 2*originalLines)
        base = getBase(auxiliar, originalLines, columns)
        auxiliar = simplexPrimalAuxiliar(auxiliar, lines, originalLines, columns, base)
        # Lida com o resultado do simplex da PL auxiliar
        if isViable(auxiliar, columns):
            tableau = returnToOriginal(auxiliar, FPI, lines, originalLines, columns, base)
            columns -= originalLines
        else:
            certificado = getCertificado(auxiliar, originalLines)
            print "PL inviavel, aqui esta um certificado: ", certificado

    # caso a PL auxiliar nao seja necessaria
    else:
        tableau = makeTableau(FPI, lines, originalLines)
        columns = updateNumberColumns(columns, originalLines)
        base = getBase(tableau, originalLines, columns)

    # roda o simplex primal na PL original
    tableau = simplexPrimal(tableau, lines, originalLines, columns, base, modo)

    # caso em que a PL tem solucao otima
    if tableau is not None:
        dual = getCertificado(tableau, originalLines)
        solution = getSolution(tableau, originalLines, columns, originalColumns, base)
        otimo = tableau[0][columns-1]
        print "Solucao otima x = ", solution, "com valor objetivo ", otimo, "e solucao dual y = ", dual


def modo2(PL, originalLines, originalColumns, lines, columns, modo, tipo):
    if tipo == "P":
        # faz o mesmo que o modo 1, mas imprime os passos do simplex primal
        modo1(PL, originalLines, originalColumns, lines, columns, modo)
    elif tipo == "D":
        # roda o simplex dual
        FPI = makeFPI(PL, originalColumns, lines, originalLines)
        columns = updateNumberColumns(columns, originalLines)
        tableau = makeTableau(FPI, lines, originalLines)
        columns = updateNumberColumns(columns, originalLines)
        tableau = simplexDual(tableau, lines, originalLines, columns)


if modo == "modo 1":
    modo1(PL, originalLines, originalColumns, lines, columns, 1)
elif modo == "modo 2":
    modo2(PL, originalLines, originalColumns, lines, columns, 2, tipo)
entrada.close()
