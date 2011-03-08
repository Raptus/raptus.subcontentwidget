jQuery(document).ready(function($) {
     
     $('table.subcontentwidget_default').each(function(){
         var button = $(this).find('.subcontentwidget_addrow');
         $(this).before('<a href="#">'+button.html()+'</a>');
         var link = $(this).prev();
         var widget = $(this).subcontentwidget()[0];
         link.click(function(){
             widget.add();
             return false;
         });
     });
     
});