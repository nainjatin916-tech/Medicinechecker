"""
Streamlit Cloud Entrypoint for MediSafe
Executes main.py for deployment compatibility.
"""
from pathlib import Path
import runpy

if __name__ == "__main__" or True:
    main_file = Path(__file__).resolve().parent / "main.py"
    runpy.run_path(str(main_file), run_name="__main__")
