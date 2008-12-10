# -*- coding: utf-8 -*-

import pkg_resources

import turbogears
from turbogears.controllers import expose
from turbogears import widgets
from turbogears.validators import Int, FancyValidator, Schema
from turbogears.widgets import CSSLink, JSLink, Widget, WidgetDescription, \
                               register_static_directory

__all__ = [
    'ShuttleValidator',
    'SelectShuttle',
]

pkg_name = "selectshuttle"
option_transfer = JSLink(pkg_name, "OptionTransfer.js")
js_dir = pkg_resources.resource_filename(pkg_name, "static/javascript")
register_static_directory(pkg_name, js_dir)

css_code = """
.selectshuttle {
    width: 100%;
}
table.selectshuttle th {
    text-align: left;
}
td.selectshuttle-left {
    text-align: left;
    width: 45%;
}
td.selectshuttle-middle {
    text-align: center;
    valign: middle;
}
td.selectshuttle-right {
    text-align: left;
    width: 45%;
}
td.selectshuttle-addlink {
    text-align: center;
}
"""

template = """
<div xmlns:py='http://purl.org/kid/ns#'>
    <script type="text/javascript">
    var ${optrans_name} = new OptionTransfer('${name}.${available.name}',
                                             '${name}.${selected.name}');
    ${optrans_name}.setAutoSort(true);
    ${optrans_name}.saveNewLeftOptions('${name}.available_new');
    ${optrans_name}.saveAddedLeftOptions('${name}.available_added');
    ${optrans_name}.saveRemovedLeftOptions('${name}.available_removed');
    ${optrans_name}.saveNewRightOptions('${name}.selected_new');
    ${optrans_name}.saveAddedRightOptions('${name}.selected_added');
    ${optrans_name}.saveRemovedRightOptions('${name}.selected_removed');
    </script>
    ${display_field_for(available_new)}
    ${display_field_for(available_added)}
    ${display_field_for(available_removed)}
    ${display_field_for(selected_new)}
    ${display_field_for(selected_added)}
    ${display_field_for(selected_removed)}
    <table align='left' width='100%' class='selectshuttle'>
      <thead>
        <tr>
          <th class='selectshuttle-left' py:content='title_available'>Left Options</th>
          <th class='selectshuttle-middle'></th>
          <th class='selectshuttle-right' py:content='title_selected'>Right Options</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class='selectshuttle-left'>${display_field_for(available)}</td>
          <td class='selectshuttle-middle'>
            <input type="button"
                   name="btn_selected"
                   id="${optrans_name}_btn_selected"
                   py:attrs="value=btn_to_selected"
                   onclick="${optrans_name}.transferRight()"
            /><br /><br />
            <input type="button"
                   name="btn_all_selected"
                   id="${optrans_name}_btn_all_selected"
                   py:attrs="value=btn_all_selected"
                   onclick="${optrans_name}.transferAllRight()"
            /><br /><br />
            <input type="button"
                   name="btn_all_available"
                   id="${optrans_name}_btn_all_available"
                   py:attrs="value=btn_all_available"
                  onclick="${optrans_name}.transferAllLeft()"
            /><br /><br />
            <input type="button"
                   name="btn_available"
                   id="${optrans_name}_btn_available"
                   py:attrs="value=btn_to_available"
                   onclick="${optrans_name}.transferLeft()"
            />
          </td>
          <td class='selectshuttle-right'>${display_field_for(selected)}</td>
        </tr>
        <tr py:if='add_link is not None'>
          <td class='selectshuttle-addlink' colspan='3'>
            <a target="${target}" href="${add_link}">
                <span py:strip="1" py:if="add_image_src is not None">
                    <img src="${add_image_src}" border="0" />
                </span>
                ${add_text}
            </a>
          </td>
        </tr>
      </tbody>
    </table>
    <script type="text/javascript">
      addLoadEvent(${optrans_name}.init(${form_reference}))
    </script>
</div>
"""


class ShuttleValidator(Schema):
    def from_python(self, value, state=None):
        # Prevent the Schema from converting it's child widgets' values or else
        # it'll fail and TG will convert the whole form's dict into a string
        # (dont ask me why, I really don't care ATM ;) )
        return value

class ShuttleParser(FancyValidator):
    def to_python(self, value, state=None):
        if value is None:
            return []
        return map(Int.to_python, filter(bool, value.split(',')))

