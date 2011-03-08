import re
from zope import component
from zope.component import queryUtility
from OFS.ObjectManager import checkValidId
from zExceptions import BadRequest, Unauthorized
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.Archetypes.Widget import TypesWidget
from Products.Archetypes.Registry import registerWidget
from Products.Archetypes import atapi
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base

class Handler(object):

    temp_data = None


    def __call__(self, container):
        
        ids = list()
        for subinst in self.temp_data:
            subinst = self.temp_data[subinst]
            id = self._create_id(self._container(container), subinst)
            subinst.setId(id)
            self._container(container)._setObject(id, aq_base(subinst))
        self._container(container).reindexObject()


    def _container(self, container):
        """ subclass and overrides this
            method to get a other container
        """  
        return container


    def _create_id(self, container, subinst):
            id = startid = queryUtility(IIDNormalizer).normalize(getattr(subinst, 'title', 'subcontent'))
            id = startid = id and id or 'subcontent'
            ok = False
            counter = 0
            while(not ok):
                try:
                    checkValidId(container, id)
                    ok = True
                except BadRequest:
                    counter += 1
                    id = '%s_%s' % (startid,counter)
            return id


    def reset(self, context):
        portal_factory = getToolByName(context, 'portal_factory')
        self.temp_data = portal_factory._getTempFolder('subcontent_temp_folder')
        ids = self.temp_data.keys()
        if len(ids) > 0:
            ids = list(ids)
            self.temp_data.manage_delObjects(ids)


    def data(self):
        return self.temp_data


class SubContentWidget(TypesWidget):

    edited_handler = Handler()
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'sub_fields' : None,
        'sub_content_class' : None,
        'edited_handler' : edited_handler,
        'initialized_handler' : edited_handler,
        'macro' : 'subcontentwidget',
        'helper_js':('subcontentwidget_default.js',),
        })
    
    security = ClassSecurityInfo()


    def __init__(self, *arg, **kw):
        super(SubContentWidget, self).__init__(*arg, **kw)
        assert self.sub_content_class, 'missing sub_content_class on widget'
        assert self.sub_fields, 'missing sub_fields on widget'


    def bootstrap(self, inst):
        for field in inst.Schema().values():
            if field.widget == self:
                self.namespace = '%s_%s_' % ( self.sub_content_class.__name__, field.getName(), )
                return
    
        self.catalog = getToolByName(inst, 'portal_catalog')


    def getFields(self, refs=[]):
        # need to make a instance to get schema over ISchema
        tempinst = self.sub_content_class('temp')
        di = dict()
        for inst in refs + [tempinst]:
            li = list()
            for field in inst.Schema().values():
                if not field.getName() in self.sub_fields:
                    continue
                #fix remove DateTime on calendar field
                if hasattr(field, 'default_method'):
                    temp = field.default_method
                    field.default_method = None
                field = field.copy()
                if hasattr(field, 'default_method'):
                    field.default_method = temp
                li.append(field)
            if tempinst == inst:
                di[None] = li
            else:
                di[inst] = li
                    
        return di


    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        
        ref_catalog = getToolByName(instance, 'reference_catalog')
        portal_types = getToolByName(instance,'portal_types')
        self.edited_handler.reset(instance)
        
        # parse string e.g: subEvent_myWidget__0__start_ampm
        # index = 0     title = start
        p = re.compile('^%s__([0-9]*)__(.*)'% self.namespace)
        
        rows = dict()
        for key, value in form.iteritems():
            m = p.match(key)
            if m:
                index, title = m.groups()
                di = rows.get(index, dict())
                di.update({title:value})
                rows.update({index:di})
        
        results = dict()
        for index, row in rows.iteritems():
            index = int(index)
            # button pressed from a non javascript browser
            if index == 0 and not row.get('addrow',False):
                continue
            copy = form.copy()
            copy.update(row)
            id = 'temp_sub_content_%s' % index
            rowset = row.get('rowset', False) or False
            subinstance = ref_catalog.lookupObject(rowset)
            if not subinstance:
                portal_types.constructContent(type_name=self.sub_content_class.portal_type,
                                              container=self.edited_handler.data(), id=id)
                subinstance = self.edited_handler.data()[id]
            results[subinstance] = dict()
            for key, value in row.iteritems():
                fi = subinstance.Schema().get(key, None)
                if fi:
                    result = fi.widget.process_form(instance, fi, copy,empty_marker=None,
                                                    emptyReturnsMarker=False, validating=True)
                    results[subinstance][key] = dict(value=value, field=fi, result=result)
        return results, {}


    def fields(self, context, widgetfield):
        ab_index = 1
        refs = widgetfield.get(context)
        if not isinstance(refs, list):
            refs = [refs]
        
        rows = list()
        for ref, fields in self.getFields(refs).iteritems():
            index= ab_index
            if ref is None:
                index = 0
            prefix = fieldprefix = '%s__%s__' % (self.namespace, index,)
            row = list()
            for field in fields:
                if ref is None:
                    # change the id of the field to render a empty field
                    field = field.__class__('%s%s' % (fieldprefix,field.getName()), **field._properties)
                    fieldprefix = ''
                field.widget.label = ' '
                field.widget.description = ' '
                row.append(field)
            row.append(dict(name='%s__%s__rowset' % (self.namespace, index),
                            value=ref and ref.UID() or None
                            ))
            fcontext = ref and ref or context
            rows.append(dict(context=fcontext, fieldprefix=fieldprefix,
                             prefix=prefix, fields=row))
            ab_index += 1

     #   brains = catalog(object_provides=IAdvertisement.__identifier__,
      #                      path={'query': '/'.join(self.context.getPhysicalPath())})
        return rows


    @property
    def titles(self):
        return [f.widget.label for f in self.getFields()[None]]


    @property
    def generator(self):
        """ this make a css class with the name of the
            first helper_js file. Important: all out side A-z will be stripped.
        """
        if len(self.helper_js):
            name = self.helper_js[0][:-3]
            return re.sub('([^A-z])','',name)
        else:
            return ''

registerWidget(SubContentWidget,
               title='SubContentWidget',
               description=('Render a widget to create sub contenttype '
                            'right on the edit form'),
               used_for=('raptus.subcontentwidget.field.SubContentField',)
               )


