# -*- coding: utf-8 -*-
import django
if django.VERSION >= (1,9):
    from django.forms.utils import flatatt
else:    
    from django.forms.util import flatatt
from django.forms.widgets import DateTimeInput
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

try:
    import json
except ImportError:
    from django.utils import simplejson as json
try:
    from django.utils.encoding import force_unicode as force_text
except ImportError:  # python3
    from django.utils.encoding import force_text


lang_map = {
    'tzm-la': 'tzm-latn',
    'zh-hk': 'zh-TW',
}

class DateTimePicker(DateTimeInput):
    class Media:
        class JsFiles(object):
            def __iter__(self):
                yield 'bootstrap3_datetime/js/moment.min.js'
                yield 'bootstrap3_datetime/js/bootstrap-datetimepicker.min.js'
                lang = translation.get_language()
                if lang:
                    lang = lang.lower()
                    lang = lang_map.get(lang, lang)
                    if lang not in ('en', 'en-us'):
                        yield 'bootstrap3_datetime/js/locale/%s.js' % (lang)

            def __getitem__(self, item):
                return list(self)[item]

        js = JsFiles()
        css = {'all': ('bootstrap3_datetime/css/bootstrap-datetimepicker.min.css',), }

    # http://momentjs.com/docs/#/parsing/string-format/
    # http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    format_map = (('DDD', r'%j'),
                  ('DD', r'%d'),
                  ('MMMM', r'%B'),
                  ('MMM', r'%b'),
                  ('MM', r'%m'),
                  ('YYYY', r'%Y'),
                  ('YY', r'%y'),
                  ('HH', r'%H'),
                  ('hh', r'%I'),
                  ('mm', r'%M'),
                  ('ss', r'%S'),
                  ('a', r'%p'),
                  ('ZZ', r'%z'),
    )

    @classmethod
    def conv_datetime_format_py2js(cls, format):
        for js, py in cls.format_map:
            format = format.replace(py, js)
        return format

    @classmethod
    def conv_datetime_format_js2py(cls, format):
        for js, py in cls.format_map:
            format = format.replace(js, py)
        return format

    html_template = '''
        <div%(div_attrs)s>
            <input%(input_attrs)s/>
            <span class="input-group-addon">
                <span%(icon_attrs)s></span>
            </span>
        </div>'''

    js_template = '''
        <script>
            (function(window) {
                var callback = function() {
                    $(function(){$("#%(picker_id)s:has(input:not([readonly],[disabled]))").datetimepicker(%(options)s);});
                };
                if(window.addEventListener)
                    window.addEventListener("load", callback, false);
                else if (window.attachEvent)
                    window.attachEvent("onload", callback);
                else window.onload = callback;
            })(window);
        </script>'''

    def __init__(self, attrs=None, format=None, options=None, div_attrs=None, icon_attrs=None):
        if not icon_attrs:
            icon_attrs = {'class': 'glyphicon glyphicon-calendar'}
        if not div_attrs:
            div_attrs = {'class': 'input-group date'}
        if format is None and options and options.get('format'):
            format = self.conv_datetime_format_js2py(options.get('format'))
        super(DateTimePicker, self).__init__(attrs, format)
        if 'class' not in self.attrs:
            self.attrs['class'] = 'form-control'
        self.div_attrs = div_attrs and div_attrs.copy() or {}
        self.icon_attrs = icon_attrs and icon_attrs.copy() or {}
        self.picker_id = self.div_attrs.get('id') or None
        if options == False:  # datetimepicker will not be initalized only when options is False
            self.options = False
        else:
            self.options = options and options.copy() or {}
            if format and not self.options.get('format') and not self.attrs.get('date-format'):
                self.options['format'] = self.conv_datetime_format_py2js(format)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        extra_attrs = dict(type=self.input_type, name=name)
        if self.attrs:
            extra_attrs.update(self.attrs)
        input_attrs = self.build_attrs(attrs, extra_attrs=extra_attrs)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            input_attrs['value'] = force_text(self.format_value(value))
        input_attrs = dict([(key, conditional_escape(val)) for key, val in input_attrs.items()])  # python2.6 compatible
        if not self.picker_id:
             self.picker_id = (input_attrs.get('id', '') +
                               '_pickers').replace(' ', '_')
        self.div_attrs['id'] = self.picker_id
        picker_id = conditional_escape(self.picker_id)
        div_attrs = dict(
            [(key, conditional_escape(val)) for key, val in self.div_attrs.items()])  # python2.6 compatible
        icon_attrs = dict([(key, conditional_escape(val)) for key, val in self.icon_attrs.items()])
        html = self.html_template % dict(div_attrs=flatatt(div_attrs),
                                         input_attrs=flatatt(input_attrs),
                                         icon_attrs=flatatt(icon_attrs))
        if self.options != False:
            lang = translation.get_language()
            self.options['locale'] = lang_map.get(lang, lang)
            js = self.js_template % dict(picker_id=picker_id,
                                         options=json.dumps(self.options or {}))
        else:
            js = ''
        return mark_safe(force_text(html + js))
