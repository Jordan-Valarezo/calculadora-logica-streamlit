import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")
st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará exclusivamente en 0 y 1.")

# Las variables coinciden con los botones del constructor.
VARIABLES = ["P", "B", "C", "D", "E", "F"]

if "expr" not in st.session_state:
    st.session_state.expr = ""

st.subheader("🧩 Constructor de Expresión")
cols = st.columns(6)
for i, variable in enumerate(VARIABLES):
    with cols[i]:
        if st.button(variable, key=f"btn_{variable}", use_container_width=True):
            st.session_state.expr += f" {variable} "

st.markdown("---")
st.subheader("＋ Operadores")
operadores = ["AND", "OR", "NOT", "XOR", "->", "<->", "(", ")"]
cols = st.columns(4)

for i, op in enumerate(operadores):
    with cols[i % 4]:
        if st.button(op, key=f"btn_{op}", use_container_width=True):
            if op == "(":
                st.session_state.expr += " ( "
            elif op == ")":
                st.session_state.expr += " ) "
            elif op == "NOT":
                st.session_state.expr += " NOT "
            else:
                st.session_state.expr += f" {op} "

col_limpiar, col_preview = st.columns([1, 2])
with col_limpiar:
    if st.button("🧹 Limpiar", use_container_width=True):
        st.session_state.expr = ""
with col_preview:
    st.code(st.session_state.expr.strip() or "(vacío)", language="text")


def tokenizar(expresion):
    """Convierte la expresión en tokens y rechaza cualquier símbolo desconocido."""
    patron = re.compile(r"\s*(<->|->|AND\b|OR\b|NOT\b|XOR\b|[PBCDEF()] )", re.IGNORECASE)
    # Se usa un patrón sin espacios dentro de los tokens.
    patron = re.compile(r"\s*(<->|->|AND\b|OR\b|NOT\b|XOR\b|[PBCDEF()])", re.IGNORECASE)
    tokens = []
    posicion = 0

    while posicion < len(expresion):
        coincidencia = patron.match(expresion, posicion)
        if not coincidencia:
            if expresion[posicion:].strip() == "":
                break
            raise ValueError(f"Símbolo no válido cerca de: {expresion[posicion:posicion+10]}")
        tokens.append(coincidencia.group(1).upper())
        posicion = coincidencia.end()

    if not tokens:
        raise ValueError("La expresión está vacía.")
    return tokens


class AnalizadorLogico:
    """Evalúa expresiones respetando la precedencia de los operadores."""

    def __init__(self, tokens, valores):
        self.tokens = tokens
        self.valores = valores
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def aceptar(self, token):
        if self.actual() == token:
            self.pos += 1
            return True
        return False

    def analizar(self):
        resultado = self.equivalencia()
        if self.actual() is not None:
            raise ValueError(f"Token inesperado: {self.actual()}")
        return bool(resultado)

    # Precedencia: NOT, AND, XOR, OR, ->, <->
    def equivalencia(self):
        izquierda = self.implicacion()
        while self.aceptar("<->"):
            derecha = self.implicacion()
            izquierda = (izquierda == derecha)
        return izquierda

    def implicacion(self):
        izquierda = self.disyuncion()
        if self.aceptar("->"):
            derecha = self.implicacion()
            return (not izquierda) or derecha
        return izquierda

    def disyuncion(self):
        izquierda = self.xor()
        while self.aceptar("OR"):
            derecha = self.xor()
            izquierda = izquierda or derecha
        return izquierda

    def xor(self):
        izquierda = self.conjuncion()
        while self.aceptar("XOR"):
            derecha = self.conjuncion()
            izquierda = (izquierda != derecha)
        return izquierda

    def conjuncion(self):
        izquierda = self.unario()
        while self.aceptar("AND"):
            derecha = self.unario()
            izquierda = izquierda and derecha
        return izquierda

    def unario(self):
        if self.aceptar("NOT"):
            return not self.unario()

        if self.aceptar("("):
            resultado = self.equivalencia()
            if not self.aceptar(")"):
                raise ValueError("Falta cerrar un paréntesis.")
            return resultado

        token = self.actual()
        if token in VARIABLES:
            self.pos += 1
            return bool(self.valores[token])

        if token is None:
            raise ValueError("La expresión está incompleta.")
        raise ValueError(f"Se esperaba una variable, pero se encontró: {token}")


def generar_tabla(expresion):
    tokens = tokenizar(expresion)
    variables_usadas = [v for v in VARIABLES if v in tokens]

    if not variables_usadas:
        raise ValueError("No se detectaron variables.")

    # Comprobación de sintaxis para cada combinación de valores.
    filas = []
    for combinacion in product([0, 1], repeat=len(variables_usadas)):
        entorno = dict(zip(variables_usadas, combinacion))
        resultado = AnalizadorLogico(tokens, entorno).analizar()
        filas.append(list(combinacion) + [int(resultado)])

    return variables_usadas, filas


if st.button("📊 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        try:
            vars_, tabla = generar_tabla(st.session_state.expr)
            columnas = vars_ + ["Resultado"]
            df = pd.DataFrame(tabla, columns=columnas)
            st.success(f"✅ Tabla generada para {len(vars_)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar CSV",
                data=csv,
                file_name="tabla_verdad.csv",
                mime="text/csv"
            )
        except ValueError as error:
            st.error(f"❌ Expresión inválida: {error}")
