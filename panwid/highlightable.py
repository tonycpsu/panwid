import logging
logger = logging.getLogger(__name__)

class HighlightableTextMixin(object):

    @property
    def highlight_state(self):
        if not getattr(self, "_highlight_state", False):
            self._highlight_state = False
            self._highlight_case_sensitive = False
            self._highlight_string = None
        return self._highlight_state

    @property
    def highlight_content(self):
        if self.highlight_state:
            return self.get_highlight_text()
        else:
            return self.highlight_source


    def highlight(self, start, end):
        self._highlight_state = True
        self._highlight_location = (start, end)
        self.on_highlight()

    def unhighlight(self):
        self._highlight_state = False
        self._highlight_location = None
        self.on_unhighlight()

    def get_highlight_text(self):

        if not self._highlight_location:
            return None

        return [
            (self.highlightable_attr_normal, self.highlight_source[:self._highlight_location[0]]),
            (self.highlightable_attr_highlight, self.highlight_source[self._highlight_location[0]:self._highlight_location[1]]),
            (self.highlightable_attr_normal, self.highlight_source[self._highlight_location[1]:]),
        ]

    @property
    def highlight_source(self):
        raise NotImplementedError

    @property
    def highlightable_attr_normal(self):
        raise NotImplementedError

    @property
    def highlightable_attr_highlight(self):
        raise NotImplementedError

    def on_highlight(self):
        pass

    def on_unhighlight(self):
        pass

__all__ = ["HighlightableTextMixin"]
