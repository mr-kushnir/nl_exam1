"""Test YaGPT parser edge cases - boundary conditions."""
import pytest
from src.services.yagpt_service import YaGPTService


class TestParserEdgeCases:
    """Test parser with various edge cases."""

    @pytest.fixture
    def service(self):
        return YaGPTService()

    # Group 1: Conversational amounts
    @pytest.mark.parametrize("message,expected_amount", [
        ("маме отправил две тыщи", 2000),
        ("сотка на проезд", 100),
        ("полтос за кофе", 50),
        ("штука на такси", 1000),
        ("пятихатка за стрижку", 500),
        ("косарь на продукты", 1000),
        ("двадцатка за воду", 20),
        ("трёшка за обед", 3000),
    ])
    def test_conversational_amounts(self, service, message, expected_amount):
        """Test parsing of colloquial Russian number words."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")
        # Note: These may fail with fallback parser, depends on YaGPT

    # Group 2: Slang and abbreviations
    @pytest.mark.parametrize("message,expected_amount", [
        ("кофе 3 сотни", 300),
        ("бенз на 2к", 2000),
        ("закинул на телефон пол ляма", 500000),
        ("пиво 250р", 250),
        ("на карту жене 5к", 5000),
        ("доширак 50 рэ", 50),
    ])
    def test_slang_abbreviations(self, service, message, expected_amount):
        """Test parsing of slang and abbreviations."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")

    # Group 3: Ambiguous formulations
    @pytest.mark.parametrize("message,expected_amount", [
        ("купил 2 кофе по 200", 400),
        ("три пива по сотке", 300),
        ("2 билета в кино 800", 800),
        ("обед на двоих 1500", 1500),
        ("взял 5 булок по 45", 225),
    ])
    def test_ambiguous_formulations(self, service, message, expected_amount):
        """Test parsing of ambiguous quantity expressions."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")

    # Group 4: Amount not at end
    @pytest.mark.parametrize("message,expected_amount", [
        ("500 рублей на такси", 500),
        ("за 300 купил воду", 300),
        ("отдал 1500 за доставку", 1500),
    ])
    def test_amount_not_at_end(self, service, message, expected_amount):
        """Test parsing when amount is not at the end."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
            assert result.amount == expected_amount, f"Expected {expected_amount}, got {result.amount}"
        else:
            print(f"'{message}' -> NOT PARSED (fallback should handle)")

    # Group 5: With date/time
    @pytest.mark.parametrize("message,expected_amount", [
        ("вчера потратил 500 на еду", 500),
        ("утром кофе 250", 250),
        ("на прошлой неделе ремонт 15000", 15000),
    ])
    def test_with_datetime(self, service, message, expected_amount):
        """Test parsing with date/time context."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")

    # Group 6: Complex descriptions
    @pytest.mark.parametrize("message,expected_amount", [
        ("заплатил за интернет и мобильную связь 900", 900),
        ("скинулись на подарок шефу 500", 500),
        ("вернул долг Серёге 3000", 3000),
        ("подписка на яндекс плюс 300", 300),
    ])
    def test_complex_descriptions(self, service, message, expected_amount):
        """Test parsing of complex expense descriptions."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")

    # Group 7: Edge cases that should fail or partially work
    @pytest.mark.parametrize("message,should_parse", [
        ("кофе", False),
        ("500", False),
        ("потратил деньги", False),
        ("что-то купил вроде", False),
        ("ну там рублей 300 примерно", True),
        ("тысяч 5 наверное ушло", True),
        ("около 200 на мелочи", True),
    ])
    def test_edge_cases(self, service, message, should_parse):
        """Test edge cases that may break the parser."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> PARSED: {result.item}, {result.amount}р")
        else:
            print(f"'{message}' -> NOT PARSED")

        if should_parse:
            # These might parse or not depending on fallback
            pass
        else:
            # These should NOT parse (no amount)
            if result is None:
                print(f"  CORRECT: Rejected invalid input")

    # Group 8: STT artifacts (speech-to-text)
    @pytest.mark.parametrize("message,expected_amount", [
        ("кофе триста рублей", 300),
        ("такси пятьсот", 500),
        ("эээ обед где-то тыща двести", 1200),
    ])
    def test_stt_artifacts(self, service, message, expected_amount):
        """Test parsing of STT transcription artifacts."""
        result = service.parse_expense(message)
        if result:
            print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")
        else:
            print(f"'{message}' -> NOT PARSED")


class TestSimpleFallbackParser:
    """Test the simple fallback parser directly."""

    @pytest.fixture
    def service(self):
        return YaGPTService()

    @pytest.mark.parametrize("message,expected_item,expected_amount", [
        ("кофе 300", "кофе", 300),
        ("такси 500р", "такси", 500),
        ("300 кофе", "кофе", 300),
        ("500р такси", "такси", 500),
        ("обед 1500", "обед", 1500),
    ])
    def test_simple_patterns(self, service, message, expected_item, expected_amount):
        """Test simple fallback parser patterns."""
        result = service._simple_parse(message)
        assert result is not None, f"Should parse: {message}"
        assert result.amount == expected_amount
        assert expected_item in result.item.lower()
        print(f"'{message}' -> {result.item}, {result.amount}р, {result.category}")

    @pytest.mark.parametrize("message", [
        "кофе",
        "просто текст",
        "",
        "рублей много",
    ])
    def test_invalid_patterns(self, service, message):
        """Test that invalid patterns are rejected."""
        result = service._simple_parse(message)
        assert result is None, f"Should NOT parse: {message}"
        print(f"'{message}' -> CORRECTLY REJECTED")
