import sys
import types
from types import SimpleNamespace

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

if "pandas" not in sys.modules:
    pandas_stub = types.ModuleType("pandas")
    pandas_stub.read_csv = lambda *args, **kwargs: None
    pandas_stub.DataFrame = object
    sys.modules["pandas"] = pandas_stub

if "playwright" not in sys.modules:
    playwright_stub = types.ModuleType("playwright")
    sync_api_stub = types.ModuleType("playwright.sync_api")

    class _Placeholder:
        def __getattr__(self, _name):
            return self

    sync_api_stub.Browser = _Placeholder
    sync_api_stub.BrowserContext = _Placeholder
    sync_api_stub.Page = _Placeholder
    sync_api_stub.Playwright = _Placeholder
    sync_api_stub.TimeoutError = type("TimeoutError", (Exception,), {})

    def _missing_playwright():
        raise RuntimeError("playwright not available in test environment")

    sync_api_stub.sync_playwright = _missing_playwright

    playwright_stub.sync_api = sync_api_stub
    sys.modules["playwright"] = playwright_stub
    sys.modules["playwright.sync_api"] = sync_api_stub

if "rich" not in sys.modules:
    rich_stub = types.ModuleType("rich")
    console_stub = types.ModuleType("rich.console")
    logging_stub = types.ModuleType("rich.logging")

    class _Console:
        def __init__(self, *args, **kwargs):
            pass

        def log(self, *args, **kwargs):
            pass

    class _RichHandler:
        def __init__(self, *args, **kwargs):
            pass

    console_stub.Console = _Console
    logging_stub.RichHandler = _RichHandler

    rich_stub.console = console_stub
    rich_stub.logging = logging_stub

    sys.modules["rich"] = rich_stub
    sys.modules["rich.console"] = console_stub
    sys.modules["rich.logging"] = logging_stub

if "tenacity" not in sys.modules:
    tenacity_stub = types.ModuleType("tenacity")

    def _identity_decorator(*_args, **_kwargs):
        return lambda func: func

    tenacity_stub.retry = _identity_decorator
    tenacity_stub.stop_after_attempt = lambda *args, **kwargs: None
    tenacity_stub.wait_exponential = lambda *args, **kwargs: None

    sys.modules["tenacity"] = tenacity_stub

import main
from scraper.schema import OUTPUT_COLUMNS


class DummyFrame:
    class _ILoc:
        def __init__(self, frame: "DummyFrame"):
            self._frame = frame

        def __getitem__(self, index: int):
            return SimpleNamespace(to_dict=lambda: self._frame._rows[index].copy())

    class _At:
        def __init__(self, frame: "DummyFrame"):
            self._frame = frame

        def __setitem__(self, key, value):
            index, column = key
            self._frame._rows[index][column] = value

    def __init__(self, rows):
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def iloc(self):
        return DummyFrame._ILoc(self)

    @property
    def at(self):
        return DummyFrame._At(self)

    def copy(self):
        return DummyFrame([row.copy() for row in self._rows])

    def to_csv(self, *_args, **_kwargs):
        return None

    def data(self):
        return self._rows


class DummyScraper:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    def fetch(self, query):
        response = self._responses[self.calls]
        self.calls += 1
        return response


def _frame_row(civic_number: str, street_name: str, status: str):
    row = {"civicNumber": civic_number, "streetName": street_name}
    for column in OUTPUT_COLUMNS:
        row.setdefault(column, "")
    row["status"] = status
    return row


def test_process_csv_skips_failures(monkeypatch, tmp_path):
    frame = DummyFrame(
        [
            _frame_row("123", "Main", "old_status"),
            _frame_row("456", "Elm", "stale"),
        ]
    )

    written_frames = []

    monkeypatch.setattr(main, "read_csv", lambda path: frame.copy())
    monkeypatch.setattr(main, "backup_original", lambda path, df: path)
    monkeypatch.setattr(main, "export_snapshot", lambda df, _: None)

    def _capture_write(path, df):
        written_frames.append(df.copy())
        return path

    monkeypatch.setattr(main, "write_csv", _capture_write)

    scraper = DummyScraper(
        [
            {"status": "ok", "owner_names": "New Owner"},
            {"status": "not_found"},
        ]
    )

    args = SimpleNamespace(from_row=2, max=0)
    main.process_csv(tmp_path / "input.csv", scraper, args)

    assert written_frames, "process_csv should produce an output frame"
    result_rows = written_frames[-1].data()
    assert result_rows[0]["owner_names"] == "New Owner"
    assert result_rows[0]["status"] == "ok"
    assert result_rows[1]["status"] == "stale"


class StubWorksheet:
    def __init__(self, rows):
        self._rows = rows
        self.updates = []

    def row_values(self, index):
        return self._rows[index - 1]

    def update(self, range_label, values):
        self.updates.append((range_label, values))

    def get_all_values(self):
        return self._rows


def _sheet_row(civic_number: str, street_name: str, status: str = ""):
    row = [civic_number, street_name]
    defaults = {column: "" for column in OUTPUT_COLUMNS}
    defaults["status"] = status
    row.extend(defaults[column] for column in OUTPUT_COLUMNS)
    return row


# Placeholder for future test cases
