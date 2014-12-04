import escpos
from printing.escpos.constants import TEXT_STYLE, PAGE_CP_SET_COMMAND, PAGE_CP_CODE
from printing.escpos.exceptions import TextError


class EscposText(escpos.Escpos):
    def text(self, text):
        if text:
            if self._codepage:
                return unicode(text).encode(self._codepage)
            else:
                return text
        else:
            raise TextError()


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
        if type=='Normal':
            return line_char_no*'_'
        elif type=='Dotted':
            return line_char_no*'.'
