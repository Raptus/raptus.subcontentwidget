import re
from zope import component
from zope.component import queryUtility
from OFS.ObjectManager import checkValidId
from zExceptions import BadRequest, Unauthorized
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.Archetypes.Widget import TypesWidget
from Products.Archetypes import atapi
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base


class Handler(object):
    
    temp_data = None
    
    def __call__(self, container, event):
        
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
        })
    
    security = ClassSecurityInfo()
    
    def __init__(self, *arg, **kw):
        super(SubContentWidget, self).__init__(*arg, **kw)
        assert self.sub_content_class, 'missing sub_content_class on widget'
        assert self.sub_fields, 'missing sub_fields on widget'
    
    def bootstrap(self, inst):
        for field in inst.Schema().values():
            if field.widget == self:
                self.namespace = '%s_%s_' % (field.getName(), self.sub_content_class.__name__, )
                return
    
    def getFields(self):
        # need to make a instance to get schema over ISchema
        inst = self.sub_content_class('temp')
        li = list()
        for field in inst.Schema().values():
            if not field.getName() in self.sub_fields:
                continue
            #fix remove DateTime on calendar field
            if hasattr(field, 'default_method'):
                field.default_method = None
            field = field.copy()
            li.append(field)
        return li
        
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        
        portal_types = getToolByName(instance,'portal_types')
        self.edited_handler.reset(instance)
        
        # parse string e.g: subEvent_myWidget_start__0___ampm
        # title = start    index = 0    additional = _ampm
        p = re.compile('^%s(.*)__([0-9]*)__(.*)'% self.namespace)
        
        rows = dict()
        for key, value in form.iteritems():
            m = p.match(key)
            if m:
                title, index, additional = m.groups()
                di = rows.get(index, dict())
                di.update({title+additional:value})
                rows.update({index:di})
                
        for index, row in rows.iteritems():
            copy = form.copy()
            copy.update(row)
            id = 'temp_sub_content_%s' % index
            portal_types.constructContent(type_name=self.sub_content_class.portal_type,
                                          container=self.edited_handler.data(), id=id)
            subinstance = self.edited_handler.data()[id]
            for key, value in row.iteritems():
                fi = subinstance.Schema().get(key, None)
                if fi:
                    result, marker = fi.widget.process_form(instance, fi, copy,empty_marker=None,
                                                            emptyReturnsMarker=False, validating=True)
                    method = fi.getMutator(subinstance)
                    method(result)

    @property
    def fields(self):
        row = list()
        index = 0
        for field in self.getFields():
            name = '%s%s__%s__' % (self.namespace, field.getName(), index,)
            field = field.__class__(name, **field._properties)
            field.widget.label = ' '
            field.widget.description = ' '
            row.append(field)
        row.append(dict(name='%srowset__%s__' % (self.namespace, index),
                        value=None
                        ))
        return [row]
    
    @property
    def titles(self):
        return [f.widget.label for f in self.getFields()]



