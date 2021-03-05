from django.forms import SelectMultiple
from django.utils.encoding import force_text


class ArrayFieldSelectMultipleWdget(SelectMultiple):
    def format_value(self, value):
        """Return selected values as a list."""
        if value is None and self.allow_multiple_selected:
            return []
        if not isinstance(value, (tuple, list)):
            # This means it should be a comma delimited list of items so parse it
            value = value.split(',')

        return [force_text(v) if v is not None else '' for v in value]
