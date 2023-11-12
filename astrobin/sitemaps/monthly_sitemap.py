from django.contrib.sitemaps import Sitemap
from django.db.models import Model, QuerySet
from django.db.models.functions import ExtractYear, ExtractMonth
import datetime

class MonthlySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    date_field = 'updated'  # Default date field

    def __init__(self, queryset: QuerySet, year: int, month: int, date_field: str = None):
        self.queryset = queryset
        self.year = year
        self.month = month
        if date_field:
            self.date_field = date_field

    def items(self) -> QuerySet:
        start_date = datetime.date(self.year, self.month, 1)
        end_date = datetime.date(self.year, self.month + 1, 1) \
            if self.month < 12 \
            else datetime.date(self.year + 1, 1, 1)

        return self.queryset.filter(**{f"{self.date_field}__range": (start_date, end_date)})

    def lastmod(self, obj) -> datetime:
        return getattr(obj, self.date_field)


def generate_sitemaps(queryset: QuerySet, date_field: str) -> dict:
    sitemaps = {}
    queryset = queryset.annotate(
        year=ExtractYear(date_field),
        month=ExtractMonth(date_field)
    ).values('year', 'month').distinct()

    for date in queryset:
        year = date['year']
        month = date['month']
        sitemap_key = f'{queryset.model.__name__.lower()}_{year}_{month}'
        sitemaps[sitemap_key] = MonthlySitemap(queryset, year, month, date_field)

    return sitemaps
