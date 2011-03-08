(function($){
    $.fn.subcontentwidget = function(options) {
        
        var defaults = {
            // actually no options available
        };
        
        var options = $.extend(defaults, options);

        var Widget = function(field){
            if( arguments.length ) { this.init(field); };
        };
        
        Widget.prototype.init = function (field){
            var regex = /(archetypes-fieldname-)(.*)/;
            this.fieldname = field.parent('div').attr('id');
            this.fieldname = this.fieldname.match(regex)[2];
            
            skeleton = field.find('tr input.skeleton').parents('tr');
            this.table = skeleton.parents('tbody');
            this.skeleton = skeleton.wrapInner('<tr/>').html();
            skeleton.remove();
            this.initRow();
        }
        
        Widget.prototype.initRow = function(){
            this.index = 0;
            this.table.children('tr').each($.proxy(function(i, elem){
                this.index++;
                index = this.index;
                $(elem).data('index',this.index);
                var button = $(elem).find('.subcontentwidget_remove');
                button.unbind('click');
                button.click( $.proxy(function(){
                    this.del($(elem).data('index'));
                    return false;
                },this));
            },this));
        }
        
        Widget.prototype.getSkeleton = function(){
            this.index++;
            var regex = new RegExp("(_"+this.fieldname+"___)([0-9]*)(__)",'gm');
            input = this.skeleton;
            return this.skeleton.replace(regex, "$1"+this.index+"$3");
        }
        
        Widget.prototype.add = function(){
            this.table.append(this.getSkeleton());
            this.initRow();
        }
        
        Widget.prototype.del = function(index){
            this.table.children('tr').each(function(i, elem){
                if ($(elem).data('index') == index)
                    $(elem).remove();
            });
        }
        
        Widget.prototype.get = function(index){
            
        }
        
        var widgets = new Array();
        this.each(function(index){
            widgets[index] = new Widget($(this));
        });
        return widgets;
    };
    
})(jQuery);