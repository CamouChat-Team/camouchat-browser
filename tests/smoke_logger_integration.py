from camouchat_browser.browser_logger import get_profile_browser_logger


def smoke_test():
    # 1. Initialize Browser Logger
    b_log = get_profile_browser_logger("smoke_test", profile_id="CHROME_1")

    print("\n--- Browser Plugin Logging Test ---")
    b_log.info("Testing Browser Info Log")
    b_log.warning("Testing Browser Warning Log")


if __name__ == "__main__":
    smoke_test()
