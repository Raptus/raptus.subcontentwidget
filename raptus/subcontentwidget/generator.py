from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile



class DefaultGenerator(object):
    
    def __init__(self, properties=dict()):
        self._properties = dict(macro = 'subcontentwidget_generator_default',
                                maxlength = 10
                           )
        self._properties.update(properties)
    
    def macro(self):
        return 'context/%s/macros/generator' % self._properties.get('macro')
    
    @property
    def maxlength(self):
        return self._properties.get('maxlength')