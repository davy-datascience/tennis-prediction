

def element_has_class(web_element, class_name):
    return class_name in web_element.get_attribute("class").split()
