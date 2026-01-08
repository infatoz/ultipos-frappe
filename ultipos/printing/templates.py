def generate_test_kot(printer_name, width="80"):
    line = "-" * (32 if width == "58" else 48)

    return (
        "\x1b\x40"
        "\x1b\x21\x30"
        "ULTIPOS TEST KOT\n"
        "\x1b\x21\x00"
        f"{line}\n"
        f"Printer: {printer_name}\n\n"
        "1  Test Burger\n"
        "1  Test Coke\n\n"
        f"{line}\n"
        "If you see this,\nPrinter is OK\n\n\n"
        "\x1d\x56\x00"
    )
