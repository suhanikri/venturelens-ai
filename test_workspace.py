from dotenv import load_dotenv

load_dotenv()
import google_workspace as g

print("configured:", g.configured())
pdf = open("memo_test.pdf", "rb").read()
print("email:", g.send_report_email("scalestudent2@gmail.com", "VentureLens test",
                                    "Test message from VentureLens.", [("test.pdf", pdf)]))
print("drive folder:", g.save_to_drive("test123", "TestCo", [("hello.txt", b"hello", "text/plain")]))
