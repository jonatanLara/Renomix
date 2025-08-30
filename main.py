import os
import sys

# Alta DPI en Windows para que Tkinter no se vea borroso
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from ui.RenomixApp import RenomixApp


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "renomix.db")
    app = RenomixApp(db_path=db_path)
    app.mainloop()


if __name__ == "__main__":
    main()
