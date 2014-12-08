import re
import unidecode
import escpos
from printing.escpos.constants import TEXT_STYLE, PAGE_CP_SET_COMMAND, PAGE_CP_CODE
from printing.escpos.exceptions import TextError


class EscposText(escpos.Escpos):
    def text(self, text):
        t = unicode(text)
        if t:
            if self._codepage:
                return unicode(text).encode(self._codepage)
            else:
                return unidecode.unidecode(t)
        else:
            return ''


    def set(self, codepage=None, **kwargs):
        """
        :type bold:         bool
        :param bold:        set bold font
        :type underline:    [None, 1, 2]
        :param underline:   underline text
        :type size:         ['normal', '2w', '2h' or '2x']
        :param size:        Text size
        :type font:         ['a', 'b', 'c']
        :param font:        Font type
        :type align:        ['left', 'center', 'right']
        :param align:       Text position
        :type inverted:     boolean
        :param inverted:    White on black text
        :type color:        [1, 2]
        :param color:       Text color
        :rtype:             NoneType
        :returns:            None
        """

        for key in kwargs.iterkeys():
            if not TEXT_STYLE.has_key(key):
                raise KeyError('Parameter {0} is wrong.'.format(key))

        for key, value in TEXT_STYLE.iteritems():
            if kwargs.has_key(key):
                cur = kwargs[key]
                if isinstance(cur, str) or isinstance(cur, unicode):
                    cur = cur.lower()

                if value.has_key(cur):
                    return value[cur]
                else:
                    raise AttributeError(
                        'Attribute {0} is wrong.'.format(cur)
                    )

        # Codepage
        self._codepage = codepage
        if codepage:
           return PAGE_CP_SET_COMMAND + chr(PAGE_CP_CODE[codepage])

    def line(self, line_char_no=48, style='Normal'):
        if style=='Normal':
            return line_char_no*'_' + '\x0a'
        elif style=='Dotted':
            return line_char_no*'.' + '\x0a'
        elif style=='Dashed':
            return line_char_no*'-' + '\x0a'

    def full_text_line(self, percents, strings, line_char_no=48, aligns=[], left_offset=0):
        if len(aligns) == 0:
            aligns = ['left']*line_char_no
        temp_s = list(' '*line_char_no)
        numberized = []
        for i in range(0, len(percents)):
            numberized.append(int(sum(percents[:(i+1)])*line_char_no))

        for i in range(0, len(strings)):
            if aligns[i] == 'left':
                if i == 0:
                    temp_s[(int(sum(percents[:i]))+left_offset):(len(strings[i])+left_offset)] = strings[i]
                else:
                    temp_s[int(sum(percents[:i])):len(strings[i])] = strings[i]
            elif aligns[i] == 'right':
                temp_s[(numberized[i]-len(strings[i])):(numberized[i])] = strings[i]

        return unidecode.unidecode("".join(temp_s)) + '\x0a'