class SelectShuttle(widgets.CompoundFormField):
    """
    The SelectShuttle widget provides a mechanism for selecting
    multiple values from a list of values by allowing the user
    to move items between two lists.

    On modern browsers you can also double click an item to move it
    from one list to the other.

    After the first "move", all entries will be sorted automatically
    accordingly to its "description" on both lists.

    An optional "add" link, text, image and link target may be
    specified as well to enhance the usability of this widget when
    new options can be added.

    Take a look at the code for SelectShuttleDesc for an example of
    how to use this widget in your code.
    """

    javascript = [widgets.mochikit, option_transfer]
    css = [widgets.CSSSource(src=css_code, media="screen")]
    template = template

    member_widgets = ['available', 'available_new', 'available_added',
                      'available_removed', 'selected', 'selected_new',
                      'selected_added', 'selected_removed']

    # The select boxes
    available = widgets.MultipleSelectField("available", size=10,
                                            validator=Int())
    selected = widgets.MultipleSelectField("selected", size=10,
                                           validator=Int())

    # Hidden fields for the JS to put information on what moved to where.
    available_new = widgets.HiddenField('available_new',
                                        validator=ShuttleParser())
    available_added = widgets.HiddenField('available_added',
                                          validator=ShuttleParser())
    available_removed = widgets.HiddenField('available_removed',
                                            validator=ShuttleParser())
    selected_new = widgets.HiddenField('selected_new',
                                       validator=ShuttleParser())
    selected_added = widgets.HiddenField('selected_added',
                                         validator=ShuttleParser())
    selected_removed = widgets.HiddenField('selected_removed',
                                           validator=ShuttleParser())

    params = ["title_available", "title_selected", "form_reference",
              "btn_all_selected", "btn_all_available",
              "btn_to_selected", "btn_to_available",
              "available_options",
              "add_link", "add_text", "target", "add_image_src"]

    params_doc = {
        'title_available':'Header for available options',
        'title_selected':'Header for selected options',
        'form_reference':'Form number on the page, if in a multi-form page',
        'btn_all_selected':'Text to the button that moves all available to selected',
        'btn_all_available':'Text to the button that moves all selected to available',
        'btn_to_selected':'Text to the button that moves one available option to selected',
        'btn_to_available':'Text to the button that moves one selected option to available',
        'available_options':'Options to be shown as available',
        'add_link':'Hyperlink to some action (e.g. add new options) - optional',
        'add_text':'Text to show the user for the add_link - optional',
        'target':'Target to open the add_link - optional',
        'add_image_src':'Image to show before the add_link text - optional',
        }

    # Make sure to inherit from ShuttleValidator if you need to override the
    # shuttle's validator!
    validator = ShuttleValidator()

    title_available = "Left"
    title_selected = "Right"
    form_reference = 'document.forms[0]'
    btn_to_selected = '>>'
    btn_all_selected = 'All >>'
    btn_all_available = '<< All'
    btn_to_available = '<<'
    available_options = []
    convert = False
    add_link = None
    add_text = 'Add a new option'
    target = ""
    add_image_src = '/tg_static/images/add.png'


    def update_params(self, params):
        super(SelectShuttle, self).update_params(params)
        params['optrans_name'] = optrans_name = 'optrans_' + params['name'].replace('.','_')
        value = params.get('value', None) or {}
        available_opts = params['available_options']
        selected_opts = value.get('selected', [])
        redisplayed_opts = value.get('selected_new', None)
        if redisplayed_opts is not None:
            redisplayed_opts = ShuttleParser.to_python(redisplayed_opts)
            # Form is being redisplayed, find names in available_options
            def get_name(find_id):
                for id, name in available_opts:
                    if find_id == id:
                        return name
            selected_opts = [(id, get_name(id)) for id in redisplayed_opts]
        not_selected = lambda x: x not in selected_opts
        available_opts = filter(not_selected, available_opts)

        # Lets set options for our member_widgets
        widgets_params = params['member_widgets_params']
        widgets_params.update(
            options = dict(
                available = available_opts,
                selected = selected_opts,
                ),
            attrs = dict(
                available = dict(
                    ondblclick = optrans_name + ".transferRight()"),
                selected = dict(
                    ondblclick = optrans_name + ".transferLeft()"),
                )
            )
        params['member_widgets_params'] = widgets_params
        # Hack around the fact 'params_for' is already curried with the old
        # 'widgets_params'
        params['params_for'] = lambda f: self.params_for(f, **widgets_params)


class SelectShuttleDesc(WidgetDescription):
    name = "Select Shuttle"

    full_class_name = "selectshuttle.SelectShuttle"

    form_name = "remote_form_for_shuttle"

    template = """
    <div>
        <form action="%s/post_data" name="%s" method="POST">
            ${for_widget.display()}<br />
            <input type="submit" value="Submit" />
        </form>
    </div>
    """ % (full_class_name, form_name)

    for_widget = SelectShuttle(
        name="select_shuttle_demo",
        label = "The shuttle",
        title_available = "Available options",
        title_selected = "Selected options",
        form_reference = "document.forms['%s']" % form_name,
        # All data should be provided as a list of tuples, in the form of
        # ("id", "value"). ATM, id should be an int
        available_options = [(i, "Option %d"%i) for i in xrange(5)],
        default = dict(selected=[(i, "Option %d"%i) for i in xrange(3)])
    )

    # Dummy form just so we can validate input
    validating_form = widgets.Form(fields=[for_widget])

    [expose()]
    def post_data(self, **kw):
        kw = self.validating_form.validate(kw)
        return "<b>Coerced data:</b><br />%s<br /><br /> " % kw