import unittest

from panwid.dropdown import *
from orderedattrdict import AttrDict

class TestDropdown(unittest.TestCase):

    def setUp(self):

        self.data = AttrDict([('Adipisci eius dolore consectetur.', 34),
            ('Aliquam consectetur velit dolore', 19),
            ('Amet ipsum quaerat numquam.', 25),
            ('Amet quisquam labore dolore.', 30),
            ('Amet velit consectetur.', 20),
            ('Consectetur consectetur aliquam voluptatem', 23),
            ('Consectetur ipsum aliquam.', 28),
            ('Consectetur sit neque est', 15),
            ('Dolore voluptatem etincidunt sit', 40),
            ('Dolorem porro tempora tempora.', 37),
            ('Eius numquam dolor ipsum', 26),
            ('Eius tempora etincidunt est', 12),
            ('Est adipisci numquam adipisci', 7),
            ('Est aliquam dolor.', 38),
            ('Etincidunt amet quisquam.', 33),
            ('Etincidunt consectetur velit.', 29),
            ('Etincidunt dolore eius.', 45),
            ('Etincidunt non amet.', 14),
            ('Etincidunt velit adipisci labore', 6),
            ('Ipsum magnam velit quiquia', 21),
            ('Ipsum modi eius.', 3),
            ('Labore voluptatem quiquia aliquam', 18),
            ('Magnam etincidunt porro magnam', 39),
            ('Magnam numquam amet.', 44),
            ('Magnam quisquam sit amet.', 27),
            ('Magnam voluptatem ipsum neque', 32),
            ('Modi est ipsum adipisci', 2),
            ('Neque eius voluptatem voluptatem', 42),
            ('Neque quisquam ipsum.', 10),
            ('Neque quisquam neque.', 48),
            ('Non dolore voluptatem.', 41),
            ('Non numquam consectetur voluptatem.', 35),
            ('Numquam eius dolorem.', 43),
            ('Numquam sed neque modi', 9),
            ('Porro voluptatem quaerat voluptatem', 11),
            ('Quaerat eius quiquia.', 17),
            ('Quiquia aliquam etincidunt consectetur.', 0),
            ('Quiquia ipsum sit.', 49),
            ('Quiquia non dolore quiquia', 8),
            ('Quisquam aliquam numquam dolore.', 1),
            ('Quisquam dolorem voluptatem adipisci.', 22),
            ('Sed magnam dolorem quisquam', 4),
            ('Sed tempora modi est.', 16),
            ('Sit aliquam dolorem.', 46),
            ('Sit modi dolor.', 31),
            ('Sit quiquia quiquia non.', 5),
            ('Sit quisquam numquam quaerat.', 36),
            ('Tempora etincidunt quiquia dolor', 13),
            ('Tempora velit etincidunt.', 24),
            ('Velit dolor velit.', 47)])

    def test_create(self):
        dropdown = Dropdown(self.data)

    def test_default_label(self):
        dropdown = Dropdown(self.data, default=3)
        self.assertEqual(dropdown.selected_label, "Ipsum modi eius.")

    def test_default_value(self):
        dropdown = Dropdown(self.data, default=37)
        self.assertEqual(dropdown.selected_value, 37)
