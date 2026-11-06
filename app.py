import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")
st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará exclusivamente en 0 y 1.")

if "expr" not in st.session_state:
    st.session_state.expr = ""

st.subheader("🧩 Constructor de Expresión")
variables = ["A", "B", "C", "D", "E", "F"]
cols = st.columns(6)
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(v, key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")
st.subheader("＋ Operadores")
operadores = ["AND", "OR", "NOT", "XOR", "->", "<->", "(", ")"]
cols = st.columns(4)
for i, op in enumerate(operadores):
    with cols[i % 4]:
        if st.button(op, key=f"btn_{op}", use_container_width=True):
            if op == "NOT":
                st.session_state.expr += " NOT "
            elif op in ["(", ")"]:
                st.session_state.expr += op
            else:
                st.session_state.expr += f" {op} "

col_limpiar, col_preview, col_gen = st.columns([2, 3, 2])
with col_limpiar:
    if st.button("🧹 Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""
with col_preview:
    st.code(st.session_state.expr.strip() or "(vacío)", language="text")

def normalizar_expresion(expr: str) -> str:
    e = expr.strip().upper()
    e = re.sub(r"\bAND\b", " and ", e)
    e = re.sub(r"\bOR\b", " or ", e)
    e = re.sub(r"\bNOT\b", " not ", e)
    e = re.sub(r"\bXOR\b", " != ", e)
    e = re.sub(r"\b([A-F])\s*->\s*([A-F])\b", r"(not \1 or \2)", e)
    e = re.sub(r"\b([A-F])\s*<->\s*([A-F])\b", r"(\1 == \2)", e)
    return re.sub(r"\s+", " ", e).strip()

def extraer_variables(expr: str) -> list:
    return sorted(set(re.findall(r"\b[A-F]\b", expr)))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_norm)
    if not variables:
        return [], []

    # Solo se permiten variables, operadores lógicos y paréntesis.
    permitido = re.fullmatch(r"[\sA-Fa-f()=!<>]+|[\sA-Fa-f()=!<>]+", expr_norm)
    if not permitido:
        return [], []

    tabla = []
    for valores in product([0, 1], repeat=len(variables)):
        entorno = {v: bool(val) for v, val in zip(variables, valores)}
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            fila = list(valores) + [int(bool(resultado))]
            tabla.append(fila)
        except Exception:
            return [], []
    return variables, tabla

if st.button("📊 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars_, tabla = generar_tabla(st.session_state.expr)
        if not vars_ or not tabla:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            columnas = vars_ + ["Resultado"]
            df = pd.DataFrame(tabla, columns=columnas)
            st.success(f"✅ Tabla generada para {len(vars_)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar CSV",
                csv,
                "tabla_verdad.csv",
                "text/csv"
            )
