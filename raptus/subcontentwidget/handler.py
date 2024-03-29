from zope import component
from Products.ATContentTypes.interfaces import IATContentType
from Products.Archetypes import event
from raptus.subcontentwidget.widget import SubContentWidget



def callWidgetHandler(obj, event, method):
    for widget in obj.Schema().widgets().values():
        if isinstance(widget, SubContentWidget):
            getattr(widget, method)(obj, event)


@component.adapter(IATContentType, event.ObjectInitializedEvent)
def initializedHandler(obj, event):
    callWidgetHandler(obj, event, 'initialized_handler')


@component.adapter(IATContentType, event.IObjectEditedEvent)
def editedHandler(obj, event):
    callWidgetHandler(obj, event, 'edited_handler')
