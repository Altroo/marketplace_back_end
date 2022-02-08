import logging
import re

logger = logging.getLogger(__name__)


class LanguageInterpreterException(Exception):
    pass


class LanguageCleanerException(Exception):
    pass


class LanguageUnicodeMixin:
    """
    Mixin for working with unicode ranges
    """

    # Regular expression to clean up a string
    # after removing language characters
    _DELETED_CHARS_REGEX = r'\([^()]*\)|\[[^\[\]]*\]'

    # Unicode character range table for languages
    LANGUAGES_UNICODE = {}

    @staticmethod
    def get_regular_expression(unicode_range, find=False):
        """
        Getting a unicode range

        Parameters:
        ----------
        :param find:
        :param unicode_range: Start and end of a language range in a unicode table

        :return: regular expression
        """
        regular_expression = f'[\\{unicode_range.get("start")}-\\{unicode_range.get("end")}]'
        if find:
            regular_expression = f'({regular_expression}+)'
        return regular_expression

    def get_unicode_range(self, language_code, language_unicode=None):
        """
        Start and end of a language range in a unicode table

        Parameters:
        ----------
        :param language_code: Language code to receive start and end of a language range in a unicode table
        :param language_unicode: Start and end of a language range in a unicode table

        :return: unicode range
        """
        _language_unicode = language_unicode or self.LANGUAGES_UNICODE
        if not _language_unicode or not isinstance(_language_unicode, dict):
            raise LanguageCleanerException(f'The attribute "language_unicode" or '
                                           f'LANGUAGES_UNICODE must be specified')

        unicode_range = language_unicode.get(language_code)
        if not unicode_range:
            raise LanguageCleanerException(f'The specified unicode table does not '
                                           f'contain a range for "{language_code}"')
        return unicode_range


class LanguageUnicode(LanguageUnicodeMixin):
    pass


class LanguageCleaner(LanguageUnicodeMixin):
    """
    Language Cleaner
    ----------

    Description:
    ----------
    Removes characters of the specified alphabet from a string

    To add a language for processing, you need to add a language
    to the attribute LANGUAGES_UNICODE (If you inherit from this class)
    or pass a variable "language_unicode" to the method for processing.

    This should look like:
    >> {
    >>     "language_name": {
    >>         "start": "unicode range start",
    >>         "end": "unicode range end",
    >>     }
    >> }
    ...examples usage below

    Examples usage
    ----------
    >>
    >> class LanguageCleaner(LanguageCleaner):
    >>     LANGUAGES_UNICODE = {
    >>         'tifinagh': {
    >>             'start': 'u2d30',
    >>             'end': 'u2d7f',
    >>         }
    >>     }

    >> input_string = 'Agdal Riyad (\\u2d30\\u2d33\\u2d37\\u2d30\\u2d4d)'
    >>
    >> # Clear string
    >> LanguageCleaner().clear_string(string, 'tifinagh')
    >>
    >> # Clear strings
    >> LanguageCleaner().clear_strings([string], 'tifinagh')
    """

    def clear_string(self, string: str, language_code: str, language_unicode=None):
        """
        Clear string
        ----------

        Parameters:
        ----------
        :param string: String to process
        :param language_code: Language code to receive start and end of a language range in a unicode table
        :param language_unicode: Start and end of a language range in a unicode table

        :return: cleared string
        """
        unicode_range = self.get_unicode_range(language_code, language_unicode)
        return self._clear_string(string, unicode_range)

    def clear_strings(self, strings: list, language_code: str, language_unicode=None):
        """
        Clear strings
        ----------

        Parameters:
        ----------
        :param strings: Strings to process
        :param language_code: Language code to receive start and end of a language range in a unicode table
        :param language_unicode: Start and end of a language range in a unicode table

        :return: cleared string
        """
        unicode_range = self.get_unicode_range(language_code, language_unicode)
        for string in strings:
            yield self._clear_string(string, unicode_range)

    def _clear_string(self, string, unicode_range):
        """
        Clear string

        Parameters:
        ----------
        :param unicode_range: Start and end of a language range in a unicode table

        :return: cleared string
        """
        # Removing letters of the specified language
        regular_expression = self.get_regular_expression(unicode_range)
        if self._DELETED_CHARS_REGEX:
            regular_expression += f'|{self._DELETED_CHARS_REGEX}'

        string = re.sub(regular_expression, '', string)
        return string.strip()


def main():
    # #############
    # Example usage
    # #############
    strings = (
        'Agdal Riyad ⴰⴳⴷⴰⵍ ⵕⵢⴰⴹ أكدال الرياض',
        'Hassan ⵃⴰⵙⵙⴰⵏ حسان',
        'Rue Mohamed Bel Hassan El Ouazzani زنقة محمد بلحسن الوزاني',
        'Rue Jaâfar as Sadik زنقة جعفر الصديق',
        'Rue Benzert زنقة بنزرت',
        'Avenue Moulay Ismail شارع مولاي اسماعيل',
        'Avenue de la Victoire شارع النصر',
        'Oumazza أم عزة',
        'Avenue Hassan II',
        'Route de Rabat',
        'Karkouk',
        'Riad ⵔⵉⵢⴰⴷ الرياض',
        'Yacoub El Mansour ⵢⴰⵄⵇⵓⴱ ⵍⵎⴰⵏⵙⵓⵔ يعقوب المنصور',
        'Salé El Jadida ⵙⵍⴰ ⵜⴰⵎⴰⵢⵏⵓⵜ سلا الجديدة',
        'Bab Lamrissa ⴱⴰⴱ ⵍⵎⵔⵉⵙⴰ باب لمريسة',
        'Charf-Mghogha ⵛⴰⵕⴼ ⵎⵖⵓⵖⴰ الشرف مغوغة',
        'Océan ⵍⵎⵓⵃⵉⵟ المحيط',
        'El Menzeh المنزه',
        'زنقة مكة',
        'Souissi ⵙⵡⵉⵙⵉ السويسي',
        'Hssaine حصين',
        'cercle de Salé-Banlieue',
        'Bouknadel',
        'Aïn Attig ⵄⵉⵏ ⵄⵜⵉⵇ عين عتيق',
        'Rue Abderahmane Ghafiqi زنقة عبد الرحمن الغافقي',
    )

    # string = strings[5]
    # string = "Derb Kbala"

    # All languages example
    # result = get_multi_language_translate(string)
    # print(result['ar'])
    # print(result['en'])
    # print(result['fr'])
    # Single language
    # print(get_string_translate(string, 'ar'))
    # print(get_string_translate(string, 'fr'))
    # print(get_string_translate(string, 'en'))

    # string = LanguageCleaner().clear_string(string, 'tifinagh', {'tifinagh': {'start': 'u2d30', 'end': 'u2d7f'}})
    # print(string)


if __name__ == '__main__':
    main()
