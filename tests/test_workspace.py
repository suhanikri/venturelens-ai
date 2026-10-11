# project-root import path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()
import google_workspace as g

print("configured:", g.configured())
pdf = open("data/examples/memo_test.pdf", "rb").read()
print("email:", g.send_report_email("scalestudent2@gmail.com", "VentureLens test",
                                    "Test message from VentureLens.", [("test.pdf", pdf)]))
print("drive folder:", g.save_to_drive("test123", "TestCo", [("hello.txt", b"hello", "text/plain")]))
