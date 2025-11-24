from rich import print
from Nodes.PlaceNode import PlaceNode

if __name__ == "__main__":
    my_node = PlaceNode()
    print(my_node.form_schema())
    data = {"country": "India"}
    new_affected_field_values = my_node.get_populated_field_value(data)
    print(new_affected_field_values)
    my_node.populate_values(data)
    print(my_node.form_schema())

