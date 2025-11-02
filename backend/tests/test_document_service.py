from app.services.document_processing_service import (
    get_name_from_symbol,
    get_symbol_from_name,
    search_with_query,
)


class TestDocumentService:
    async def test_search_with_query(self):
        result = await search_with_query("Apple Inc")
        assert len(result) != 0

    async def test_get_symbol_from_name(self):

        # Test Success
        result = await get_symbol_from_name("Apple Inc")
        assert result == "AAPL"

        # Test Failure with empty i/p
        result = await get_symbol_from_name(" ")
        assert result is None

        # Test Failure with non-existent company
        result = await get_symbol_from_name("Dummy Company")
        assert result is None

    async def test_get_name_from_symbol(self):

        # Test Success
        result = await get_name_from_symbol("AAPL")
        assert result == "Apple Inc"

        # Test Failure with invalid symbol
        result = await get_name_from_symbol("INVALID")
        assert result is None

        # Test Failure with empty i/p
        result = await get_symbol_from_name("")
        assert result is None
