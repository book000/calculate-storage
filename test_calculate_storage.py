import unittest
from unittest.mock import patch, MagicMock
import calculate_storage
import os
import psutil
import platform
import tempfile

class TestCalculateStorage(unittest.TestCase):
    @patch('calculate_storage.requests.get')
    @patch('calculate_storage.requests.patch')
    def test_github_issue_update(self, mock_patch, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"body": "| ✅ | TEST_COMPUTER | C: | 50% | 100 GB (SSD) | <!-- calculate-storage#TEST_COMPUTER#C -->"}

        mock_patch.return_value.status_code = 200

        github_issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
        usage = MagicMock()
        usage.used = 50 * 1024 * 1024 * 1024  # 50 GB
        usage.total = 100 * 1024 * 1024 * 1024  # 100 GB
        usage.percent = 50

        result = github_issue.update_storage_row("TEST_COMPUTER", "C", usage)
        self.assertTrue(result)

        github_issue.update_issue_body()
        mock_patch.assert_called_once()

    @patch('calculate_storage.psutil.disk_usage')
    @patch('calculate_storage.get_real_hostname')
    @patch('calculate_storage.get_github_token')
    @patch('calculate_storage.GitHubIssue')
    def test_main(self, MockGitHubIssue, mock_get_github_token, mock_get_real_hostname, mock_disk_usage):
        mock_get_real_hostname.return_value = "TEST_COMPUTER"
        mock_get_github_token.return_value = "test_token"

        mock_issue_instance = MockGitHubIssue.return_value
        mock_issue_instance.get_computer_drives.return_value = ["C"]
        mock_issue_instance.update_storage_row.return_value = True
        mock_issue_instance.get_human_readable_size.return_value = "50 GB"

        mock_disk_usage.return_value = psutil._common.sdiskusage(
            total=100 * 1024 * 1024 * 1024,  # 100 GB
            used=50 * 1024 * 1024 * 1024,   # 50 GB
            free=50 * 1024 * 1024 * 1024,   # 50 GB
            percent=50
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CALCULATE_STORAGE_LOG_DIR": tmpdir}):
                with patch('sys.argv', ["calculate_storage.py", "1"]):
                    calculate_storage.main()

        mock_issue_instance.update_storage_row.assert_called_once_with("TEST_COMPUTER", "C", mock_disk_usage.return_value)
        mock_issue_instance.update_issue_body.assert_called_once()
        root_logger = calculate_storage.logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()

    @patch('calculate_storage.is_valid_issue_number', return_value=False)
    def test_main_invalid_issue_number(self, mock_is_valid_issue_number):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CALCULATE_STORAGE_LOG_DIR": tmpdir}):
                with patch('sys.argv', ["calculate_storage.py", "invalid"]):
                    with self.assertLogs(level='INFO') as log:
                        calculate_storage.main()
                        self.assertTrue(any("Invalid issue number" in message for message in log.output))
        root_logger = calculate_storage.logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()

    @patch('calculate_storage.requests.get')
    def test_get_issue_body(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"body": "Test issue body"}
        mock_get.return_value = mock_response

        issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
        self.assertEqual(issue.body, "Test issue body")

    @patch('calculate_storage.requests.get')
    def test_get_issue_body_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            calculate_storage.GitHubIssue("test_repo", 1, "test_token")
        self.assertIn("Failed to get issue body", str(context.exception))

    @patch('calculate_storage.requests.get')
    def test_get_issue_body_api_error(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        with self.assertRaises(Exception) as context:
            calculate_storage.GitHubIssue("test_repo", 1, "test_token")
        self.assertIn("Failed to get issue body", str(context.exception))

    @patch('calculate_storage.requests.patch')
    def test_update_issue_body(self, mock_patch):
        mock_patch.return_value.status_code = 200
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            issue.body = "Updated body"
            result = issue.update_issue_body()
            self.assertTrue(result)

    @patch('calculate_storage.requests.patch')
    def test_update_issue_body_failure(self, mock_patch):
        mock_patch.return_value.status_code = 400
        mock_patch.return_value.text = "Bad Request"
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            issue.body = "Updated body"
            with self.assertRaises(Exception) as context:
                issue.update_issue_body()
            self.assertIn("Failed to update issue body", str(context.exception))

    @patch('calculate_storage.requests.patch')
    def test_update_issue_body_api_error(self, mock_patch):
        mock_patch.return_value.status_code = 500
        mock_patch.return_value.text = "Internal Server Error"
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            issue.body = "Updated body"
            with self.assertRaises(Exception) as context:
                issue.update_issue_body()
            self.assertIn("Failed to update issue body", str(context.exception))

    def test_get_human_readable_size(self):
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            self.assertEqual(issue.get_human_readable_size(1024), "1.00 KB")
            self.assertEqual(issue.get_human_readable_size(1048576), "1.00 MB")
            self.assertEqual(issue.get_human_readable_size(1073741824), "1.00 GB")

    @patch('psutil.disk_usage')
    def test_update_storage_row(self, mock_disk_usage):
        mock_disk_usage.return_value = psutil._common.sdiskusage(total=1000000000, used=900000000, free=100000000, percent=91)
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            issue.storage_rows = [
                {
                    "computer_name": "test_computer",
                    "drive": "C",
                    "markdown": {
                        "computer_name": "test_computer",
                        "drive": "C",
                        "checkmark": "",
                        "used": "",
                        "size": "",
                        "raw": "",
                        "drive_type": "SSD"
                    }
                }
            ]
            result = issue.update_storage_row("test_computer", "C", mock_disk_usage.return_value)
            self.assertTrue(result)
            self.assertEqual(issue.storage_rows[0]["markdown"]["checkmark"], "🔴")

    def test_get_computer_drives(self):
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Mocked body"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            issue.storage_rows = [
                {"computer_name": "test_computer", "drive": "C"},
                {"computer_name": "test_computer", "drive": "D"},
                {"computer_name": "other_computer", "drive": "E"}
            ]
            drives = issue.get_computer_drives("test_computer")
            self.assertEqual(drives, ["C", "D"])

    def test_is_valid_issue_number(self):
        self.assertTrue(calculate_storage.is_valid_issue_number("123"))
        self.assertFalse(calculate_storage.is_valid_issue_number(None))
        self.assertFalse(calculate_storage.is_valid_issue_number("abc"))

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='test_token')
    def test_get_github_token(self, mock_open, mock_exists):
        token = calculate_storage.get_github_token()
        self.assertEqual(token, "test_token")
        mock_open.assert_called_once_with(os.path.expanduser("data/github_token.txt"), "r", encoding="utf-8")

    @patch('os.path.exists', return_value=False)
    def test_get_github_token_file_not_exists(self, mock_exists):
        with self.assertRaises(Exception) as context:
            calculate_storage.get_github_token()
        self.assertIn("Please create data/github_token.txt", str(context.exception))

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_save_results(self, mock_open):
        calculate_storage.save_results("test_host", [{"key": "value"}])
        mock_open.assert_called_once()

    @patch('builtins.open', side_effect=IOError("File write error"))
    def test_save_results_file_error(self, mock_open):
        with self.assertRaises(IOError):
            calculate_storage.save_results("test_host", [{"key": "value"}])

    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs', side_effect=OSError("Permission denied"))
    def test_save_results_directory_error(self, mock_makedirs, mock_exists):
        with self.assertRaises(OSError) as context:
            calculate_storage.save_results("test_host", [{"key": "value"}])
        self.assertIn("Permission denied", str(context.exception))

    def test_setup_logging_writes_file(self):
        root_logger = calculate_storage.logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["CALCULATE_STORAGE_LOG_DIR"] = tmpdir
            try:
                log_path = calculate_storage.setup_logging()
                calculate_storage.logging.info("test log message")
                for handler in root_logger.handlers:
                    if hasattr(handler, "flush"):
                        handler.flush()

                self.assertTrue(os.path.exists(log_path))
                with open(log_path, "r", encoding="utf-8") as f:
                    contents = f.read()
                self.assertIn("test log message", contents)
            finally:
                for handler in list(root_logger.handlers):
                    root_logger.removeHandler(handler)
                    if hasattr(handler, "close"):
                        handler.close()
                os.environ.pop("CALCULATE_STORAGE_LOG_DIR", None)

    @patch('calculate_storage.get_github_token')
    @patch('psutil.disk_usage', side_effect=OSError("Disk error"))
    def test_main_disk_usage_error(self, mock_disk_usage, mock_get_github_token):
        mock_get_github_token.return_value = "test_token"
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CALCULATE_STORAGE_LOG_DIR": tmpdir}):
                with patch('sys.argv', ["calculate_storage.py", "1"]):
                    with patch('calculate_storage.get_real_hostname', return_value="TEST_COMPUTER"):
                        with patch('calculate_storage.GitHubIssue') as MockGitHubIssue:
                            mock_issue_instance = MockGitHubIssue.return_value
                            mock_issue_instance.get_computer_drives.return_value = ["C"]

                            calculate_storage.main()
                    mock_issue_instance.update_storage_row.assert_not_called()
        root_logger = calculate_storage.logging.getLogger()
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()

    @patch('calculate_storage.os.name', 'nt')
    @patch('calculate_storage.os.environ', {'COMPUTERNAME': 'TEST_WINDOWS'})
    def test_get_real_hostname_windows(self):
        hostname = calculate_storage.get_real_hostname()
        self.assertEqual(hostname, 'TEST_WINDOWS')
    
    @patch('calculate_storage.os.name', 'posix')
    @patch('calculate_storage.os')
    def test_get_real_hostname_unix(self, mock_os):
        mock_os.uname.return_value = ('Linux', 'TEST_UNIX', '5.10.0', '#1 SMP', 'x86_64')
        hostname = calculate_storage.get_real_hostname()
        self.assertEqual(hostname, 'TEST_UNIX')

    def test_get_storage_rows_malformed_line(self):
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="Malformed line | with | incorrect | format <!-- calculate-storage#test_computer#C -->"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            # The malformed line should be skipped, resulting in an empty storage_rows
            self.assertEqual(len(issue.storage_rows), 0)

    def test_get_storage_rows_invalid_size_format(self):
        with patch.object(calculate_storage.GitHubIssue, '_GitHubIssue__get_issue_body', return_value="| ✅ | test_computer | C | 50% | Invalid Size Format | <!-- calculate-storage#test_computer#C -->"):
            issue = calculate_storage.GitHubIssue("test_repo", 1, "test_token")
            # The line with invalid size format should be skipped
            self.assertEqual(len(issue.storage_rows), 0)

if __name__ == "__main__":
    unittest.main()
