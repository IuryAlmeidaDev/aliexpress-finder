import pandas as pd
from typing import List, Dict, Any

def export_to_excel(records: List[Dict[str, Any]], filepath: str = "oportunidades.xlsx") -> str:
    df = pd.DataFrame(records)
    df.to_excel(filepath, index=False, engine="openpyxl")
    return filepath
