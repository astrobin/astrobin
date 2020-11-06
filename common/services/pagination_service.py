class PaginationService:
    @staticmethod
    def page_counter(counter, page_number, items_per_page):
        # type: (int, int, int) -> int
        return counter + (page_number - 1) * items_per_page
