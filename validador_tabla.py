import pandas as pd


class ValidadorTabla:
    """Validaciones básicas de calidad sobre un DataFrame de pandas."""

    def __init__(self, df: pd.DataFrame, nombre: str = "tabla") -> None:
        """Guarda el DataFrame y el nombre. TypeError si df no es un DataFrame."""
        if type(df) != pd.DataFrame:
            raise TypeError("El archivo que ha pasado no es del tipo indicado")

        self.dataframe = df
        self.nombre = nombre

    def nulos(self) -> pd.Series:
        """Nº de nulos por columna (índice = nombre de columna)."""
        return self.dataframe.isna().sum()

    def duplicados(self, clave: list[str]) -> pd.DataFrame:
        """Todas las filas cuya clave aparece más de una vez.
        KeyError si alguna columna de la clave no existe."""

        if set(clave) - set(self.dataframe.columns):
            raise KeyError("La clave indicada no pertenece a las columnas del df")

        return self.dataframe.loc[self.dataframe.duplicated(clave, keep="first")]

    def resumen(self) -> dict[str, int]:
        """{'filas', 'columnas', 'nulos_totales', 'duplicados_completos'}"""
        return {
            "filas": self.dataframe.shape[0],
            "columnas": self.dataframe.shape[1],
            "nulos_totales": int(self.nulos().sum()),
            "duplicados_completos": self.duplicados(self.dataframe.columns).shape[0],
        }
