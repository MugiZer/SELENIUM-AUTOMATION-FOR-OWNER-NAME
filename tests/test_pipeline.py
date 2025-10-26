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

if "gspread" not in sys.modules:
    gspread_stub = types.ModuleType("gspread")
    gspread_stub.auth = SimpleNamespace(READ_WRITE_SCOPE="")
    gspread_stub.Client = object
    gspread_stub.Worksheet = object

    def _authorize(_credentials):
        return SimpleNamespace(open=lambda name: SimpleNamespace(worksheet=lambda tab: None))

    gspread_stub.authorize = _authorize

    utils_stub = types.ModuleType("gspread.utils")

    def _rowcol_to_a1(row, col):
        letters = ""
        current = col
        while current:
            current, remainder = divmod(current - 1, 26)
            letters = chr(65 + remainder) + letters
        return f"{letters}{row}"

    utils_stub.rowcol_to_a1 = _rowcol_to_a1
    gspread_stub.utils = utils_stub

    sys.modules["gspread"] = gspread_stub
    sys.modules["gspread.utils"] = utils_stub

if "google" not in sys.modules:
    google_stub = types.ModuleType("google")
    oauth2_stub = types.ModuleType("google.oauth2")
    service_account_stub = types.ModuleType("google.oauth2.service_account")

    class _Credentials:
        @classmethod
        def from_service_account_info(cls, *_args, **_kwargs):
            return cls()

        @classmethod
        def from_service_account_file(cls, *_args, **_kwargs):
            return cls()

    service_account_stub.Credentials = _Credentials

    google_stub.oauth2 = oauth2_stub
    oauth2_stub.service_account = service_account_stub

    sys.modules["google"] = google_stub
    sys.modules["google.oauth2"] = oauth2_stub
    sys.modules["google.oauth2.service_account"] = service_account_stub

import main
from scraper.schema import OUTPUT_COLUMNS
from scraper.sheets import range_for_rows


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


def test_process_sheet_skips_failures(monkeypatch):
    header = ["civicNumber", "streetName", *OUTPUT_COLUMNS]
    worksheet = StubWorksheet([header, _sheet_row("123", "Main"), _sheet_row("456", "Elm", "existing")])

    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setattr(main, "get_client", lambda *_: None)
    monkeypatch.setattr(main, "open_sheet", lambda *_: worksheet)
    monkeypatch.setattr(main, "ensure_columns", lambda _: header)

    captured_updates = []

    def _capture_batch(ws, start_row, payload, header_row):
        captured_updates.append((start_row, [row.copy() for row in payload]))

    monkeypatch.setattr(main, "batch_update", _capture_batch)

    scraper = DummyScraper(
        [
            {"status": "ok", "owner_names": "Sheet Owner"},
            {"status": "multiple_matches"},
        ]
    )

    args = SimpleNamespace(sheet="Test", tab="Tab", from_row=2, max=0)
    main.process_sheet(args, scraper)

    assert captured_updates, "process_sheet should update successful rows"
    start_row, payload = captured_updates[0]
    assert start_row == 2
    assert payload[0]["owner_names"] == "Sheet Owner"
    assert payload[0]["status"] == "ok"
    assert all(update[0] != 3 for update in captured_updates)


def test_commit_batch_rolls_back_on_failure(monkeypatch):
    header = ["civicNumber", "streetName", *OUTPUT_COLUMNS]
    base = {"civicNumber": "123", "streetName": "Main"}
    original_values = {col: f"orig_{col}" for col in OUTPUT_COLUMNS}
    updated_values = {col: f"new_{col}" for col in OUTPUT_COLUMNS}
    rows = [(2, {**base, **original_values}, {**base, **updated_values})]

    call_history = []
    fetched_ranges = []

    class WorksheetStub:
        def get(self, range_label):
            fetched_ranges.append(range_label)
            return [["snapshot"]]

    def _flaky_batch_update(ws, start_row, payload, header_row):
        call_history.append((start_row, [row.copy() for row in payload]))
        if len(call_history) == 1:
            raise RuntimeError("network glitch")

    monkeypatch.setattr(main, "batch_update", _flaky_batch_update)

    main._commit_batch(WorksheetStub(), rows, header)

    assert len(call_history) == 3
    assert call_history[0][0] == 2
    for column in OUTPUT_COLUMNS:
        assert call_history[0][1][0][column] == f"new_{column}"
        assert call_history[1][1][0][column] == f"orig_{column}"
        assert call_history[2][1][0][column] == f"new_{column}"
    assert call_history[0][1][0]["civicNumber"] == "123"
    assert call_history[1][1][0]["civicNumber"] == "123"
    assert call_history[2][1][0]["civicNumber"] == "123"
    expected_range = range_for_rows(2, 1, header)
    assert fetched_ranges == [expected_range]
