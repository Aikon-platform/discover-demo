from django import forms


class IndexRadioSelect(forms.RadioSelect):
    option_label_template_name = "search/index_option_label.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index_map = {}

    def set_index_to_name_map(self, queryset):
        """
        map the index's ID to its name
        """
        self._index_map = {o.id: o.name for o in queryset}

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """
        set custom data in the HTML radio inputs' attributes, so that they can be accessed in the Svelte frontend.
        if `self._index_map` is defined (`set_index_to_name_map`), set the index's name as the HTML input's ID.
        """
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )

        index_name = None
        if self._index_map:
            for _index_id, _index_name in self._index_map.items():
                if _index_id == value:
                    index_name = _index_name
                    break

        if index_name:
            option["attrs"]["id"] = index_name

        return option
