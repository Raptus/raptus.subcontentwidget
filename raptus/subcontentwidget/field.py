from AccessControl import ClassSecurityInfo

from Products.Archetypes.Registry import registerField
from Products.Archetypes.Field import ReferenceField

class SubContentField(ReferenceField):
    _properties = ReferenceField._properties.copy()
    _properties.update(dict(
            relationship = 'relatesTo',
            multiValued = True
        ))
    security = ClassSecurityInfo()
    
    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        for inst, row in value.iteritems():
            for val in row.values():
                field = val.get('field')
                result, marker = val.get('result')
                field.set(inst, result, marker=marker)
            inst.reindexObject()

        self.widget.edited_handler(instance)
        super(SubContentField, self).set( instance, [i.UID() for i in value.keys()], **kwargs)

    security.declarePrivate('validate')
    def validate(self, value, instance, errors=None, **kwargs):
        if not isinstance(value,dict):
            return
        return #TODO !!!
        return [obj.UID() for obj in value.keys()]

registerField(ReferenceField,
              title='SubContentField',
              description=('Used for storing references from '
                           'SubContentWidget'))
