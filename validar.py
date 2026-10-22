"""Valida un CSV: volumen, nulos y duplicados por clave de negocio.

Uso: python scripts/validar.py <fichero.csv> <col_clave> [<col_clave> ...]

Ejemplo: python scripts/validar.py datos.csv id_contador ts
"""

import argparse
import sys

import pandas as pd

from validador_tabla import ValidadorTabla

MAX_FILAS_DUPLICADOS = 10  # no inundar el contexto con miles de filas


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida la calidad de un CSV (volumen, nulos, duplicados)."
    )
    parser.add_argument("fichero", help="Ruta del fichero CSV")
    parser.add_argument(
        "clave",
        nargs="+",
        help="Columna(s) que forman la clave de negocio (p. ej. id_contador ts)",
    )
    return parser.parse_args()


def error(mensaje: str) -> int:
    """Escribe un error claro en stderr y devuelve el código de salida 1."""
    print(f"ERROR: {mensaje}", file=sys.stderr)
    return 1


def mostrar_volumen(validador: ValidadorTabla, df: pd.DataFrame) -> None:
    resumen = validador.resumen()
    print("== VOLUMEN ==")
    print(f"filas: {resumen['filas']}")
    print(f"columnas: {resumen['columnas']} ({', '.join(map(str, df.columns))})")


def mostrar_nulos(validador: ValidadorTabla, filas: int, clave: list[str]) -> None:
    print("== NULOS ==")

    con_nulos = [(col, n) for col, n in validador.nulos().items() if n > 0]
    if not con_nulos:
        print("ninguno")
        return

    # Mayor a menor; el sort es estable, así que los empates conservan
    # el orden de las columnas del fichero (salida determinista).
    con_nulos.sort(key=lambda par: par[1], reverse=True)

    for col, n in con_nulos:
        marca = " [CLAVE]" if col in clave else ""
        print(f"{col}: {n} de {filas} ({n / filas * 100:.1f}%){marca}")


def mostrar_duplicados(
    validador: ValidadorTabla, df: pd.DataFrame, clave: list[str]
) -> None:
    print("== DUPLICADOS ==")

    repetidas = validador.duplicados(clave)
    if repetidas.empty:
        print(f"ninguno (clave: {', '.join(clave)})")
        return

    sobrantes = int(df.duplicated(subset=clave).sum())
    print(f"clave: {', '.join(clave)}")
    print(f"filas implicadas: {len(repetidas)}")
    print(f"filas sobrantes: {sobrantes}")

    for indice, fila in repetidas.head(MAX_FILAS_DUPLICADOS).iterrows():
        campos = ", ".join(
            f"{col}={'nulo' if pd.isna(valor) else valor}"
            for col, valor in fila.items()
        )
        print(f"fila {indice}: {campos}")

    if len(repetidas) > MAX_FILAS_DUPLICADOS:
        print(f"mostrando {MAX_FILAS_DUPLICADOS} de {len(repetidas)}")


def main() -> int:
    args = parsear_argumentos()

    try:
        df = pd.read_csv(args.fichero)
    except FileNotFoundError:
        return error(f"el fichero '{args.fichero}' no existe")
    except pd.errors.EmptyDataError:
        return error(f"el fichero '{args.fichero}' está vacío")
    except pd.errors.ParserError as exc:
        return error(f"el CSV está mal formado: {exc}")
    except UnicodeDecodeError:
        return error(f"el fichero '{args.fichero}' no está codificado en UTF-8")

    faltan = [col for col in args.clave if col not in df.columns]
    if faltan:
        return error(
            f"columnas de la clave no encontradas: {faltan}. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    validador = ValidadorTabla(df, nombre=args.fichero)

    # Mismo orden que en SKILL.md: volumen, nulos, duplicados.
    mostrar_volumen(validador, df)
    mostrar_nulos(validador, len(df), args.clave)
    mostrar_duplicados(validador, df, args.clave)
    return 0


if __name__ == "__main__":
    sys.exit(main())
