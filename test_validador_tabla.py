"""Tests de ValidadorTabla (TDD: primero los tests, luego la clase).

Ejecutar:  pytest -q
La clase debe vivir en validador_tabla.py, en la misma carpeta.
"""

import pandas as pd
import pytest

from validador_tabla import ValidadorTabla


@pytest.fixture
def df_lecturas() -> pd.DataFrame:
    """5 filas, 4 columnas.

    - Filas 0 y 1: idénticas (duplicado completo y duplicado por clave).
    - Nulos: 1 en kwh, 2 en region (3 en total).
    """
    return pd.DataFrame(
        {
            "id_contador": ["C1", "C1", "C2", "C3", "C3"],
            "ts": [
                "2026-10-01",
                "2026-10-01",
                "2026-10-01",
                "2026-10-01",
                "2026-10-02",
            ],
            "kwh": [1.2, 1.2, None, 40.1, 38.7],
            "region": ["Málaga", "Málaga", "Sevilla", None, None],
        }
    )


@pytest.fixture
def validador(df_lecturas: pd.DataFrame) -> ValidadorTabla:
    return ValidadorTabla(df_lecturas, nombre="lecturas")


# ---------- Constructor ----------


def test_constructor_rechaza_algo_que_no_es_dataframe():
    with pytest.raises(TypeError):
        ValidadorTabla([1, 2, 3])


def test_constructor_guarda_el_nombre(validador):
    assert validador.nombre == "lecturas"


# ---------- nulos() ----------


def test_nulos_devuelve_una_serie_con_todas_las_columnas(validador, df_lecturas):
    resultado = validador.nulos()
    assert isinstance(resultado, pd.Series)
    assert set(resultado.index) == set(df_lecturas.columns)


def test_nulos_cuenta_bien_por_columna(validador):
    resultado = validador.nulos()
    assert resultado["kwh"] == 1
    assert resultado["region"] == 2
    assert resultado["id_contador"] == 0
    assert resultado["ts"] == 0


# ---------- duplicados(clave) ----------


def test_duplicados_devuelve_todas_las_filas_repetidas(validador):
    resultado = validador.duplicados(["id_contador", "ts"])
    assert isinstance(resultado, pd.DataFrame)
    # Se devuelven las dos apariciones (no solo la segunda)
    assert len(resultado) == 2
    assert list(resultado.index) == [0, 1]


def test_duplicados_respeta_la_clave_elegida(validador):
    # Solo por id_contador se repiten C1 (x2) y C3 (x2) -> 4 filas
    resultado = validador.duplicados(["id_contador"])
    assert len(resultado) == 4


def test_duplicados_vacio_si_la_clave_es_unica():
    sin_repetidos = ValidadorTabla(pd.DataFrame({"a": [1, 2, 3]}))
    assert sin_repetidos.duplicados(["a"]).empty


def test_duplicados_lanza_keyerror_si_la_clave_no_existe(validador):
    with pytest.raises(KeyError):
        validador.duplicados(["columna_inexistente"])


def test_duplicados_no_modifica_el_dataframe_original(df_lecturas):
    copia = df_lecturas.copy()
    ValidadorTabla(df_lecturas).duplicados(["id_contador", "ts"])
    pd.testing.assert_frame_equal(df_lecturas, copia)


# ---------- resumen() ----------


def test_resumen_devuelve_las_metricas_esperadas(validador):
    assert validador.resumen() == {
        "filas": 5,
        "columnas": 4,
        "nulos_totales": 3,
        "duplicados_completos": 2,  # la fila 1 es copia de la 0
    }


def test_resumen_de_dataframe_vacio():
    vacio = ValidadorTabla(pd.DataFrame({"a": []}))
    assert vacio.resumen() == {
        "filas": 0,
        "columnas": 1,
        "nulos_totales": 0,
        "duplicados_completos": 0,
    }


def test_resumen_devuelve_enteros_de_python(validador):
    # Evita np.int64 en el dict (importante si luego lo serializas a JSON)
    assert all(type(v) is int for v in validador.resumen().values())
